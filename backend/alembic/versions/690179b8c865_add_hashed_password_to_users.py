"""add_hashed_password_to_users

Revision ID: 690179b8c865
Revises: 3ecb90078fa9
Create Date: 2026-10-17 12:55:34.221792

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '690179b8c865'
down_revision: Union[str, Sequence[str], None] = '3ecb90078fa9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "hashed_password" not in columns:
        op.add_column("users", sa.Column("hashed_password", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "hashed_password" in columns:
        op.drop_column("users", "hashed_password")
