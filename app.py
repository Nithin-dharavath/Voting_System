from fastapi import FastAPI, Request, Form, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import get_db_cursor
import jwt
import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def ensure_datetime(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    try:
        return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.fromisoformat(dt)
        except ValueError:
            return dt # Return as is if parsing fails, template might still fail but we tried

app = FastAPI()

# Mount the static directory to serve CSS, JS and images
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class RedirectException(Exception):
    def __init__(self, url: str, status_code: int = 302):
        self.url = url
        self.status_code = status_code

@app.exception_handler(RedirectException)
async def redirect_exception_handler(request: Request, exc: RedirectException):
    return RedirectResponse(url=exc.url, status_code=exc.status_code)

JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-this-in-env")
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "session_token"
CSRF_COOKIE_NAME = "csrf_token"

SUCCESS_MESSAGE_MAP = {
    "created": "Election created successfully!",
    "updated": "Election updated successfully!",
    "deleted": "Election removed successfully!",
}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(COOKIE_NAME)
        user = None
        if token:
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user = payload
            except jwt.PyJWTError:
                user = None

        request.state.user = user
        response = await call_next(request)
        return response

app.add_middleware(AuthMiddleware)

def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None

def generate_csrf_token():
    return secrets.token_urlsafe(32)

async def get_csrf_token(request: Request):
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        token = generate_csrf_token()
    return token

async def verify_csrf(request: Request, token: str = Form(None)):
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_token or not token or cookie_token != token:
        logger.warning(f"CSRF verification failed for user {request.state.user}")
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    return token

def get_election_by_id(election_id: int):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, title, description, start_time, end_time, result_published, status FROM elections WHERE id = %s", (election_id,))
        election = cursor.fetchone()
        if election:
            election['start_time'] = ensure_datetime(election['start_time'])
            election['end_time'] = ensure_datetime(election['end_time'])
        return election

async def get_current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return payload

async def admin_guard(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'ADMIN':
        raise RedirectException(url="/admin/login")
    return user

async def student_guard(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'STUDENT':
        raise RedirectException(url="/login")
    return user

@app.get("/debug-role")
async def debug_role(request: Request):
    return {"role": request.state.user.get('role') if request.state.user else "None"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.state.user
    if user:
        return RedirectResponse(url="/admin/dashboard" if user['role'].upper() == "ADMIN" else "/student/dashboard", status_code=302)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"request": request}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/admin/dashboard" if user['role'].upper() == "ADMIN" else "/student/dashboard", status_code=302)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"request": request}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/admin/dashboard" if user['role'].upper() == "ADMIN" else "/student/dashboard", status_code=302)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request}
    )

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin-login.html",
        {"request": request}
    )

@app.post("/auth/register")
async def register_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    department: str = Form(...),
    academic_year: str = Form(...)
):
    try:
        hashed_password = generate_password_hash(password)
        if not validate_email(email):
            return templates.TemplateResponse(
                request,
                "register.html",
                {"request": request, "error": "Invalid email format."}
            )
        if len(password) < 8:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"request": request, "error": "Password must be at least 8 characters long."}
            )

        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return templates.TemplateResponse(
                    request,
                    "register.html",
                    {"request": request, "error": "Email already registered."}
                )

            query = """
            INSERT INTO users (full_name, email, password_hash, department, academic_year, role)
            VALUES (%s, %s, %s, %s, %s, 'STUDENT')
            """
            cursor.execute(query, (full_name, email, hashed_password, department, academic_year))

        return templates.TemplateResponse(
            request,
            "register.html",
            {"request": request, "success": "Registration successful! You can now login."}
        )

    except Exception as e:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"request": request, "error": "An internal error occurred. Please try again."}
        )

@app.post("/auth/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        if not validate_email(email):
            return templates.TemplateResponse(
                request,
                "login.html",
                {"request": request, "error": "Invalid email format."}
            )

        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            return templates.TemplateResponse(
                request,
                "login.html" if "/admin/" not in str(request.url) else "admin-login.html",
                {"request": request, "error": "Invalid email or password."}
            )

        token = create_access_token({"user_id": user['id'], "role": user['role'], "email": user['email']})

        response = RedirectResponse(
            url=("/admin/dashboard?login=success" if user['role'].upper() == "ADMIN" else "/student/dashboard?login=success"),
            status_code=303
        )
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False
        )
        return response

    except Exception as e:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "An internal error occurred. Please try again."}
        )

