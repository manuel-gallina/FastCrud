import time

# This script is used to keep the container running.
# It is used to allow terminal connections to the running container.
# This is useful to run alembic migrations on the database test container.

if __name__ == "__main__":
    while True:
        time.sleep(1)
