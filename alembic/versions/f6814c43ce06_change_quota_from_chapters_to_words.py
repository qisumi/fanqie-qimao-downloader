"""change_quota_from_chapters_to_words

Revision ID: f6814c43ce06
Revises: 9102b0e53518
Create Date: 2025-11-29 01:19:18.526021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6814c43ce06'
down_revision: Union[str, Sequence[str], None] = '9102b0e53518'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 words_downloaded 列，默认值为 0
    op.add_column('daily_quota', sa.Column('words_downloaded', sa.Integer(), nullable=False, server_default='0'))
    # 删除旧的 chapters_downloaded 列
    op.drop_column('daily_quota', 'chapters_downloaded')
    # 更新 limit 列的默认值为 20000000 (2000万字)
    # 注意: SQLite 使用双引号转义列名
    op.execute('UPDATE daily_quota SET "limit" = 20000000 WHERE "limit" = 200')


def downgrade() -> None:
    """Downgrade schema."""
    # 添加 chapters_downloaded 列
    op.add_column('daily_quota', sa.Column('chapters_downloaded', sa.INTEGER(), nullable=False, server_default='0'))
    # 删除 words_downloaded 列
    op.drop_column('daily_quota', 'words_downloaded')
    # 恢复 limit 列的旧值
    op.execute('UPDATE daily_quota SET "limit" = 200 WHERE "limit" = 20000000')
