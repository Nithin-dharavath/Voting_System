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

def validate_password(password: str) -> bool:
    return len(password) >= 8


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
    print(f"DEBUG: get_current_user token: {token}")
    if not token:
        return None

    payload = decode_access_token(token)
    print(f"DEBUG: get_current_user payload: {payload}")
    if not payload:
        return None

    return payload

@app.get("/debug-role")
async def debug_role(request: Request):
    return {"role": request.state.user.get('role') if request.state.user else "None"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"request": request}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"request": request}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
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

        # Validate email and password
        if not validate_email(email):
            return templates.TemplateResponse(
                request,
                "register.html",
                {"request": request, "error": "Invalid email format."}
            )
        if not validate_password(password):
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

            # Insert new user
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
            "register.html",
            {"request": request, "error": f"An error occurred: {str(e)}"}
        )

@app.post("/auth/login")
async def login_user(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        if not validate_email(email):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid email format."}
            )

        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            # Determine if this was an admin login or student login based on referrer or a hidden field
            # For simplicity, we check the requested URL or use a default.
            # If it's an admin login, we might want to redirect back to /admin/login
            return templates.TemplateResponse(
                "login.html" if "/admin/" not in str(request.url) else "admin-login.html",
                {"request": request, "error": "Invalid email or password."}
            )

        token = create_access_token({"user_id": user['id'], "role": user['role'], "email": user['email']})

        response = RedirectResponse(
            url="/admin/dashboard" if user['role'] == "ADMIN" else "/student/dashboard"
        )
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False # Set to True in production with HTTPS
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
                "admin-login.html",
                {"request": request, "error": "Invalid email format."}
            )

        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        print(f"DEBUG: User found: {user}")
        if not user or not check_password_hash(user['password_hash'], password):
            print("DEBUG: Password verification failed")
            return templates.TemplateResponse(
                "admin-login.html",
                {"request": request, "error": "Invalid email or password."}
            )

        print(f"DEBUG: Role check: {user['role']} -> {user['role'].upper()}")
        if user['role'].upper() != "ADMIN":
            print("DEBUG: Role is not ADMIN")
            return templates.TemplateResponse(
                "admin-login.html",
                {"request": request, "error": "Administrator access required."}
            )

        token = create_access_token({"user_id": user['id'], "role": user['role'], "email": user['email']})

        response = RedirectResponse(url="/admin/dashboard")
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
            "admin-login.html",
            {"request": request, "error": f"An error occurred: {str(e)}"}
        )

@app.get("/auth/logout")
async def logout_user(response: Response):
    response = RedirectResponse(url="/login")
    response.delete_cookie(COOKIE_NAME)
    return response

@app.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'STUDENT':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html", # Placeholder template
        context={"user": user}
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user = Depends(get_current_user)):
    if not user or user['role'].upper() != 'ADMIN':
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html", # Placeholder template
        context={"user": user}
    )

@app.get("/auth/me")
async def get_me(request: Request, user = Depends(get_current_user)):
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}
