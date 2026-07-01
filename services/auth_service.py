import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from database.connection import get_db_cursor
from exceptions import AuthError, ValidationError

logger = logging.getLogger(__name__)

JWT_SECRET_KEY: str | None = None
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "session_token"
CSRF_COOKIE_NAME = "csrf_token"


def configure_jwt(secret: str):
    global JWT_SECRET_KEY
    JWT_SECRET_KEY = secret


def get_jwt_secret() -> str:
    if JWT_SECRET_KEY is None:
        raise RuntimeError("JWT secret not configured. Call configure_jwt() during startup.")
    return JWT_SECRET_KEY


def create_access_token(data: dict, remember_me: bool = False) -> str:
    payload = data.copy()
    if remember_me:
        expire = datetime.now(UTC) + timedelta(days=30)
    else:
        expire = datetime.now(UTC) + timedelta(hours=1)
    payload.update({"exp": expire})
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


PASSWORD_MIN_LENGTH = 12


def validate_password_strength(password: str) -> str | None:
    import re

    errors = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"at least {PASSWORD_MIN_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        errors.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("a lowercase letter")
    if not re.search(r"\d", password):
        errors.append("a digit")
    if not re.search(r"[^a-zA-Z0-9]", password):
        errors.append("a special character")
    if errors:
        missing = "; ".join(errors)
        return f"Password must contain {missing}."
    return None


def register_user(
    full_name: str, email: str, password: str, department: str, academic_year: str
) -> dict:
    import re

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValidationError("Invalid email format.")

    password_error = validate_password_strength(password)
    if password_error:
        raise ValidationError(password_error)

    from services.breach_service import check_password_breached

    breach_count = check_password_breached(password)
    if breach_count and breach_count > 0:
        raise ValidationError(
            "This password has been exposed in a data breach. Please choose a different password."
        )

    hashed_password = generate_password_hash(password)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            raise ValidationError("Email already registered.")

        query = """
        INSERT INTO users (full_name, email, password_hash, department, academic_year, role)
        VALUES (%s, %s, %s, %s, %s, 'STUDENT')
        """
        cursor.execute(query, (full_name, email, hashed_password, department, academic_year))

    return {"message": "Registration successful! You can now login."}


def authenticate_user(
    email: str, password: str, require_admin: bool = False, remember_me: bool = False
) -> dict:
    import re

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise AuthError("Invalid email format.")

    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT user_id, email, password_hash, role FROM users WHERE email = %s", (email,)
        )
        user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        raise AuthError("Invalid email or password.")

    if require_admin and user["role"].upper() != "ADMIN":
        raise AuthError("Administrator access required.")

    from services.breach_service import check_password_breached

    breach_warning = None
    try:
        breach_count = check_password_breached(password)
        if breach_count and breach_count > 0:
            breach_warning = (
                f"This password has been exposed {breach_count} times in data breaches. "
                "Consider changing it."
            )
    except Exception:
        logger.debug("Breach check failed during login", exc_info=True)

    token = create_access_token(
        {
            "user_id": user["user_id"],
            "role": user["role"],
            "email": user["email"],
        },
        remember_me=remember_me,
    )

    result = {"token": token, "role": user["role"].upper()}
    if breach_warning:
        result["breach_warning"] = breach_warning
    return result


def get_user_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    return decode_access_token(token)
