"""initial_schema

Revision ID: 3ecb90078fa9
Revises: 
Create Date: 2026-10-17 12:55:13.795659

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '3ecb90078fa9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use inspector to safely check existing tables to preserve existing user data
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False, unique=True),
        )

    if "documents" not in tables:
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("upload_status", sa.String(), server_default="processing"),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        )

    if "conversations" not in tables:
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=True),
        )

    if "messages" not in tables:
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("documents")
    op.drop_table("users")
