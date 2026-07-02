import logging
import os
import time
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Scope

from config import settings
from database.connection import get_db_cursor
from exceptions import AuthError, ElectionError, NotFoundError, ValidationError, VoteError
from middleware import (
    AppErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from services import auth_service
from services.audit_service import get_action_types, get_audit_logs, get_target_types, log_action
from services.auth_service import configure_jwt
from services.auth_service import create_access_token as auth_create_token
from services.auth_service import decode_access_token as auth_decode_token
from services.candidate_service import (
    apply_as_candidate,
    bulk_update_candidate_status,
    get_applications_by_status_paginated,
    get_approved_candidates_for_election,
    get_election_candidates_paginated,
    get_student_candidacy_status,
    get_user_applications,
    has_user_applied,
    update_candidate_status,
)
from services.election_service import (
    bulk_delete_elections,
    bulk_publish_results,
    clone_election,
    create_election,
    delete_election,
    ensure_datetime,
    get_active_elections_count,
    get_dashboard_stats,
    get_election_by_id,
    get_election_results,
    get_elections_by_status_paginated,
    get_elections_paginated,
    get_elections_results_batch,
    get_ended_elections_paginated,
    get_published_ended_elections_paginated,
    get_recent_activity,
    get_upcoming_elections,
    get_vote_trend,
    publish_results,
    update_election,
)
from services.file_service import (
    validate_and_save_profile_picture,
    validate_and_save_verification_file,
)
from services.user_service import (
    get_distinct_departments,
    get_user_by_id,
    get_user_candidate_applications,
    update_user_profile,
)
from services.vote_service import (
    create_voting_session,
    get_active_session,
    get_user_vote_count,
    has_user_voted,
    submit_vote_with_verification,
)

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voting System API",
    description="Web-based election management platform",
    version="1.0.0",
)


class CachedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=3600, immutable"
        return response


app.mount("/static", CachedStaticFiles(directory="static"), name="static")

os.makedirs(f"{settings.upload_dir}/profiles", exist_ok=True)
os.makedirs(f"{settings.upload_dir}/selfies", exist_ok=True)
os.makedirs(f"{settings.upload_dir}/signatures", exist_ok=True)

app.mount(f"/{settings.upload_dir}", StaticFiles(directory=settings.upload_dir), name="uploads")

templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(AppErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(COOKIE_NAME)
        user = auth_decode_token(token) if token else None
        request.state.user = user
        if user and settings.sentry_dsn:
            try:
                import sentry_sdk

                sentry_sdk.set_user(
                    {
                        "id": user.get("user_id"),
                        "email": user.get("email"),
                        "role": user.get("role"),
                    }
                )
            except ImportError:
                pass
        return await call_next(request)


app.add_middleware(AuthMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

if settings.environment == "production":
    origins = [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
configure_jwt(settings.jwt_secret)

# Sentry
if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=1.0,
    )

app.state.startup_time = time.time()

# Re-export for test compatibility
create_access_token = auth_create_token
COOKIE_NAME = auth_service.COOKIE_NAME
CSRF_COOKIE_NAME = auth_service.CSRF_COOKIE_NAME
JWT_ALGORITHM = auth_service.JWT_ALGORITHM
JWT_SECRET = settings.jwt_secret

SUCCESS_MESSAGE_MAP = {
    "created": "Election created successfully!",
    "updated": "Election updated successfully!",
    "deleted": "Election removed successfully!",
}

ERROR_MESSAGE_MAP = {
    "internal": "An internal error occurred. Please try again.",
}


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    import shutil

    db_ok = False
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False

    uptime_seconds = time.time() - app.state.startup_time
    total, used, free = shutil.disk_usage(settings.upload_dir)

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0",
        "uptime_seconds": round(uptime_seconds, 2),
        "database": "connected" if db_ok else "disconnected",
        "disk_space_mb": {
            "free": round(free / (1024 * 1024), 2),
            "total": round(total / (1024 * 1024), 2),
        },
    }


class RedirectError(Exception):
    def __init__(self, url: str, status_code: int = 302):
        self.url = url
        self.status_code = status_code


@app.exception_handler(RedirectError)
async def redirect_exception_handler(request: Request, exc: RedirectError):
    return RedirectResponse(url=exc.url, status_code=exc.status_code)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
async def get_current_user(request: Request):
    return request.state.user


async def admin_guard(request: Request, user=Depends(get_current_user)):
    if not user or user.get("role", "").upper() != "ADMIN":
        raise RedirectError(url="/admin/login")
    return user


async def student_guard(request: Request, user=Depends(get_current_user)):
    if not user or user.get("role", "").upper() != "STUDENT":
        raise RedirectError(url="/login")
    return user


async def get_csrf_token(request: Request):
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        token = auth_service.generate_csrf_token()
    return token


async def verify_csrf(request: Request, csrf_token: str = Form(None)):
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_token or not csrf_token or cookie_token != csrf_token:
        logger.warning(f"CSRF verification failed for user {request.state.user}")
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    return csrf_token


def set_csrf_cookie(response, csrf_token: str):
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.environment == "production",
    )


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------
@app.get("/debug-role", tags=["Auth"])
async def debug_role(request: Request):
    return {"role": request.state.user.get("role") if request.state.user else "None"}


