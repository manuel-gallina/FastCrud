from sqlalchemy import text
from sqlmodel import Session


def execute_raw_queries(session: Session, *queries: str) -> tuple:
    results = []
    for query in queries:
        # noinspection PyTypeChecker
        results.append(session.exec(text(query)))
    return tuple(results)