@app.post("/auth/admin-login")
async def admin_login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        if not validate_email(email):
            return templates.TemplateResponse(
                request,
                "admin-login.html",
                {"request": request, "error": "Invalid email format."}
            )

        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            return templates.TemplateResponse(
                request,
                "admin-login.html",
                {"request": request, "error": "Invalid email or password."}
            )

        if user['role'].upper() != "ADMIN":
            return templates.TemplateResponse(
                request,
                "admin-login.html",
                {"request": request, "error": "Administrator access required."}
            )

        token = create_access_token({"user_id": user['id'], "role": user['role'], "email": user['email']})

        response = RedirectResponse(url="/admin/dashboard?login=success", status_code=303)
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False
        )
        return response

    except Exception as e:
        return templates.TemplateResponse(
            request,
            "admin-login.html",
            {"request": request, "error": "An internal error occurred. Please try again."}
        )

@app.get("/auth/logout")
async def logout_user():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response

@app.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'STUDENT':
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={"user": user}
    )

@app.get("/student/elections", response_class=HTMLResponse)
async def student_elections_list(request: Request, user = Depends(student_guard)):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, title, description, start_time, end_time, status FROM elections ORDER BY start_time ASC")
        elections = cursor.fetchall()
        for e in elections:
            e['start_time'] = ensure_datetime(e['start_time'])
            e['end_time'] = ensure_datetime(e['end_time'])

    active = [e for e in elections if e['status'] == 'ACTIVE']
    upcoming = [e for e in elections if e['status'] == 'UPCOMING']
    ended = [e for e in elections if e['status'] == 'ENDED']

    return templates.TemplateResponse(
        request,
        "student_elections.html",
        {"request": request, "active": active, "upcoming": upcoming, "ended": ended, "user": user}
    )

@app.get("/student/elections/{id}", response_class=HTMLResponse)
async def student_election_detail(request: Request, id: int, user = Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/student/elections", status_code=302)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT id FROM candidate_applications WHERE user_id = %s AND election_id = %s", (user['user_id'], id))
        has_applied = cursor.fetchone() is not None

    return templates.TemplateResponse(
        request,
        "student_election_detail.html",
        {"request": request, "election": election, "user": user, "has_applied": has_applied}
    )

@app.get("/student/elections/{id}/apply", response_class=HTMLResponse)
async def student_election_apply_page(request: Request, id: int, user = Depends(student_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/student/elections", status_code=302)

    if election['status'] != 'UPCOMING':
        return RedirectResponse(url="/student/elections", status_code=302)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT id FROM candidate_applications WHERE user_id = %s AND election_id = %s", (user['user_id'], id))
        if cursor.fetchone():
            return RedirectResponse(url="/student/candidate-status", status_code=302)

    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "student_election_apply.html",
        {"request": request, "election": election, "user": user, "csrf_token": csrf_token}
    )
    response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
    return response

@app.post("/candidates/apply")
async def apply_as_candidate(
    request: Request,
    election_id: int = Form(...),
    manifesto: str = Form(...),
    user = Depends(student_guard),
    csrf_token = Depends(verify_csrf)
):
    election = get_election_by_id(election_id)
    if not election or election['status'] != 'UPCOMING':
        return RedirectResponse(url="/student/elections", status_code=302)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT id FROM candidate_applications WHERE user_id = %s AND election_id = %s", (user['user_id'], election_id))
        if cursor.fetchone():
            return RedirectResponse(url="/student/candidate-status", status_code=302)

        query = "INSERT INTO candidate_applications (user_id, election_id, manifesto, approval_status) VALUES (%s, %s, %s, 'PENDING')"
        cursor.execute(query, (user['user_id'], election_id, manifesto))

    return RedirectResponse(url="/student/candidate-status", status_code=303)

@app.get("/student/candidate-status", response_class=HTMLResponse)
async def student_candidate_status(request: Request, user = Depends(student_guard)):
    with get_db_cursor() as cursor:
        query = """
        SELECT ca.id, ca.approval_status, ca.applied_at, e.title as election_title
        FROM candidate_applications ca
        JOIN elections e ON ca.election_id = e.id
        WHERE ca.user_id = %s
        ORDER BY ca.applied_at DESC
        """
        cursor.execute(query, (user['user_id'],))
        applications = cursor.fetchall()
        for app in applications:
            app['applied_at'] = ensure_datetime(app['applied_at']).strftime('%Y-%m-%d %H:%M') if app['applied_at'] else None

    return templates.TemplateResponse(
        request,
        "student_candidate_status.html",
        {"request": request, "applications": applications, "user": user}
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user = Depends(admin_guard)):
    with get_db_cursor() as cursor:
        try:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'STUDENT'")
            total_students = cursor.fetchone()['count']
        except Exception:
            total_students = 0

        try:
            cursor.execute("SELECT COUNT(*) as count FROM elections WHERE status = 'ACTIVE'")
            active_elections = cursor.fetchone()['count']
        except Exception:
            active_elections = 0

        try:
            cursor.execute("SELECT COUNT(*) as count FROM candidate_applications WHERE approval_status = 'PENDING'")
            pending_apps = cursor.fetchone()['count']
        except Exception:
            pending_apps = 0

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": user,
            "stats": {
                "total_students": total_students,
                "active_elections": active_elections,
                "pending_apps": pending_apps
            }
        }
    )

