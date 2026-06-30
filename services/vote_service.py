import logging
from datetime import UTC, datetime, timedelta

from database.connection import get_db_cursor
from exceptions import ElectionError, VoteError
from services.candidate_service import get_approved_candidate_for_vote
from services.election_service import ensure_datetime, get_election_by_id

logger = logging.getLogger(__name__)


def has_user_voted(user_id: int, election_id: int) -> bool:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM votes WHERE voter_id = %s AND election_id = %s LIMIT 1",
            (user_id, election_id),
        )
        return cursor.fetchone() is not None


def get_user_vote_count(user_id: int) -> int:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM votes WHERE voter_id = %s", (user_id,))
        return cursor.fetchone()["count"]


def create_voting_session(user_id: int, election_id: int, candidate_application_id: int):
    election = get_election_by_id(election_id)
    if not election:
        raise ElectionError("Election not found.")
    if election["status"] != "ACTIVE":
        raise ElectionError("Voting is only available while the election is active.")
    if has_user_voted(user_id, election_id):
        raise VoteError("You have already voted in this election.")

    candidate = get_approved_candidate_for_vote(candidate_application_id, election_id)
    if not candidate:
        raise VoteError("Please select an approved candidate from this election.")

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO voting_sessions"
                " (student_id, election_id, started_at, expires_at,"
                " completed, candidate_application_id)"
                " VALUES (%s, %s, %s, %s, 0, %s)"
                " ON DUPLICATE KEY UPDATE"
                " candidate_application_id = %s,"
                " started_at = %s, expires_at = %s",
                (
                    user_id,
                    election_id,
                    datetime.now(UTC),
                    datetime.now(UTC) + timedelta(minutes=15),
                    candidate_application_id,
                    candidate_application_id,
                    datetime.now(UTC),
                    datetime.now(UTC) + timedelta(minutes=15),
                ),
            )
    except Exception as e:
        logger.exception("Failed to record session choice")
        raise VoteError("An internal error occurred. Please try again.") from e


def get_active_session(user_id: int, election_id: int) -> dict | None:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT candidate_application_id, expires_at"
            " FROM voting_sessions WHERE student_id = %s"
            " AND election_id = %s AND completed = 0",
            (user_id, election_id),
        )
        return cursor.fetchone()


def mark_session_completed(user_id: int, election_id: int):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "UPDATE voting_sessions SET completed = 1"
                " WHERE student_id = %s AND election_id = %s"
                " AND completed = 0",
                (user_id, election_id),
            )
    except Exception:
        logger.info(
            "Voting sessions table was not updated for election %s and user %s",
            election_id,
            user_id,
        )


def submit_vote_with_verification(
    user_id: int,
    election_id: int,
    verification_type: str,
    file_path: str,
) -> dict:
    election = get_election_by_id(election_id)
    if not election:
        raise ElectionError("Election not found.")
    if election["status"] != "ACTIVE":
        raise ElectionError("Voting is only available while the election is active.")
    if has_user_voted(user_id, election_id):
        raise VoteError("You have already voted in this election.")

    session = get_active_session(user_id, election_id)
    if not session or not session["candidate_application_id"]:
        raise VoteError("No active voting session found. Please select your candidate again.")

    expires_at = ensure_datetime(session["expires_at"])
    if expires_at and expires_at < datetime.now(UTC):
        raise VoteError("Your voting session has expired. Please select your candidate again.")

    candidate_application_id = session["candidate_application_id"]

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO votes"
                " (voter_id, election_id, candidate_id, voted_at)"
                " VALUES (%s, %s, %s, %s)",
                (user_id, election_id, candidate_application_id, datetime.now(UTC)),
            )
            cursor.execute(
                "INSERT INTO vote_verifications"
                " (student_id, election_id, verification_type,"
                " file_path, uploaded_at)"
                " VALUES (%s, %s, %s, %s, %s)",
                (user_id, election_id, verification_type, file_path, datetime.now(UTC)),
            )
            cursor.execute(
                "UPDATE voting_sessions SET completed = 1"
                " WHERE student_id = %s AND election_id = %s",
                (user_id, election_id),
            )
    except Exception as e:
        logger.exception("Verification transaction failed")
        raise VoteError("An internal error occurred during verification. Please try again.") from e

    return {"message": "Your vote has been recorded."}
