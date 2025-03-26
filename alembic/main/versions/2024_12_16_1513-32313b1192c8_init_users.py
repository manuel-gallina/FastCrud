"""init_users

Revision ID: 32313b1192c8
Revises: 
Create Date: 2024-12-16 15:13:29.577200

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "32313b1192c8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE ROLE "user";""")
    op.execute("""CREATE SCHEMA IF NOT EXISTS "main";""")
    op.execute("""GRANT USAGE ON SCHEMA main TO "user";""")
    op.execute(
        """ALTER DEFAULT PRIVILEGES IN SCHEMA main GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "user";"""
    )
    op.execute(
        """ALTER DEFAULT PRIVILEGES IN SCHEMA main GRANT EXECUTE ON FUNCTIONS TO "user";"""
    )
    op.execute(
        """ALTER DEFAULT PRIVILEGES IN SCHEMA main GRANT USAGE ON SEQUENCES TO "user";"""
    )


def downgrade() -> None:
    op.execute("""DROP SCHEMA IF EXISTS "main" CASCADE;""")
    op.execute("""DROP ROLE IF EXISTS "user";""")
