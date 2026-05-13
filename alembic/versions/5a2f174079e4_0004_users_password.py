"""0004_users_password

Revision ID: 5a2f174079e4
Revises: 10b0c9c68e8b
Create Date: 2026-05-13 20:55:42.042251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a2f174079e4'
down_revision: Union[str, Sequence[str], None] = '10b0c9c68e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'hashed_password')
