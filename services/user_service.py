import logging

from database.connection import get_db_cursor
from exceptions import NotFoundError

logger = logging.getLogger(__name__)


def get_user_by_id(user_id: int) -> dict:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT user_id, full_name, email, department, academic_year, "
            "profile_picture, role FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
    if not user:
        raise NotFoundError("User not found.")
    return user


def get_student_count() -> int:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'STUDENT'")
        return cursor.fetchone()["count"]


def update_user_profile(
    user_id: int,
    full_name: str,
    department: str,
    academic_year: str,
    profile_path: str | None = None,
):
    with get_db_cursor() as cursor:
        if profile_path:
            query = (
                "UPDATE users SET full_name = %s, department = %s,"
                " academic_year = %s, profile_picture = %s WHERE user_id = %s"
            )
            cursor.execute(query, (full_name, department, academic_year, profile_path, user_id))
        else:
            query = (
                "UPDATE users SET full_name = %s, department = %s,"
                " academic_year = %s WHERE user_id = %s"
            )
            cursor.execute(query, (full_name, department, academic_year, user_id))


def get_user_candidate_applications(user_id: int) -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ca.id, ca.election_id, ca.approval_status, ca.applied_at,
                   e.title as election_title
            FROM candidate_applications ca
            JOIN elections e ON ca.election_id = e.id
            WHERE ca.user_id = %s
            ORDER BY ca.applied_at DESC
            """,
            (user_id,),
        )
        applications = cursor.fetchall()
        from services.election_service import format_datetime_simple

        for app in applications:
            app["applied_at"] = format_datetime_simple(app["applied_at"])
        return applications


def get_distinct_departments() -> list[str]:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT department FROM users WHERE department IS NOT NULL")
        return [row["department"] for row in cursor.fetchall()]
