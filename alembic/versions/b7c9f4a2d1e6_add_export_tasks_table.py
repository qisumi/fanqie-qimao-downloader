"""add export tasks table

Revision ID: b7c9f4a2d1e6
Revises: 4e1c8c4d7f3b
Create Date: 2026-02-14 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c9f4a2d1e6"
down_revision: Union[str, Sequence[str], None] = "4e1c8c4d7f3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "export_tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("export_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True, server_default="not_started"),
        sa.Column("progress", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "export_type", name="uq_export_task_book_type"),
    )
    op.create_index("ix_export_tasks_book_id", "export_tasks", ["book_id"], unique=False)
    op.create_index("ix_export_tasks_export_type", "export_tasks", ["export_type"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_export_tasks_export_type", table_name="export_tasks")
    op.drop_index("ix_export_tasks_book_id", table_name="export_tasks")
    op.drop_table("export_tasks")
