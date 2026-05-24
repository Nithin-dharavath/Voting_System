from fastapi import FastAPI, Request, Form, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import get_db_cursor
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
import re

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

JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-this-in-env")
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "session_token"

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
        return RedirectResponse(url="/admin/login", status_code=302)
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
            {"request": request, "error": f"An error occurred: {str(e)}"}
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
            {"request": request, "error": f"An error occurred: {str(e)}"}
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
            {"request": request, "error": f"An error occurred: {str(e)}"}
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
async def list_elections(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login", status_code=302)
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, title, description, start_time, end_time, result_published FROM elections ORDER BY created_at DESC")
        elections = cursor.fetchall()
        for e in elections:
            e['start_time'] = ensure_datetime(e['start_time'])
            e['end_time'] = ensure_datetime(e['end_time'])

    return templates.TemplateResponse(
        request,
        "admin_elections.html",
        {"request": request, "elections": elections}
    )


@app.get("/admin/elections/create", response_class=HTMLResponse)
async def create_election_page(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "admin_election_create.html",
        {"request": request}
    )


@app.post("/admin/elections")
async def create_election(
    request: Request,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    user = Depends(get_current_user)
):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login", status_code=302)

    if not title or not start_time or not end_time:
        return templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {"request": request, "error": "Title, start time, and end time are required."}
        )

    try:
        s_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        e_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')


        if e_time <= s_time:
            return templates.TemplateResponse(
                request,
                "admin_election_create.html",
                {"request": request, "error": "End time must be after start time.", "values": {"title": title, "description": description, "start_time": start_time, "end_time": end_time}}
            )

        with get_db_cursor() as cursor:
            query = "INSERT INTO elections (title, description, start_time, end_time, created_by) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (title, description, s_time, e_time, user['user_id']))

        return RedirectResponse(url="/admin/elections?success=created", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            request,
            "admin_election_create.html",
            {"request": request, "error": f"An error occurred: {str(e)}", "values": {"title": title, "description": description, "start_time": start_time, "end_time": end_time}}
        )

@app.get("/admin/elections/{id}", response_class=HTMLResponse)
async def edit_election_page(request: Request, id: int, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login", status_code=302)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, title, description, start_time, end_time, result_published FROM elections WHERE id = %s", (id,))
        election = cursor.fetchone()
        if election:
            election['start_time'] = ensure_datetime(election['start_time'])
            election['end_time'] = ensure_datetime(election['end_time'])

    if not election:
        return RedirectResponse(url="/admin/elections", status_code=302)

    return templates.TemplateResponse(
        request,
        "admin_election_edit.html",
        {"request": request, "election": election}
    )


@app.post("/admin/elections/{id}/update")
async def update_election(
    request: Request,
    id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    user = Depends(get_current_user)
):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login", status_code=302)

    if not title or not start_time or not end_time:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, title, description, start_time, end_time, result_published FROM elections WHERE id = %s", (id,))
            election = cursor.fetchone()
            if election:
                election['start_time'] = ensure_datetime(election['start_time'])
                election['end_time'] = ensure_datetime(election['end_time'])
        return templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {"request": request, "error": "Title, start time, and end time are required.", "election": election}
        )

    try:
        s_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        e_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')


        if e_time <= s_time:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT id, title, description, start_time, end_time, result_published FROM elections WHERE id = %s", (id,))
                election = cursor.fetchone()
                if election:
                    election['start_time'] = ensure_datetime(election['start_time'])
                    election['end_time'] = ensure_datetime(election['end_time'])
            return templates.TemplateResponse(
                request,
                "admin_election_edit.html",
                {"request": request, "error": "End time must be after start time.", "election": election}
            )

        with get_db_cursor() as cursor:
            query = "UPDATE elections SET title = %s, description = %s, start_time = %s, end_time = %s WHERE id = %s"
            cursor.execute(query, (title, description, s_time, e_time, id))

        return RedirectResponse(url="/admin/elections?success=updated", status_code=303)

    except Exception as e:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, title, description, start_time, end_time, result_published FROM elections WHERE id = %s", (id,))
            election = cursor.fetchone()
            if election:
                election['start_time'] = ensure_datetime(election['start_time'])
                election['end_time'] = ensure_datetime(election['end_time'])
        return templates.TemplateResponse(
            request,
            "admin_election_edit.html",
            {"request": request, "error": f"An error occurred: {str(e)}", "election": election}
        )

@app.post("/admin/elections/{id}/delete")
async def delete_election(request: Request, id: int, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login", status_code=302)

    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM elections WHERE id = %s", (id,))
        return RedirectResponse(url="/admin/elections?success=deleted", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/admin/elections?error={str(e)}", status_code=303)


@app.get("/auth/me")
async def get_me(request: Request, user = Depends(get_current_user)):
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}
