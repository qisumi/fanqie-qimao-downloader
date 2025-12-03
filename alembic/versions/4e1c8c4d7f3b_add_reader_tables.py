"""add reader tables

Revision ID: 4e1c8c4d7f3b
Revises: f6814c43ce06
Create Date: 2025-12-03 13:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e1c8c4d7f3b'
down_revision: Union[str, Sequence[str], None] = 'f6814c43ce06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 阅读进度
    op.create_table(
        'reading_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('book_id', sa.String(), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter_id', sa.String(), sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('offset_px', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('percent', sa.Float(), nullable=False, server_default='0'),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id', 'user_id', 'device_id', name='uq_reading_progress_book_user_device'),
    )
    op.create_index('ix_reading_progress_user_book', 'reading_progress', ['user_id', 'book_id'], unique=False)

    # 书签
    op.create_table(
        'bookmarks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('book_id', sa.String(), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter_id', sa.String(), sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('offset_px', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('percent', sa.Float(), nullable=False, server_default='0'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bookmarks_user_book', 'bookmarks', ['user_id', 'book_id'], unique=False)

    # 阅读历史
    op.create_table(
        'reading_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('book_id', sa.String(), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter_id', sa.String(), sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('percent', sa.Float(), nullable=False, server_default='0'),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reading_history_user_book', 'reading_history', ['user_id', 'book_id'], unique=False)
    op.create_index('ix_reading_history_updated', 'reading_history', ['updated_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_reading_history_updated', table_name='reading_history')
    op.drop_index('ix_reading_history_user_book', table_name='reading_history')
    op.drop_table('reading_history')

    op.drop_index('ix_bookmarks_user_book', table_name='bookmarks')
    op.drop_table('bookmarks')

    op.drop_index('ix_reading_progress_user_book', table_name='reading_progress')
    op.drop_table('reading_progress')
