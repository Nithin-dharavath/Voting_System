"""initial_schema

Revision ID: 61a23139ab16
Revises:
Create Date: 2026-07-01 12:59:35.714745

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op  # type: ignore[attr-defined]

revision: str = "61a23139ab16"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", mysql.ENUM("STUDENT", "ADMIN"), nullable=False, server_default="STUDENT"),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("academic_year", sa.String(20), nullable=True),
        sa.Column("profile_picture", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "elections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            mysql.ENUM("UPCOMING", "ACTIVE", "ENDED"),
            nullable=False,
            server_default="UPCOMING",
        ),
        sa.Column("result_published", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "candidate_applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("election_id", sa.Integer(), nullable=False),
        sa.Column("manifesto", sa.Text(), nullable=True),
        sa.Column(
            "approval_status",
            mysql.ENUM("PENDING", "APPROVED", "REJECTED"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "applied_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["election_id"],
            ["elections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "voting_sessions",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("election_id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("candidate_application_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["election_id"],
            ["elections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("student_id", "election_id"),
    )
    op.create_table(
        "votes",
        sa.Column("voter_id", sa.Integer(), nullable=False),
        sa.Column("election_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column(
            "voted_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_applications.id"],
        ),
        sa.ForeignKeyConstraint(
            ["election_id"],
            ["elections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["voter_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("voter_id", "election_id"),
    )
    op.create_table(
        "vote_verifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("election_id", sa.Integer(), nullable=False),
        sa.Column(
            "verification_type",
            mysql.ENUM("FILE", "SELFIE", "SIGNATURE"),
            nullable=False,
            server_default="FILE",
        ),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["election_id"],
            ["elections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("vote_verifications")
    op.drop_table("votes")
    op.drop_table("voting_sessions")
    op.drop_table("candidate_applications")
    op.drop_table("elections")
    op.drop_table("users")
