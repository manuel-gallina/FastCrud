"""user_password_hash

Revision ID: 4fa0fd934d53
Revises: 151d47c71e51
Create Date: 2025-02-11 16:36:58.198290

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4fa0fd934d53"
down_revision = "151d47c71e51"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE main.user ADD COLUMN password_hash varchar NOT NULL DEFAULT '';
    """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE main.user DROP COLUMN password_hash;
    """
    )
