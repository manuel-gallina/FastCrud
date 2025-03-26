"""customer

Revision ID: b99147b16dbf
Revises: 32313b1192c8
Create Date: 2024-12-16 16:16:08.153210

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b99147b16dbf"
down_revision = "32313b1192c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE main.customer
        (
            id      uuid NOT NULL
                CONSTRAINT customer_pk
                    PRIMARY KEY,
            name    varchar NOT NULL,
            email   varchar NOT NULL,
            phone   varchar NOT NULL,
            address varchar NOT NULL
        );
    """
    )
    op.execute(
        """
    CREATE UNIQUE INDEX customer_email_uindex
    ON main.customer (email);"""
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX customer_email_uindex 
    """
    )
    op.execute("""DROP TABLE main.customer;""")
