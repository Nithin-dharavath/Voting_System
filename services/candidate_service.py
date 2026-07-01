import logging

from database.connection import get_db_cursor
from exceptions import ValidationError
from services.election_service import format_datetime_simple, get_election_by_id

logger = logging.getLogger(__name__)


def has_user_applied(user_id: int, election_id: int) -> bool:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id FROM candidate_applications WHERE user_id = %s AND election_id = %s",
            (user_id, election_id),
        )
        return cursor.fetchone() is not None


def apply_as_candidate(user_id: int, election_id: int, manifesto: str):
    election = get_election_by_id(election_id)
    if not election or election["status"] != "UPCOMING":
        raise ValidationError("Applications are only accepted for upcoming elections.")

    if has_user_applied(user_id, election_id):
        raise ValidationError("You have already applied for this election.")

    with get_db_cursor() as cursor:
        query = (
            "INSERT INTO candidate_applications"
            " (user_id, election_id, manifesto, approval_status)"
            " VALUES (%s, %s, %s, 'PENDING')"
        )
        cursor.execute(query, (user_id, election_id, manifesto))


def get_user_applications(user_id: int) -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ca.id, ca.approval_status, ca.applied_at, e.title as election_title
            FROM candidate_applications ca
            JOIN elections e ON ca.election_id = e.id
            WHERE ca.user_id = %s
            ORDER BY ca.applied_at DESC
            """,
            (user_id,),
        )
        applications = cursor.fetchall()
        for app in applications:
            app["applied_at"] = format_datetime_simple(app["applied_at"])
        return applications


def get_applications_by_status(
    status: str,
    sort: str = "date",
    order: str = "ASC",
    category: str | None = None,
) -> list[dict]:
    valid_statuses = {"PENDING", "APPROVED", "REJECTED"}
    status = status.upper()
    if status not in valid_statuses:
        status = "PENDING"

    order = order.upper()
    if order not in ["ASC", "DESC"]:
        order = "ASC"

    sort_mapping = {"date": "ca.applied_at", "name": "u.full_name", "election": "e.title"}
    sort_field = sort_mapping.get(sort, "ca.applied_at")

    with get_db_cursor() as cursor:
        query = """
        SELECT ca.*, u.full_name as applicant_name, u.department, e.title as election_title
        FROM candidate_applications ca
        JOIN users u ON ca.user_id = u.user_id
        JOIN elections e ON ca.election_id = e.id
        WHERE ca.approval_status = %s
        """
        params = [status]

        if category:
            query += " AND u.department = %s"
            params.append(category)

        query += f" ORDER BY {sort_field} {order}"
        cursor.execute(query, tuple(params))
        applications = cursor.fetchall()
        for app in applications:
            app["applied_at"] = format_datetime_simple(app["applied_at"])
        return applications


def get_election_candidates(election_id: int) -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ca.*, u.full_name as applicant_name
            FROM candidate_applications ca
            JOIN users u ON ca.user_id = u.user_id
            WHERE ca.election_id = %s
            """,
            (election_id,),
        )
        applications = cursor.fetchall()
        for app in applications:
            app["applied_at"] = format_datetime_simple(app["applied_at"])
        return applications


def update_candidate_status(application_id: int, action: str, reviewed_by: int):
    if action not in ("approve", "reject"):
        raise ValidationError("Invalid action. Must be 'approve' or 'reject'.")

    status = "APPROVED" if action == "approve" else "REJECTED"
    with get_db_cursor() as cursor:
        query = (
            "UPDATE candidate_applications SET approval_status = %s, reviewed_by = %s WHERE id = %s"
        )
        cursor.execute(query, (status, reviewed_by, application_id))


def get_approved_candidates_for_election(election_id: int) -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ca.id,
                ca.user_id,
                ca.election_id,
                ca.manifesto,
                u.full_name AS candidate_name,
                u.department,
                u.academic_year
            FROM candidate_applications ca
            JOIN users u ON ca.user_id = u.user_id
            WHERE ca.election_id = %s AND ca.approval_status = 'APPROVED'
            ORDER BY u.full_name ASC
            """,
            (election_id,),
        )
        return cursor.fetchall()


def get_approved_candidate_for_vote(candidate_application_id: int, election_id: int) -> dict | None:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, election_id, approval_status
            FROM candidate_applications
            WHERE id = %s AND election_id = %s AND approval_status = 'APPROVED'
            LIMIT 1
            """,
            (candidate_application_id, election_id),
        )
        return cursor.fetchone()


def get_pending_count() -> int:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM candidate_applications WHERE approval_status = 'PENDING'"
        )
        return cursor.fetchone()["count"]


def bulk_update_candidate_status(ids: list[int], action: str, reviewed_by: int):
    if not ids:
        return
    if action not in ("approve", "reject"):
        raise ValidationError("Invalid action. Must be 'approve' or 'reject'.")
    status = "APPROVED" if action == "approve" else "REJECTED"
    placeholders = ",".join(["%s"] * len(ids))
    with get_db_cursor() as cursor:
        cursor.execute(
            f"UPDATE candidate_applications SET approval_status = %s, reviewed_by = %s"  # noqa: S608
            f" WHERE id IN ({placeholders})",
            (status, reviewed_by, *ids),
        )


def get_student_candidacy_status(user_id: int) -> str | None:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT approval_status FROM candidate_applications"
            " WHERE user_id = %s ORDER BY applied_at DESC LIMIT 1",
            (user_id,),
        )
        row = cursor.fetchone()
        return row["approval_status"] if row else None
