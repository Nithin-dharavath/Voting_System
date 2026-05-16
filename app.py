from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from werkzeug.security import generate_password_hash
from database.connection import get_db_cursor

app = FastAPI()

# Mount the static directory to serve CSS, JS and images
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin-login.html"
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

        with get_db_cursor() as cursor:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return templates.TemplateResponse(
                    request=request,
                    name="register.html",
                    context={"error": "Email already registered."}
                )

            # Insert new user
            query = """
            INSERT INTO users (full_name, email, password_hash, department, academic_year, role)
            VALUES (%s, %s, %s, %s, %s, 'STUDENT')
            """
            cursor.execute(query, (full_name, email, hashed_password, department, academic_year))

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"success": "Registration successful! You can now login."}
        )

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": f"An error occurred: {str(e)}"}
        )
