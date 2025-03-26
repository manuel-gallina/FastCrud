import asyncio

from faker import Faker
from sqlmodel import Session
from uuid6 import uuid7

from app.core.models.main.user import User
from system.database.session import get_database_engine
from system.database.settings import DatabaseId
from system.logging.setup import init_logging

import nacl.pwhash


async def seed_users(count: int, batch_size: int | None = None) -> None:
    logger = init_logging()

    if batch_size:
        for _ in range(count // batch_size):
            await seed_users(batch_size)
        return

    engine = get_database_engine(DatabaseId.MAIN)
    with Session(engine) as database_session:
        fake = Faker()

        for i in range(count):
            user_id = uuid7()
            user = User(
                id=user_id,
                name=fake.name(),
                email=f"{user_id}@{fake.free_email_domain()}",
                phone=fake.phone_number(),
                address=fake.address(),
                password_hash=nacl.pwhash.str(str(user_id).encode()).decode(),
            )
            database_session.add(user)
            logger.info(f"Seeded user {i + 1}/{count}: {user}")
        database_session.commit()


if __name__ == "__main__":
    asyncio.run(seed_users(1_000, 500))
