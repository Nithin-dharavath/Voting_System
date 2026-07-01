import logging
import os
import time
from datetime import UTC, datetime

from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database.connection import get_db_cursor
from exceptions import AuthError, ElectionError, NotFoundError, ValidationError, VoteError
from middleware import AppErrorHandlerMiddleware, RequestLoggingMiddleware
from services import auth_service
from services.auth_service import configure_jwt
from services.auth_service import create_access_token as auth_create_token
from services.auth_service import decode_access_token as auth_decode_token
from services.candidate_service import (
    apply_as_candidate,
    get_applications_by_status,
    get_approved_candidates_for_election,
    get_election_candidates,
    get_pending_count,
    get_student_candidacy_status,
    get_user_applications,
    has_user_applied,
    update_candidate_status,
)
from services.election_service import (
    create_election,
    delete_election,
    ensure_datetime,
    get_active_elections_count,
    get_all_elections,
    get_election_by_id,
    get_election_results,
    get_elections_with_results,
    get_published_ended_elections,
    get_upcoming_elections,
    publish_results,
    update_election,
)
from services.file_service import (
    validate_and_save_profile_picture,
    validate_and_save_verification_file,
)
from services.user_service import (
    get_distinct_departments,
    get_student_count,
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

app.mount("/static", StaticFiles(directory="static"), name="static")

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
    response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=True)


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
    remember_me: Optional[str] = Form(None),
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
            secure=True,
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
    remember_me: Optional[str] = Form(None),
):
    try:
        result = auth_service.authenticate_user(email, password, require_admin=True, remember_me=remember_me == "true")
        response = RedirectResponse(url="/admin/dashboard?login=success", status_code=303)
        response.set_cookie(
            key=auth_service.COOKIE_NAME,
            value=result["token"],
            httponly=True,
            samesite="lax",
            secure=True,
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
async def student_elections_list(request: Request, user=Depends(student_guard)):
    elections = get_all_elections()
    active = [e for e in elections if e["status"] == "ACTIVE"]
    upcoming = [e for e in elections if e["status"] == "UPCOMING"]
    ended = [e for e in elections if e["status"] == "ENDED"]
    return templates.TemplateResponse(
        request,
        "student_elections.html",
        {"request": request, "active": active, "upcoming": upcoming, "ended": ended, "user": user},
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


@app.get("/student/results", response_class=HTMLResponse, tags=["Student"])
async def student_results_overview(request: Request, user=Depends(student_guard)):
    elections = get_published_ended_elections()
    election_results = []
    for election in elections:
        results, total_votes = get_election_results(election["id"])
        election_results.append(
            {"election": election, "results": results, "total_votes": total_votes}
        )
    return templates.TemplateResponse(
        request,
        "student_results.html",
        {"request": request, "user": user, "election_results": election_results},
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
        total_students = get_student_count()
    except Exception:
        total_students = 0
    try:
        active_elections = get_active_elections_count()
    except Exception:
        active_elections = 0
    try:
        pending_apps = get_pending_count()
    except Exception:
        pending_apps = 0
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                (SELECT u.full_name, 'candidacy' as action_type, ca.applied_at as acted_at
                 FROM candidate_applications ca
                 JOIN users u ON ca.user_id = u.user_id
                 ORDER BY ca.applied_at DESC LIMIT 5)
                UNION ALL
                (SELECT u.full_name, 'vote' as action_type, v.voted_at as acted_at
                 FROM votes v
                 JOIN users u ON v.voter_id = u.user_id
                 ORDER BY v.voted_at DESC LIMIT 5)
                UNION ALL
                (SELECT u.full_name, 'election_created' as action_type, e.created_at as acted_at
                 FROM elections e
                 JOIN users u ON e.created_by = u.user_id
                 ORDER BY e.created_at DESC LIMIT 5)
                ORDER BY acted_at DESC LIMIT 10
                """
            )
            recent_activity = cursor.fetchall()
    except Exception:
        recent_activity = []
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": user,
            "stats": {
                "total_students": total_students,
                "active_elections": active_elections,
                "pending_apps": pending_apps,
            },
            "recent_activity": recent_activity,
        },
    )


@app.get("/admin/elections", response_class=HTMLResponse, tags=["Admin"])
async def list_elections(request: Request, user=Depends(admin_guard)):
    elections = get_all_elections()
    success_key = request.query_params.get("success")
    success_message = SUCCESS_MESSAGE_MAP.get(success_key) if success_key else None
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_elections.html",
        {
            "request": request,
            "elections": elections,
            "success_message": success_message,
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
        delete_election(id)
        return RedirectResponse(url="/admin/elections?success=deleted", status_code=303)
    except Exception:
        logger.exception("Failed to delete election")
        return RedirectResponse(url="/admin/elections?error=internal", status_code=303)


@app.get("/admin/candidates", response_class=HTMLResponse, tags=["Admin"])
async def admin_candidates_list(
    request: Request,
    status: str = "PENDING",
    sort: str = "date",
    order: str = "ASC",
    category: str | None = None,
    user=Depends(admin_guard),
):
    try:
        departments = get_distinct_departments()
        applications = get_applications_by_status(status, sort, order, category)
    except Exception:
        logger.exception(f"Failed to fetch {status} candidates")
        return RedirectResponse(
            url=f"/admin/candidates?status={status}&error=internal", status_code=303
        )
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
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


@app.get("/admin/candidates/pending", response_class=HTMLResponse, tags=["Admin"])
async def admin_candidates_pending_redirect():
    return RedirectResponse(url="/admin/candidates?status=PENDING", status_code=302)


@app.get("/admin/candidates/approved", response_class=HTMLResponse, tags=["Admin"])
async def admin_candidates_approved(request: Request, user=Depends(admin_guard)):
    try:
        applications = get_applications_by_status("APPROVED")
    except Exception:
        logger.exception("Failed to fetch approved candidates")
        return RedirectResponse(url="/admin/dashboard?error=internal", status_code=303)
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_candidates_approved.html",
        {"request": request, "applications": applications, "user": user, "csrf_token": csrf_token},
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
        return RedirectResponse(url="/admin/candidates", status_code=303)
    except ValidationError:
        return RedirectResponse(
            url="/admin/candidates/pending?error=invalid_action", status_code=303
        )
    except Exception:
        logger.exception(f"Failed to {action} candidate")
        return RedirectResponse(url="/admin/candidates?error=internal", status_code=303)


@app.get("/admin/elections/{id}/candidates", response_class=HTMLResponse, tags=["Admin"])
async def admin_election_candidates(request: Request, id: int, user=Depends(admin_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)
    try:
        applications = get_election_candidates(id)
    except Exception:
        logger.exception("Failed to fetch candidates for election")
        return RedirectResponse(
            url=f"/admin/elections/{id}/candidates?error=internal", status_code=303
        )
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


@app.post("/admin/elections/{id}/publish-results", tags=["Admin"])
async def publish_election_results_route(
    request: Request,
    id: int,
    user=Depends(admin_guard),
    csrf_token=Depends(verify_csrf),
):
    try:
        publish_results(id)
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
async def admin_results_overview(request: Request, user=Depends(admin_guard)):
    try:
        election_results = get_elections_with_results()
    except Exception:
        election_results = []
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
            "info_message": info_message,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, csrf_token)
    return response


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
        return RedirectResponse(url=f"/admin/users/{id}/profile?success=updated", status_code=303)
    except Exception:
        logger.exception("Admin failed to update user profile")
        return RedirectResponse(url=f"/admin/users/{id}/profile?error=internal", status_code=303)
