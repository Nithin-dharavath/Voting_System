import logging
from datetime import UTC, datetime

from database.connection import get_db_cursor
from exceptions import ElectionError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def ensure_datetime(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    try:
        dt_obj = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        return dt_obj.replace(tzinfo=UTC)
    except ValueError:
        try:
            dt_obj = datetime.fromisoformat(dt)
            if dt_obj.tzinfo is None:
                return dt_obj.replace(tzinfo=UTC)
            return dt_obj
        except ValueError:
            return dt


def format_datetime_simple(dt):
    dt_obj = ensure_datetime(dt)
    return dt_obj.strftime("%Y-%m-%d %H:%M") if dt_obj else None


def compute_election_status(start_time, end_time) -> str:
    now = datetime.now(UTC)
    start = ensure_datetime(start_time)
    end = ensure_datetime(end_time)
    if now < start:
        return "UPCOMING"
    elif now >= end:
        return "ENDED"
    return "ACTIVE"


def get_election_by_id(election_id: int) -> dict | None:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, title, description, start_time, end_time,"
            " result_published, status, created_by"
            " FROM elections WHERE id = %s",
            (election_id,),
        )
        election = cursor.fetchone()
        if election:
            election["start_time"] = ensure_datetime(election["start_time"])
            election["end_time"] = ensure_datetime(election["end_time"])
            election["status"] = compute_election_status(
                election["start_time"], election["end_time"]
            )
        return election


def get_all_elections() -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, title, description, start_time, end_time,"
            " status, result_published FROM elections"
            " ORDER BY created_at DESC"
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = compute_election_status(e["start_time"], e["end_time"])
        return elections


def get_upcoming_elections() -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, title, description, start_time, end_time"
            " FROM elections WHERE start_time > NOW()"
            " ORDER BY start_time ASC"
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = "UPCOMING"
        return elections


def get_active_elections_count() -> int:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM elections WHERE start_time <= NOW() AND end_time > NOW()"
        )
        return cursor.fetchone()["count"]


def get_ended_elections() -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, description, start_time, end_time, status, result_published
            FROM elections
            WHERE end_time <= NOW()
            ORDER BY end_time DESC
            """
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = compute_election_status(e["start_time"], e["end_time"])
        return elections


def get_published_ended_elections() -> list[dict]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, description, start_time, end_time, status, result_published
            FROM elections
            WHERE end_time <= NOW() AND result_published = 1
            ORDER BY end_time DESC
            """
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = compute_election_status(e["start_time"], e["end_time"])
        return elections


def create_election(
    title: str, description: str | None, start_time: str, end_time: str, created_by: int
):
    try:
        s_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        e_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise ValidationError("Invalid date/time format. Use YYYY-MM-DDTHH:MM.")

    if e_time <= s_time:
        raise ValidationError("End time must be after start time.")

    status = compute_election_status(s_time, e_time)
    with get_db_cursor() as cursor:
        query = (
            "INSERT INTO elections"
            " (title, description, start_time, end_time, status, created_by)"
            " VALUES (%s, %s, %s, %s, %s, %s)"
        )
        cursor.execute(query, (title, description, s_time, e_time, status, created_by))


def update_election(
    election_id: int, title: str, description: str | None, start_time: str, end_time: str
):
    try:
        s_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        e_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise ValidationError("Invalid date/time format. Use YYYY-MM-DDTHH:MM.")

    if e_time <= s_time:
        raise ValidationError("End time must be after start time.")

    status = compute_election_status(s_time, e_time)
    with get_db_cursor() as cursor:
        query = (
            "UPDATE elections SET title = %s, description = %s,"
            " start_time = %s, end_time = %s, status = %s"
            " WHERE id = %s"
        )
        cursor.execute(query, (title, description, s_time, e_time, status, election_id))


def delete_election(election_id: int):
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM elections WHERE id = %s", (election_id,))


def get_election_results(election_id: int) -> tuple[list[dict], int]:
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ca.id           AS candidate_application_id,
                u.full_name     AS candidate_name,
                u.department    AS department,
                u.academic_year AS academic_year,
                ca.manifesto    AS manifesto,
                COUNT(v.candidate_id) AS vote_count
            FROM candidate_applications ca
            JOIN users u ON ca.user_id = u.user_id
            LEFT JOIN votes v
                ON v.candidate_id = ca.id AND v.election_id = ca.election_id
            WHERE ca.election_id = %s AND ca.approval_status = 'APPROVED'
            GROUP BY ca.id, u.full_name, u.department, u.academic_year, ca.manifesto
            ORDER BY vote_count DESC, u.full_name ASC
            """,
            (election_id,),
        )
        rows = cursor.fetchall()
    total = sum(r["vote_count"] for r in rows)
    for r in rows:
        r["percentage"] = (r["vote_count"] / total * 100) if total else 0.0
    return rows, total


def publish_results(election_id: int):
    election = get_election_by_id(election_id)
    if not election:
        raise NotFoundError("Election not found.")
    if election["status"] != "ENDED":
        raise ElectionError("Results can only be published for ended elections.")
    if not election["result_published"]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "UPDATE elections SET result_published = 1 WHERE id = %s", (election_id,)
            )


def get_elections_with_results() -> list[dict]:
    elections = get_ended_elections()
    election_results = []
    for election in elections:
        results, total_votes = get_election_results(election["id"])
        election_results.append(
            {
                "election": election,
                "results": results,
                "total_votes": total_votes,
            }
        )
    return election_results