@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home(request: Request):
    user = request.state.user
    if user:
        return RedirectResponse(
            url="/admin/dashboard" if user["role"].upper() == "ADMIN" else "/student/dashboard",
            status_code=302,
        )
    return templates.TemplateResponse(request, "register.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, tags=["Auth"])
async def register_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(
            url="/admin/dashboard" if user["role"].upper() == "ADMIN" else "/student/dashboard",
            status_code=302,
        )
    return templates.TemplateResponse(request, "register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["Auth"])
async def login_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(
            url="/admin/dashboard" if user["role"].upper() == "ADMIN" else "/student/dashboard",
            status_code=302,
        )
    return templates.TemplateResponse(request, "login.html", {"request": request})


@app.get("/admin/login", response_class=HTMLResponse, tags=["Auth"])
async def admin_login_page(request: Request):
    return templates.TemplateResponse(request, "admin-login.html", {"request": request})


@app.post("/auth/register", tags=["Auth"])
async def register_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    department: str = Form(...),
    academic_year: str = Form(...),
):
    try:
        result = auth_service.register_user(full_name, email, password, department, academic_year)
        return templates.TemplateResponse(
            request,
            "register.html",
            {"request": request, "success": result["message"]},
        )
    except ValidationError as e:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"request": request, "error": str(e)},
        )
    except Exception:
        logger.exception("Registration failed")
        return templates.TemplateResponse(
            request,
            "register.html",
            {"request": request, "error": "An internal error occurred. Please try again."},
        )


@app.post("/auth/login", tags=["Auth"])
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: str | None = Form(None),
):
    try:
        result = auth_service.authenticate_user(email, password, remember_me=remember_me == "true")
        response = RedirectResponse(
            url="/student/dashboard?login=success",
            status_code=303,
        )
        response.set_cookie(
            key=auth_service.COOKIE_NAME,
            value=result["token"],
            httponly=True,
            samesite="lax",
            secure=settings.environment == "production",
        )
        breach_warning = result.get("breach_warning")
        if breach_warning:
            response.set_cookie(
                key="breach_warning", value=breach_warning, httponly=False, samesite="lax"
            )
        return response
    except AuthError as e:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": str(e)},
        )
    except Exception:
        logger.exception("Login failed")
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "An internal error occurred. Please try again."},
        )


@app.post("/auth/admin-login", tags=["Auth"])
async def admin_login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: str | None = Form(None),
):
    try:
        result = auth_service.authenticate_user(
            email, password, require_admin=True, remember_me=remember_me == "true"
        )
        response = RedirectResponse(url="/admin/dashboard?login=success", status_code=303)
        response.set_cookie(
            key=auth_service.COOKIE_NAME,
            value=result["token"],
            httponly=True,
            samesite="lax",
            secure=settings.environment == "production",
        )
        return response
    except AuthError as e:
        return templates.TemplateResponse(
            request,
            "admin-login.html",
            {"request": request, "error": str(e)},
        )
    except Exception:
        logger.exception("Admin login failed")
        return templates.TemplateResponse(
            request,
            "admin-login.html",
            {"request": request, "error": "An internal error occurred. Please try again."},
        )


@app.get("/auth/logout", tags=["Auth"])
async def logout_user():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(auth_service.COOKIE_NAME)
    return response


# ---------------------------------------------------------------------------
# Student Routes
# ---------------------------------------------------------------------------
@app.get("/student/dashboard", response_class=HTMLResponse, tags=["Student"])
async def student_dashboard(request: Request, user=Depends(get_current_user)):
    if not user or user.get("role", "").upper() != "STUDENT":
        return RedirectResponse(url="/login", status_code=302)
    try:
        active_count = get_active_elections_count()
    except Exception:
        active_count = 0
    try:
        candidacy_status = get_student_candidacy_status(user["user_id"])
    except Exception:
        candidacy_status = None
    try:
        votes_cast = get_user_vote_count(user["user_id"])
    except Exception:
        votes_cast = 0
    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={
            "user": user,
            "active_count": active_count,
            "candidacy_status": candidacy_status,
            "votes_cast": votes_cast,
        },
    )


