"""devices

Revision ID: 8efba66f1dc9
Revises: 4fa0fd934d53
Create Date: 2025-02-12 15:22:49.978119

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8efba66f1dc9"
down_revision = "4fa0fd934d53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE main.device
        (
            id            uuid    NOT NULL
                CONSTRAINT device_pk
                    PRIMARY KEY,
            user_id       uuid    NOT NULL
                CONSTRAINT device_user_id_fk
                    REFERENCES main."user",
            code          varchar NOT NULL,
            refresh_token varchar NOT NULL,
            CONSTRAINT device_uq_user_id_code
                UNIQUE (user_id, code)
        ); 
    """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE main.device;
    """
    )