@app.get("/admin/elections", response_class=HTMLResponse)
async def list_elections(request: Request, user = Depends(admin_guard)):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, title, description, start_time, end_time, result_published FROM elections ORDER BY created_at DESC")
        elections = cursor.fetchall()
        for e in elections:
            e['start_time'] = ensure_datetime(e['start_time'])
            e['end_time'] = ensure_datetime(e['end_time'])

    success_key = request.query_params.get("success")
    success_message = SUCCESS_MESSAGE_MAP.get(success_key, None) if success_key else None

    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_elections.html",
        {"request": request, "elections": elections, "success_message": success_message, "csrf_token": csrf_token}
    )
    response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
    return response


@app.get("/admin/elections/create", response_class=HTMLResponse)
async def create_election_page(request: Request, user = Depends(admin_guard)):
    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_create.html",
        {"request": request, "csrf_token": csrf_token}
    )
    response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
    return response


@app.post("/admin/elections")
async def create_election(
    request: Request,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    user = Depends(admin_guard),
    csrf_token = Depends(verify_csrf)
):
    if not title or not start_time or not end_time:
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {"request": request, "error": "Title, start time, and end time are required.", "csrf_token": csrf_token}
        )
        response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
        return response

    try:
        s_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        e_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')


        if e_time <= s_time:
            csrf_token = await get_csrf_token(request)
            response = templates.TemplateResponse(
                request,
                "admin_election_create.html",
                {"request": request, "error": "End time must be after start time.", "values": {"title": title, "description": description, "start_time": start_time, "end_time": end_time}, "csrf_token": csrf_token}
            )
            response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
            return response

        with get_db_cursor() as cursor:
            query = "INSERT INTO elections (title, description, start_time, end_time, created_by) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (title, description, s_time, e_time, user['user_id']))

        return RedirectResponse(url="/admin/elections?success=created", status_code=303)

    except Exception as e:
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {"request": request, "error": "An internal error occurred. Please try again.", "values": {"title": title, "description": description, "start_time": start_time, "end_time": end_time}, "csrf_token": csrf_token}
        )
        response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
        return response

@app.get("/admin/elections/{id}", response_class=HTMLResponse)
async def edit_election_page(request: Request, id: int, user = Depends(admin_guard)):
    election = get_election_by_id(id)
    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)

    csrf_token = await get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin_election_edit.html",
        {"request": request, "election": election, "csrf_token": csrf_token}
    )
    response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
    return response


@app.post("/admin/elections/{id}/update")
async def update_election(
    request: Request,
    id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    user = Depends(admin_guard),
    csrf_token = Depends(verify_csrf)
):
    if not title or not start_time or not end_time:
        election = get_election_by_id(id)
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {"request": request, "error": "Title, start time, and end time are required.", "election": election, "csrf_token": csrf_token}
        )
        response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
        return response

    try:
        s_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        e_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')


        if e_time <= s_time:
            election = get_election_by_id(id)
            csrf_token = await get_csrf_token(request)
            response = templates.TemplateResponse(
                request,
                "admin_election_edit.html",
                {"request": request, "error": "End time must be after start time.", "election": election, "csrf_token": csrf_token}
            )
            response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
            return response

        with get_db_cursor() as cursor:
            query = "UPDATE elections SET title = %s, description = %s, start_time = %s, end_time = %s WHERE id = %s"
            cursor.execute(query, (title, description, s_time, e_time, id))

        return RedirectResponse(url="/admin/elections?success=updated", status_code=303)

    except Exception as e:
        logger.exception("Failed to update election")
        election = get_election_by_id(id)
        csrf_token = await get_csrf_token(request)
        response = templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {"request": request, "error": "An internal error occurred. Please try again.", "election": election, "csrf_token": csrf_token}
        )
        response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="lax", secure=False)
        return response

@app.post("/admin/elections/{id}/delete")
async def delete_election(request: Request, id: int, user = Depends(admin_guard), csrf_token = Depends(verify_csrf)):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM elections WHERE id = %s", (id,))
        return RedirectResponse(url="/admin/elections?success=deleted", status_code=303)
    except Exception as e:
        logger.exception("Failed to delete election")
        return RedirectResponse(url="/admin/elections?error=internal", status_code=303)


@app.get("/auth/me")
async def get_me(request: Request, user = Depends(get_current_user)):
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}
