"""users

Revision ID: 151d47c71e51
Revises: b99147b16dbf
Create Date: 2025-02-10 10:35:38.263402

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "151d47c71e51"
down_revision = "b99147b16dbf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE main.customer RENAME TO "user";
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE main."user" RENAME TO customer;
        """
    )
