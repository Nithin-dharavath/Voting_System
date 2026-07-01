import logging
from datetime import UTC, datetime

from database.connection import get_db_cursor
from exceptions import ElectionError, NotFoundError, ValidationError
from services.cache_service import cache_delete_prefix, cache_get, cache_set

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


def get_all_elections(status_filter: str | None = None) -> list[dict]:
    conditions = []
    params: list = []
    if status_filter:
        conditions.append("status = %s")
        params.append(status_filter.upper())
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    with get_db_cursor() as cursor:
        cursor.execute(
            f"SELECT id, title, description, start_time, end_time,"  # noqa: S608
            f" status, result_published FROM elections{where_clause}"
            f" ORDER BY created_at DESC",
            tuple(params),
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            if not status_filter:
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


def get_ended_elections_paginated(page: int = 1, per_page: int = 10) -> tuple[list[dict], int]:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM elections WHERE end_time <= NOW()",
        )
        total = cursor.fetchone()["count"]

    offset = (page - 1) * per_page
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, description, start_time, end_time, status, result_published
            FROM elections
            WHERE end_time <= NOW()
            ORDER BY end_time DESC
            LIMIT %s OFFSET %s
            """,
            (per_page, offset),
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = compute_election_status(e["start_time"], e["end_time"])
    return elections, total


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


def get_published_ended_elections_paginated(
    page: int = 1, per_page: int = 10
) -> tuple[list[dict], int]:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM elections"
            " WHERE end_time <= NOW() AND result_published = 1",
        )
        total = cursor.fetchone()["count"]

    offset = (page - 1) * per_page
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, description, start_time, end_time, status, result_published
            FROM elections
            WHERE end_time <= NOW() AND result_published = 1
            ORDER BY end_time DESC
            LIMIT %s OFFSET %s
            """,
            (per_page, offset),
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = compute_election_status(e["start_time"], e["end_time"])
    return elections, total


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
    cache_delete_prefix("dashboard:")


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
    cache_delete_prefix("dashboard:")


def delete_election(election_id: int):
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM vote_verifications WHERE election_id = %s", (election_id,))
        cursor.execute("DELETE FROM votes WHERE election_id = %s", (election_id,))
        cursor.execute("DELETE FROM voting_sessions WHERE election_id = %s", (election_id,))
        cursor.execute("DELETE FROM candidate_applications WHERE election_id = %s", (election_id,))
        cursor.execute("DELETE FROM elections WHERE id = %s", (election_id,))
    cache_delete_prefix("dashboard:")


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
        cache_delete_prefix("dashboard:")


def get_elections_results_batch(election_ids: list[int]) -> dict[int, tuple[list[dict], int]]:
    if not election_ids:
        return {}
    placeholders = ",".join(["%s"] * len(election_ids))
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT ca.election_id,
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
            WHERE ca.election_id IN ({placeholders}) AND ca.approval_status = 'APPROVED'
            GROUP BY ca.election_id, ca.id, u.full_name, u.department, u.academic_year, ca.manifesto
            ORDER BY ca.election_id, vote_count DESC, u.full_name ASC
            """,  # noqa: S608
            tuple(election_ids),
        )
        rows = cursor.fetchall()

    result_map: dict[int, list[dict]] = {}
    for r in rows:
        eid = r["election_id"]
        if eid not in result_map:
            result_map[eid] = []
        result_map[eid].append(r)

    output: dict[int, tuple[list[dict], int]] = {}
    for eid in election_ids:
        results = result_map.get(eid, [])
        total = sum(r["vote_count"] for r in results)
        for r in results:
            r["percentage"] = (r["vote_count"] / total * 100) if total else 0.0
        output[eid] = (results, total)
    return output


def get_elections_with_results() -> list[dict]:
    elections = get_ended_elections()
    if not elections:
        return []
    ids = [e["id"] for e in elections]
    batch = get_elections_results_batch(ids)
    election_results = []
    for election in elections:
        results, total_votes = batch.get(election["id"], ([], 0))
        election_results.append(
            {
                "election": election,
                "results": results,
                "total_votes": total_votes,
            }
        )
    return election_results


def get_dashboard_stats(use_cache: bool = True) -> dict:
    import logging

    logger = logging.getLogger(__name__)
    cache_key = "dashboard:stats"
    if use_cache:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    stats = {
        "total_students": 0,
        "total_elections": 0,
        "active_elections": 0,
        "total_votes": 0,
        "pending_apps": 0,
        "turnout_percentage": 0.0,
    }
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'STUDENT'")
            stats["total_students"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM elections")
            stats["total_elections"] = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM elections"
                " WHERE start_time <= NOW() AND end_time > NOW()"
            )
            stats["active_elections"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM votes")
            stats["total_votes"] = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM candidate_applications"
                " WHERE approval_status = 'PENDING'"
            )
            stats["pending_apps"] = cursor.fetchone()["count"]
    except Exception:
        logger.exception("Failed to get dashboard stats")

    if stats["total_students"] > 0:
        stats["turnout_percentage"] = round(
            (stats["total_votes"] / stats["total_students"]) * 100, 1
        )

    if use_cache:
        cache_set(cache_key, stats, ttl=60)
    return stats


def get_vote_trend(days: int = 7, use_cache: bool = True) -> list[dict]:
    import logging
    from datetime import UTC, datetime, timedelta

    logger = logging.getLogger(__name__)
    cache_key = f"dashboard:vote_trend:{days}"
    if use_cache:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=days - 1)
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT DATE(voted_at) AS vote_date, COUNT(*) AS count
                FROM votes
                WHERE voted_at >= %s AND voted_at < %s
                GROUP BY DATE(voted_at)
                ORDER BY vote_date ASC
                """,
                (start_date, today + timedelta(days=1)),
            )
            db_rows = cursor.fetchall()
            rows: dict = {}
            for r in db_rows:
                vd = r["vote_date"]
                if hasattr(vd, "strftime"):
                    key = vd.strftime("%Y-%m-%d")
                else:
                    key = str(vd)
                rows[key] = r["count"]
    except Exception:
        logger.exception("Failed to get vote trend")
        rows = {}

    trend = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        trend.append({"date": date_str, "votes": rows.get(date_str, 0)})

    if use_cache:
        cache_set(cache_key, trend, ttl=300)
    return trend


