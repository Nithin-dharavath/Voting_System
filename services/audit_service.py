import json
import logging

from database.connection import get_db_cursor
from services.cache_service import cache_get, cache_set

logger = logging.getLogger(__name__)


def log_action(
    user_id: int,
    action_type: str,
    target_type: str,
    target_id: int | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO audit_log"
                " (user_id, action_type, target_type, target_id, details, ip_address)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    user_id,
                    action_type,
                    target_type,
                    target_id,
                    json.dumps(details) if details else None,
                    ip_address,
                ),
            )
    except Exception:
        logger.exception("Failed to log audit action")


def get_audit_logs(
    page: int = 1,
    per_page: int = 20,
    user_id: int | None = None,
    action_type: str | None = None,
    target_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[dict], int]:
    conditions: list[str] = []
    params: list[str | int] = []

    if user_id:
        conditions.append("al.user_id = %s")
        params.append(user_id)
    if action_type:
        conditions.append("al.action_type = %s")
        params.append(action_type)
    if target_type:
        conditions.append("al.target_type = %s")
        params.append(target_type)
    if date_from:
        conditions.append("al.created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("al.created_at <= %s")
        params.append(date_to)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    count_query = "SELECT COUNT(*) as count FROM audit_log al" + where_clause
    with get_db_cursor() as cursor:
        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()["count"]

    offset = (page - 1) * per_page
    data_query = (
        "SELECT al.*, u.full_name as user_name, u.email as user_email"
        " FROM audit_log al"
        " JOIN users u ON al.user_id = u.user_id"
        + where_clause
        + " ORDER BY al.created_at DESC LIMIT %s OFFSET %s"
    )
    params.extend([per_page, offset])
    with get_db_cursor() as cursor:
        cursor.execute(data_query, tuple(params))
        logs = cursor.fetchall()

    for log in logs:
        if log.get("details") and isinstance(log["details"], str):
            try:
                log["details"] = json.loads(log["details"])
            except (json.JSONDecodeError, TypeError):
                pass

    return logs, total


def get_action_types(use_cache: bool = True) -> list[str]:
    cache_key = "audit:action_types"
    if use_cache:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT action_type FROM audit_log ORDER BY action_type")
        result = [row["action_type"] for row in cursor.fetchall()]
    if use_cache:
        cache_set(cache_key, result, ttl=300)
    return result


def get_target_types(use_cache: bool = True) -> list[str]:
    cache_key = "audit:target_types"
    if use_cache:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT target_type FROM audit_log ORDER BY target_type")
        result = [row["target_type"] for row in cursor.fetchall()]
    if use_cache:
        cache_set(cache_key, result, ttl=300)
    return result
