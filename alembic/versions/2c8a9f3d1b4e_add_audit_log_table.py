"""add_audit_log_table

Revision ID: 2c8a9f3d1b4e
Revises: 61a23139ab16
Create Date: 2026-07-01 23:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op  # type: ignore[attr-defined]

revision: str = "2c8a9f3d1b4e"
down_revision: str | Sequence[str] | None = "61a23139ab16"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("details", mysql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_user_id", "audit_log", ["user_id"])
    op.create_index("idx_audit_action_type", "audit_log", ["action_type"])
    op.create_index("idx_audit_target_type", "audit_log", ["target_type"])
    op.create_index("idx_audit_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_created_at", table_name="audit_log")
    op.drop_index("idx_audit_target_type", table_name="audit_log")
    op.drop_index("idx_audit_action_type", table_name="audit_log")
    op.drop_index("idx_audit_user_id", table_name="audit_log")
    op.drop_table("audit_log")