def get_elections_by_status_paginated(
    status: str, page: int = 1, per_page: int = 10
) -> tuple[list[dict], int]:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM elections WHERE status = %s",
            (status,),
        )
        total = cursor.fetchone()["count"]

    offset = (page - 1) * per_page
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, title, description, start_time, end_time,"
            " status, result_published FROM elections"
            " WHERE status = %s"
            " ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (status, per_page, offset),
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
    return elections, total


def get_elections_paginated(
    page: int = 1,
    per_page: int = 10,
    search: str | None = None,
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    params = []

    if search:
        conditions.append("e.title LIKE %s")
        params.append(f"%{search}%")
    if status_filter:
        conditions.append("e.status = %s")
        params.append(status_filter.upper())
    if date_from:
        conditions.append("e.start_time >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("e.end_time <= %s")
        params.append(date_to)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_db_cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) as count FROM elections e{where_clause}",  # noqa: S608
            tuple(params),
        )
        total = cursor.fetchone()["count"]

    offset = (page - 1) * per_page
    with get_db_cursor() as cursor:
        cursor.execute(
            f"SELECT e.id, e.title, e.description, e.start_time, e.end_time,"  # noqa: S608
            f" e.status, e.result_published, e.created_at"
            f" FROM elections e{where_clause}"
            f" ORDER BY e.created_at DESC LIMIT %s OFFSET %s",
            tuple(params) + (per_page, offset),
        )
        elections = cursor.fetchall()
        for e in elections:
            e["start_time"] = ensure_datetime(e["start_time"])
            e["end_time"] = ensure_datetime(e["end_time"])
            e["status"] = compute_election_status(e["start_time"], e["end_time"])
    return elections, total


def clone_election(
    election_id: int, new_title: str, new_start_time: str, new_end_time: str, created_by: int
):
    election = get_election_by_id(election_id)
    if not election:
        raise NotFoundError("Election not found.")
    create_election(new_title, election["description"], new_start_time, new_end_time, created_by)


def bulk_delete_elections(election_ids: list[int]):
    if not election_ids:
        return
    placeholders = ",".join(["%s"] * len(election_ids))
    with get_db_cursor() as cursor:
        cursor.execute(
            f"DELETE FROM elections WHERE id IN ({placeholders})",  # noqa: S608
            tuple(election_ids),
        )
    cache_delete_prefix("dashboard:")


def bulk_publish_results(election_ids: list[int]):
    if not election_ids:
        return
    placeholders = ",".join(["%s"] * len(election_ids))
    with get_db_cursor() as cursor:
        cursor.execute(
            f"UPDATE elections SET result_published = 1 WHERE id IN ({placeholders})"  # noqa: S608
            f" AND end_time <= NOW()",
            tuple(election_ids),
        )
    cache_delete_prefix("dashboard:")


def get_recent_activity(limit: int = 20, use_cache: bool = True) -> list[dict]:
    import logging

    logger = logging.getLogger(__name__)
    cache_key = f"dashboard:recent_activity:{limit}"
    if use_cache:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                (SELECT u.full_name, 'candidacy' as action_type, ca.applied_at as acted_at
                 FROM candidate_applications ca
                 JOIN users u ON ca.user_id = u.user_id
                 ORDER BY ca.applied_at DESC LIMIT %s)
                UNION ALL
                (SELECT u.full_name, 'vote' as action_type, v.voted_at as acted_at
                 FROM votes v
                 JOIN users u ON v.voter_id = u.user_id
                 ORDER BY v.voted_at DESC LIMIT %s)
                UNION ALL
                (SELECT u.full_name, 'election_created' as action_type, e.created_at as acted_at
                 FROM elections e
                 JOIN users u ON e.created_by = u.user_id
                 ORDER BY e.created_at DESC LIMIT %s)
                ORDER BY acted_at DESC LIMIT %s
                """,
                (limit, limit, limit, limit),
            )
            result = cursor.fetchall()
    except Exception:
        logger.exception("Failed to get recent activity")
        result = []

    from datetime import datetime

    for row in result:
        if isinstance(row.get("acted_at"), datetime):
            row["acted_at"] = row["acted_at"].strftime("%Y-%m-%d %H:%M")

    if use_cache:
        cache_set(cache_key, result, ttl=60)
    return result