@app.get("/student/elections", response_class=HTMLResponse, tags=["Student"])
async def student_elections_list(
    request: Request,
    tab: str = "active",
    page: int = 1,
    user=Depends(student_guard),
):
    per_page = 10
    status_map = {"active": "ACTIVE", "upcoming": "UPCOMING", "ended": "ENDED"}
    db_status = status_map.get(tab, "ACTIVE")
    try:
        elections, total = get_elections_by_status_paginated(db_status, page, per_page)
    except Exception:
        logger.exception("Failed to fetch elections")
        elections = []
        total = 0
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    return templates.TemplateResponse(
        request,
        "student_elections.html",
        {
            "request": request,
            "elections": elections,
            "tab": tab,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "user": user,
        },
    )


@app.get("/student/elections/apply", response_class=HTMLResponse, tags=["Student"])
async def student_election_apply_list(request: Request, user=Depends(student_guard)):
    upcoming = get_upcoming_elections()
    return templates.TemplateResponse(
        request,
        "student_election_apply_list.html",
        {"request": request, "upcoming": upcoming, "user": user},
    )


@app.get("/student/elections/{id}", response_class=HTMLResponse, tags=["Student"])
async def student_election_detail(request: Request, id: int, user=Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/student/elections", status_code=302)
    has_applied = has_user_applied(user["user_id"], id)
    has_voted = has_user_voted(user["user_id"], id)
    success_message = None
    error_message = None
    info_message = None
    success_key = request.query_params.get("success")
    error_key = request.query_params.get("error")
    info_key = request.query_params.get("info")
    if success_key == "voted":
        success_message = "Your vote has been recorded."
    elif success_key == "already_voted":
        success_message = "You have already voted in this election."
    if error_key == "already_voted":
        error_message = "You have already voted in this election."
    elif error_key == "invalid_candidate":
        error_message = "Please select an approved candidate from this election."
    elif error_key == "inactive":
        error_message = "Voting is only available while the election is active."
    if info_key == "not_published":
        info_message = "The results for this election have not been published yet."
    return templates.TemplateResponse(
        request,
        "student_election_detail.html",
        {
            "request": request,
            "election": election,
            "user": user,
            "has_applied": has_applied,
            "has_voted": has_voted,
            "success_message": success_message,
            "error_message": error_message,
            "info_message": info_message,
        },
    )


@app.get("/student/elections/{id}/apply", response_class=HTMLResponse, tags=["Student"])
async def student_election_apply_page(request: Request, id: int, user=Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/student/elections", status_code=302)
    if election.get("status") != "UPCOMING":
        return RedirectResponse(url="/student/elections", status_code=302)
    if has_user_applied(user["user_id"], id):
        return RedirectResponse(url="/student/candidate-status", status_code=302)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "student_election_apply.html",
        {"request": request, "election": election, "user": user, "csrf_token": csrf_token},
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.get("/student/elections/{id}/vote", response_class=HTMLResponse, tags=["Student"])
async def student_election_vote_page(request: Request, id: int, user=Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/student/elections", status_code=302)
    if election["status"] != "ACTIVE":
        return RedirectResponse(url=f"/student/elections/{id}?error=inactive", status_code=302)
    if has_user_voted(user["user_id"], id):
        return RedirectResponse(
            url=f"/student/elections/{id}?success=already_voted", status_code=302
        )
    approved_candidates = get_approved_candidates_for_election(id)
    error_key = request.query_params.get("error")
    error_message = None
    if error_key == "invalid_candidate":
        error_message = "Please select an approved candidate from this election."
    elif error_key == "internal":
        error_message = "An internal error occurred. Please try again."
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "student_election_vote.html",
        {
            "request": request,
            "election": election,
            "user": user,
            "approved_candidates": approved_candidates,
            "csrf_token": csrf_token,
            "error_message": error_message,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/student/elections/{id}/vote", tags=["Student"])
async def submit_student_vote(
    request: Request,
    id: int,
    candidate_application_id: int = Form(...),
    user=Depends(student_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        create_voting_session(user["user_id"], id, candidate_application_id)
    except (ElectionError, VoteError) as e:
        return RedirectResponse(
            url=f"/student/elections/{id}/vote?error={e.message.lower().replace(' ', '_')}",
            status_code=303,
        )
    except Exception:
        logger.exception("Failed to create voting session")
        return RedirectResponse(url=f"/student/elections/{id}/vote?error=internal", status_code=303)
    return RedirectResponse(url=f"/student/elections/{id}/verify", status_code=303)


@app.post("/candidates/apply", tags=["Student"])
async def apply_as_candidate_route(
    request: Request,
    election_id: int = Form(...),
    manifesto: str = Form(...),
    user=Depends(student_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        apply_as_candidate(user["user_id"], election_id, manifesto)
    except ValidationError:
        pass
    return RedirectResponse(url="/student/candidate-status", status_code=303)


@app.get("/student/candidate-status", response_class=HTMLResponse, tags=["Student"])
async def student_candidate_status(request: Request, user=Depends(student_guard)):
    applications = get_user_applications(user["user_id"])
    return templates.TemplateResponse(
        request,
        "student_candidate_status.html",
        {"request": request, "applications": applications, "user": user},
    )


@app.get("/student/elections/{id}/results", response_class=HTMLResponse, tags=["Student"])
async def student_election_results(request: Request, id: int, user=Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
    if election["status"] != "ENDED" or not election["result_published"]:
        return RedirectResponse(url=f"/student/elections/{id}?info=not_published", status_code=302)
    results, total_votes = get_election_results(id)
    return templates.TemplateResponse(
        request,
        "student_election_results.html",
        {
            "request": request,
            "user": user,
            "election": election,
            "results": results,
            "total_votes": total_votes,
        },
    )


@app.get("/student/elections/{id}/results/export", tags=["Student"])
async def student_export_election_results(
    request: Request,
    id: int,
    format: str = "csv",
    user=Depends(student_guard),
):
    from services.export_service import export_results_csv, export_results_pdf

    election = get_election_by_id(id)
    if not election or election["status"] != "ENDED" or not election["result_published"]:
        return RedirectResponse(url=f"/student/elections/{id}?info=not_published", status_code=302)

    try:
        if format == "csv":
            csv_data = export_results_csv(id)
            if csv_data is None:
                return RedirectResponse(url=f"/student/elections/{id}/results", status_code=303)
            from fastapi.responses import StreamingResponse

            return StreamingResponse(
                iter([csv_data]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=election_{id}_results.csv"},
            )
        elif format == "pdf":
            pdf_data = export_results_pdf(id)
            if pdf_data is None:
                return RedirectResponse(url=f"/student/elections/{id}/results", status_code=303)
            from fastapi.responses import Response

            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=election_{id}_results.pdf"},
            )
    except Exception:
        logger.exception("Student export failed")
        return RedirectResponse(
            url=f"/student/elections/{id}/results?error=internal", status_code=303
        )


@app.get("/student/results", response_class=HTMLResponse, tags=["Student"])
async def student_results_overview(
    request: Request,
    page: int = 1,
    user=Depends(student_guard),
):
    per_page = 10
    try:
        elections, total = get_published_ended_elections_paginated(page, per_page)
    except Exception:
        logger.exception("Failed to fetch published elections")
        elections = []
        total = 0
    ids = [e["id"] for e in elections]
    if ids:
        try:
            batch = get_elections_results_batch(ids)
        except Exception:
            logger.exception("Failed to fetch batch results")
            batch = {}
    else:
        batch = {}
    election_results = []
    for election in elections:
        results, total_votes = batch.get(election["id"], ([], 0))
        election_results.append(
            {"election": election, "results": results, "total_votes": total_votes}
        )
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    return templates.TemplateResponse(
        request,
        "student_results.html",
        {
            "request": request,
            "user": user,
            "election_results": election_results,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


# ---------------------------------------------------------------------------
# Student Verification Routes
# ---------------------------------------------------------------------------
@app.get("/student/elections/{id}/verify", response_class=HTMLResponse, tags=["Student"])
async def student_election_verify_page(request: Request, id: int, user=Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/student/elections", status_code=302)
    if election["status"] != "ACTIVE":
        return RedirectResponse(url=f"/student/elections/{id}?error=inactive", status_code=302)
    if has_user_voted(user["user_id"], id):
        return RedirectResponse(
            url=f"/student/elections/{id}?success=already_voted", status_code=302
        )
    session = get_active_session(user["user_id"], id)
    if not session or not session.get("candidate_application_id"):
        return RedirectResponse(url=f"/student/elections/{id}/vote?error=internal", status_code=302)
    expires_at = ensure_datetime(session["expires_at"])
    if expires_at and expires_at < datetime.now(UTC):
        return RedirectResponse(
            url=f"/student/elections/{id}/vote?error=session_expired", status_code=302
        )
    error_key = request.query_params.get("error")
    error_message = None
    if error_key == "invalid_file":
        error_message = "Invalid file format. Please upload a JPG, JPEG, or PNG image."
    elif error_key == "session_expired":
        error_message = "Your voting session has expired. Please select your candidate again."
    elif error_key == "internal":
        error_message = "An internal error occurred during verification. Please try again."
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "student_election_verify.html",
        {
            "request": request,
            "election": election,
            "user": user,
            "csrf_token": csrf_token,
            "error_message": error_message,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/student/elections/{id}/verify", tags=["Student"])
async def submit_student_verification(
    request: Request,
    id: int,
    verification_type: str = Form(...),
    verification_file: UploadFile = File(...),
    user=Depends(student_guard),
    csrf_token=Depends(verify_csrf),
):
    if verification_type not in ("SELFIE", "SIGNATURE"):
        return RedirectResponse(
            url=f"/student/elections/{id}/verify?error=internal", status_code=303
        )
    try:
        file_path = validate_and_save_verification_file(
            user["user_id"], id, verification_type, verification_file
        )
    except ValidationError:
        return RedirectResponse(
            url=f"/student/elections/{id}/verify?error=invalid_file", status_code=303
        )
    except Exception:
        logger.exception("File save failed")
        return RedirectResponse(
            url=f"/student/elections/{id}/verify?error=internal", status_code=303
        )
    try:
        submit_vote_with_verification(user["user_id"], id, verification_type, file_path)
    except Exception:
        logger.exception("Vote submission failed after file save")
        return RedirectResponse(
            url=f"/student/elections/{id}/verify?error=internal", status_code=303
        )
    return RedirectResponse(url=f"/student/elections/{id}?success=voted", status_code=303)


# ---------------------------------------------------------------------------
# Admin Routes
# ---------------------------------------------------------------------------
@app.get("/admin/dashboard", response_class=HTMLResponse, tags=["Admin"])
async def admin_dashboard(request: Request, user=Depends(admin_guard)):
    try:
        stats = get_dashboard_stats()
    except Exception:
        stats = {}
    try:
        vote_trend = get_vote_trend(days=7)
    except Exception:
        vote_trend = []
    try:
        recent_activity = get_recent_activity(limit=20)
    except Exception:
        recent_activity = []
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": user,
            "stats": stats,
            "vote_trend": vote_trend,
            "recent_activity": recent_activity,
        },
    )


@app.get("/admin/elections", response_class=HTMLResponse, tags=["Admin"])
async def list_elections(
    request: Request,
    page: int = 1,
    search: str | None = None,
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user=Depends(admin_guard),
):
    per_page = 10
    try:
        elections, total = get_elections_paginated(
            page=page,
            per_page=per_page,
            search=search,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception:
        logger.exception("Failed to fetch elections")
        elections = []
        total = 0
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    success_key = request.query_params.get("success")
    success_message = SUCCESS_MESSAGE_MAP.get(success_key) if success_key else None
    error_key = request.query_params.get("error")
    error_message = ERROR_MESSAGE_MAP.get(error_key) if error_key else None
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_elections.html",
        {
            "request": request,
            "elections": elections,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
            "status_filter": status_filter,
            "date_from": date_from,
            "date_to": date_to,
            "success_message": success_message,
            "error_message": error_message,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.get("/admin/elections/create", response_class=HTMLResponse, tags=["Admin"])
async def create_election_page(request: Request, user=Depends(admin_guard)):
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_create.html",
        {"request": request, "csrf_token": csrf_token},
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/admin/elections", tags=["Admin"])
async def create_election_route(
    request: Request,
    title: str | None = Form(None),
    description: str | None = Form(None),
    start_time: str | None = Form(None),
    end_time: str | None = Form(None),
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    if not title or not start_time or not end_time:
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {
                "request": request,
                "error": "Title, start time, and end time are required.",
                "csrf_token": csrf_token,
                "values": {
                    "title": title,
                    "description": description,
                    "start_time": start_time,
                    "end_time": end_time,
                },
            },
        )
        set_csrf_cookie(response, csrf_token)
        return response
    try:
        create_election(title, description, start_time, end_time, user["user_id"])
        log_action(
            user_id=user["user_id"],
            action_type="ELECTION_CREATED",
            target_type="ELECTION",
            details={"title": title, "start_time": start_time, "end_time": end_time},
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url="/admin/elections?success=created", status_code=303)
    except ValidationError as e:
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {
                "request": request,
                "error": str(e),
                "csrf_token": csrf_token,
                "values": {
                    "title": title,
                    "description": description,
                    "start_time": start_time,
                    "end_time": end_time,
                },
            },
        )
        set_csrf_cookie(response, csrf_token)
        return response
    except Exception:
        logger.exception("Failed to create election")
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {
                "request": request,
                "error": "An internal error occurred. Please try again.",
                "csrf_token": csrf_token,
                "values": {
                    "title": title,
                    "description": description,
                    "start_time": start_time,
                    "end_time": end_time,
                },
            },
        )
        set_csrf_cookie(response, csrf_token)
        return response


@app.get("/admin/elections/{id}", response_class=HTMLResponse, tags=["Admin"])
async def edit_election_page(request: Request, id: int, user=Depends(admin_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_edit.html",
        {"request": request, "election": election, "csrf_token": csrf_token},
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/admin/elections/{id}/update", tags=["Admin"])
async def update_election_route(
    request: Request,
    id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    start_time: str | None = Form(None),
    end_time: str | None = Form(None),
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    if not title or not start_time or not end_time:
        election = get_election_by_id(id)
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {
                "request": request,
                "error": "Title, start time, and end time are required.",
                "election": election,
                "csrf_token": csrf_token,
            },
        )
        set_csrf_cookie(response, csrf_token)
        return response
    try:
        update_election(id, title, description, start_time, end_time)
        log_action(
            user_id=user["user_id"],
            action_type="ELECTION_UPDATED",
            target_type="ELECTION",
            target_id=id,
            details={"title": title, "start_time": start_time, "end_time": end_time},
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url="/admin/elections?success=updated", status_code=303)
    except ValidationError as e:
        election = get_election_by_id(id)
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {"request": request, "error": str(e), "election": election, "csrf_token": csrf_token},
        )
        set_csrf_cookie(response, csrf_token)
        return response
    except Exception:
        logger.exception("Failed to update election")
        election = get_election_by_id(id)
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {
                "request": request,
                "error": "An internal error occurred. Please try again.",
                "election": election,
                "csrf_token": csrf_token,
            },
        )
        set_csrf_cookie(response, csrf_token)
        return response


@app.post("/admin/elections/{id}/delete", tags=["Admin"])
async def delete_election_route(
    request: Request,
    id: int,
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        try:
            election = get_election_by_id(id)
            election_title = election["title"] if election else None
        except Exception:
            election_title = None
        delete_election(id)
        log_action(
            user_id=user["user_id"],
            action_type="ELECTION_DELETED",
            target_type="ELECTION",
            target_id=id,
            details={"title": election_title},
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url="/admin/elections?success=deleted", status_code=303)
    except Exception:
        logger.exception("Failed to delete election")
        return RedirectResponse(url="/admin/elections?error=internal", status_code=303)


@app.get("/admin/elections/{id}/clone", response_class=HTMLResponse, tags=["Admin"])
async def clone_election_page(request: Request, id: int, user=Depends(admin_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_create.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "clone_source": election,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/admin/elections/{id}/clone", tags=["Admin"])
async def clone_election_route(
    request: Request,
    id: int,
    title: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        clone_election(id, title, start_time, end_time, user["user_id"])
        log_action(
            user_id=user["user_id"],
            action_type="ELECTION_CLONED",
            target_type="ELECTION",
            target_id=id,
            details={"new_title": title},
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url="/admin/elections?success=created", status_code=303)
    except Exception:
        logger.exception("Failed to clone election")
        return RedirectResponse(url="/admin/elections?error=internal", status_code=303)


@app.post("/admin/elections/bulk-action", tags=["Admin"])
async def bulk_election_action(
    request: Request,
    election_ids: list[int] = Form(...),
    bulk_action: str = Form(...),
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        if bulk_action == "delete":
            bulk_delete_elections(election_ids)
            log_action(
                user_id=user["user_id"],
                action_type="ELECTIONS_BULK_DELETED",
                target_type="ELECTION",
                details={"count": len(election_ids), "ids": election_ids},
                ip_address=request.client.host if request.client else None,
            )
        elif bulk_action == "publish":
            bulk_publish_results(election_ids)
            log_action(
                user_id=user["user_id"],
                action_type="RESULTS_BULK_PUBLISHED",
                target_type="ELECTION",
                details={"count": len(election_ids), "ids": election_ids},
                ip_address=request.client.host if request.client else None,
            )
        return RedirectResponse(url="/admin/elections?success=updated", status_code=303)
    except Exception:
        logger.exception("Bulk action failed")
        return RedirectResponse(url="/admin/elections?error=internal", status_code=303)


@app.get("/admin/candidates", response_class=HTMLResponse, tags=["Admin"])
async def admin_candidates_list(
    request: Request,
    status: str = "PENDING",
    sort: str = "date",
    order: str = "ASC",
    category: str | None = None,
    page: int = 1,
    user=Depends(admin_guard),
):
    per_page = 20
    try:
        departments = get_distinct_departments()
        applications, total = get_applications_by_status_paginated(
            status, page, per_page, sort, order, category
        )
    except Exception:
        logger.exception(f"Failed to fetch {status} candidates")
        return RedirectResponse(
            url=f"/admin/candidates?status={status}&error=internal", status_code=303
        )
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_candidates_list.html",
        {
            "request": request,
            "applications": applications,
            "user": user,
            "csrf_token": csrf_token,
            "current_status": status.upper(),
            "departments": departments,
            "current_category": category,
            "current_sort": sort,
            "current_order": order,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.get("/admin/candidates/pending", response_class=HTMLResponse, tags=["Admin"])
async def admin_candidates_pending_redirect():
    return RedirectResponse(url="/admin/candidates?status=PENDING", status_code=302)


@app.get("/admin/candidates/approved", response_class=HTMLResponse, tags=["Admin"])
async def admin_candidates_approved(
    request: Request,
    page: int = 1,
    user=Depends(admin_guard),
):
    per_page = 20
    try:
        applications, total = get_applications_by_status_paginated("APPROVED", page, per_page)
    except Exception:
        logger.exception("Failed to fetch approved candidates")
        return RedirectResponse(url="/admin/dashboard?error=internal", status_code=303)
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_candidates_approved.html",
        {
            "request": request,
            "applications": applications,
            "user": user,
            "csrf_token": csrf_token,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/admin/candidates/{id}/{action}", tags=["Admin"])
async def update_candidate_status_route(
    request: Request,
    id: int,
    action: str,
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        update_candidate_status(id, action, user["user_id"])
        log_action(
            user_id=user["user_id"],
            action_type="CANDIDATE_" + ("APPROVED" if action == "approve" else "REJECTED"),
            target_type="CANDIDATE_APPLICATION",
            target_id=id,
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url="/admin/candidates", status_code=303)
    except ValidationError:
        return RedirectResponse(
            url="/admin/candidates/pending?error=invalid_action", status_code=303
        )
    except Exception:
        logger.exception(f"Failed to {action} candidate")
        return RedirectResponse(url="/admin/candidates?error=internal", status_code=303)


@app.post("/admin/candidates/bulk-action", tags=["Admin"])
async def bulk_candidate_action(
    request: Request,
    candidate_ids: list[int] = Form(...),
    bulk_action: str = Form(...),
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        bulk_update_candidate_status(candidate_ids, bulk_action, user["user_id"])
        action_label = "APPROVED" if bulk_action == "approve" else "REJECTED"
        log_action(
            user_id=user["user_id"],
            action_type=f"CANDIDATES_BULK_{action_label}",
            target_type="CANDIDATE_APPLICATION",
            details={"count": len(candidate_ids), "ids": candidate_ids},
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url="/admin/candidates", status_code=303)
    except Exception:
        logger.exception("Bulk candidate action failed")
        return RedirectResponse(url="/admin/candidates?error=internal", status_code=303)


@app.get("/admin/elections/{id}/candidates", response_class=HTMLResponse, tags=["Admin"])
async def admin_election_candidates(
    request: Request,
    id: int,
    page: int = 1,
    user=Depends(admin_guard),
):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)
    per_page = 20
    try:
        applications, total = get_election_candidates_paginated(id, page, per_page)
    except Exception:
        logger.exception("Failed to fetch candidates for election")
        return RedirectResponse(
            url=f"/admin/elections/{id}/candidates?error=internal", status_code=303
        )
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_candidates.html",
        {
            "request": request,
            "applications": applications,
            "user": user,
            "election": election,
            "csrf_token": csrf_token,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.get("/admin/elections/{id}/results", response_class=HTMLResponse, tags=["Admin"])
async def admin_election_results(request: Request, id: int, user=Depends(admin_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)
    if election["status"] != "ENDED":
        return RedirectResponse(url=f"/admin/elections/{id}", status_code=302)
    results, total_votes = get_election_results(id)
    published = bool(election["result_published"])
    info_message = None
    if published:
        info_message = "Results have been published to students."
    elif request.query_params.get("success") == "published":
        info_message = "Results have been published to students."
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_results.html",
        {
            "request": request,
            "user": user,
            "election": election,
            "results": results,
            "total_votes": total_votes,
            "published": published,
            "info_message": info_message,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.get("/admin/elections/{id}/results/export", tags=["Admin"])
async def export_election_results(
    request: Request,
    id: int,
    format: str = "csv",
    user=Depends(admin_guard),
):
    from services.export_service import export_results_csv, export_results_pdf

    try:
        if format == "csv":
            csv_data = export_results_csv(id)
            if csv_data is None:
                return RedirectResponse(url="/admin/elections", status_code=303)
            from fastapi.responses import StreamingResponse

            return StreamingResponse(
                iter([csv_data]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=election_{id}_results.csv"},
            )
        elif format == "pdf":
            pdf_data = export_results_pdf(id)
            if pdf_data is None:
                return RedirectResponse(url="/admin/elections", status_code=303)
            from fastapi.responses import Response

            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=election_{id}_results.pdf"},
            )
    except Exception:
        logger.exception("Export failed")
        return RedirectResponse(
            url=f"/admin/elections/{id}/results?error=internal", status_code=303
        )


@app.post("/admin/elections/{id}/publish-results", tags=["Admin"])
async def publish_election_results_route(
    request: Request,
    id: int,
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        publish_results(id)
        log_action(
            user_id=user["user_id"],
            action_type="RESULTS_PUBLISHED",
            target_type="ELECTION",
            target_id=id,
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(
            url=f"/admin/elections/{id}/results?success=published", status_code=303
        )
    except (NotFoundError, ElectionError):
        return RedirectResponse(url="/admin/elections", status_code=303)
    except Exception:
        logger.exception("Failed to publish results")
        return RedirectResponse(
            url=f"/admin/elections/{id}/results?error=internal", status_code=303
        )


@app.get("/admin/results", response_class=HTMLResponse, tags=["Admin"])
async def admin_results_overview(
    request: Request,
    page: int = 1,
    user=Depends(admin_guard),
):
    per_page = 10
    try:
        elections, total = get_ended_elections_paginated(page, per_page)
    except Exception:
        logger.exception("Failed to fetch ended elections")
        elections = []
        total = 0
    ids = [e["id"] for e in elections]
    if ids:
        try:
            batch = get_elections_results_batch(ids)
        except Exception:
            logger.exception("Failed to fetch batch results")
            batch = {}
    else:
        batch = {}
    election_results = []
    for election in elections:
        results, total_votes = batch.get(election["id"], ([], 0))
        election_results.append(
            {"election": election, "results": results, "total_votes": total_votes}
        )
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    info_message = None
    if request.query_params.get("success") == "published":
        info_message = "Results have been published to students."
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_results.html",
        {
            "request": request,
            "user": user,
            "election_results": election_results,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "info_message": info_message,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


# ---------------------------------------------------------------------------
# Audit Log Route
# ---------------------------------------------------------------------------
@app.get("/admin/audit", response_class=HTMLResponse, tags=["Admin"])
async def admin_audit_logs(
    request: Request,
    page: int = 1,
    action_type: str | None = None,
    target_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user=Depends(admin_guard),
):
    per_page = 20
    try:
        logs, total = get_audit_logs(
            page=page,
            per_page=per_page,
            action_type=action_type,
            target_type=target_type,
            date_from=date_from,
            date_to=date_to,
        )
        action_types = get_action_types()
        target_types = get_target_types()
    except Exception:
        logger.exception("Failed to fetch audit logs")
        logs = []
        total = 0
        action_types = []
        target_types = []
    total_pages = max(1, (total + per_page - 1) // per_page)
    return templates.TemplateResponse(
        request,
        "admin_audit.html",
        {
            "request": request,
            "logs": logs,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "filters": {
                "action_type": action_type,
                "target_type": target_type,
                "date_from": date_from,
                "date_to": date_to,
            },
            "action_types": action_types,
            "target_types": target_types,
        },
    )


# ---------------------------------------------------------------------------
# Profile Routes
# ---------------------------------------------------------------------------
@app.get("/profile", response_class=HTMLResponse, tags=["Profile"])
async def profile_page(request: Request, user=Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        user_data = get_user_by_id(user["user_id"])
    except NotFoundError:
        return RedirectResponse(url="/login", status_code=302)
    applications = get_user_candidate_applications(user["user_id"])
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "profile.html",
        {
            "request": request,
            "user": user_data,
            "csrf_token": csrf_token,
            "applications": applications,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/profile/update", tags=["Profile"])
async def update_profile_route(
    request: Request,
    full_name: str = Form(...),
    department: str = Form(...),
    academic_year: str = Form(...),
    profile_pic: UploadFile | None = File(None),
    user=Depends(get_current_user),
    csrf_token=Depends(verify_csrf),
):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        profile_path = None
        if profile_pic and profile_pic.filename:
            profile_path = validate_and_save_profile_picture(user["user_id"], profile_pic)
        update_user_profile(user["user_id"], full_name, department, academic_year, profile_path)
        return RedirectResponse(url="/profile?success=updated", status_code=303)
    except Exception:
        logger.exception("Failed to update user profile")
        return RedirectResponse(url="/profile?error=internal", status_code=303)


@app.get("/admin/users/{id}/profile", response_class=HTMLResponse, tags=["Admin"])
async def admin_user_profile_page(request: Request, id: int, user=Depends(admin_guard)):
    try:
        target_user = get_user_by_id(id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_user_profile.html",
        {"request": request, "target_user": target_user, "csrf_token": csrf_token},
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.post("/admin/users/{id}/update", tags=["Admin"])
async def admin_update_user_profile_route(
    request: Request,
    id: int,
    full_name: str = Form(...),
    department: str = Form(...),
    academic_year: str = Form(...),
    profile_pic: UploadFile | None = File(None),
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        profile_path = None
        if profile_pic and profile_pic.filename:
            profile_path = validate_and_save_profile_picture(id, profile_pic)
        update_user_profile(id, full_name, department, academic_year, profile_path)
        log_action(
            user_id=user["user_id"],
            action_type="USER_PROFILE_UPDATED",
            target_type="USER",
            target_id=id,
            details={"full_name": full_name, "department": department},
            ip_address=request.client.host if request.client else None,
        )
        return RedirectResponse(url=f"/admin/users/{id}/profile?success=updated", status_code=303)
    except Exception:
        logger.exception("Admin failed to update user profile")
        return RedirectResponse(url=f"/admin/users/{id}/profile?error=internal", status_code=303)
