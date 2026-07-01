"""add_performance_indexes

Revision ID: e379a0fe56ec
Revises: 2c8a9f3d1b4e
Create Date: 2026-07-02 00:29:27.637256

"""

from collections.abc import Sequence

from alembic import op  # type: ignore[attr-defined]

revision: str = "e379a0fe56ec"
down_revision: str | Sequence[str] | None = "2c8a9f3d1b4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("idx_elections_start_end", "elections", ["start_time", "end_time"])
    op.create_index("idx_elections_published_ended", "elections", ["result_published", "end_time"])
    op.create_index("idx_elections_created_at", "elections", ["created_at"])
    op.create_index("idx_elections_created_by", "elections", ["created_by"])

    op.create_index(
        "idx_ca_election_status", "candidate_applications", ["election_id", "approval_status"]
    )
    op.create_index("idx_ca_user_election", "candidate_applications", ["user_id", "election_id"])
    op.create_index("idx_ca_approval_status", "candidate_applications", ["approval_status"])
    op.create_index("idx_ca_applied_at", "candidate_applications", ["applied_at"])

    op.create_index("idx_votes_election_candidate", "votes", ["election_id", "candidate_id"])
    op.create_index("idx_votes_voted_at", "votes", ["voted_at"])
    op.create_index("idx_votes_election_voter", "votes", ["election_id", "voter_id"])

    op.create_index(
        "idx_vs_student_election_completed",
        "voting_sessions",
        ["student_id", "election_id", "completed"],
    )
    op.create_index("idx_vs_expires_at", "voting_sessions", ["expires_at"])

    op.create_index("idx_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("idx_elections_start_end", table_name="elections")
    op.drop_index("idx_elections_published_ended", table_name="elections")
    op.drop_index("idx_elections_created_at", table_name="elections")
    op.drop_index("idx_elections_created_by", table_name="elections")

    op.drop_index("idx_ca_election_status", table_name="candidate_applications")
    op.drop_index("idx_ca_user_election", table_name="candidate_applications")
    op.drop_index("idx_ca_approval_status", table_name="candidate_applications")
    op.drop_index("idx_ca_applied_at", table_name="candidate_applications")

    op.drop_index("idx_votes_election_candidate", table_name="votes")
    op.drop_index("idx_votes_voted_at", table_name="votes")
    op.drop_index("idx_votes_election_voter", table_name="votes")

    op.drop_index("idx_vs_student_election_completed", table_name="voting_sessions")
    op.drop_index("idx_vs_expires_at", table_name="voting_sessions")

    op.drop_index("idx_users_role", table_name="users")
