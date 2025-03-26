from alembic import context

from system.database.session import get_database_engine
from system.database.settings import DatabaseId

engine = get_database_engine(DatabaseId.MAIN)
with engine.connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
