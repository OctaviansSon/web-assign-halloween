from collections.abc import Iterator

from sqlalchemy.orm import Session

from .database import SessionLocal

MAX_ID = 2_147_483_647  # upper bound of an INTEGER primary key


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_possible_id(value: int) -> bool:
    """Ids start at 1 and fit into INTEGER; any other number cannot exist in the database."""
    return 1 <= value <= MAX_ID


def get_by_id(db: Session, model, obj_id: int):
    """Like db.get(), but returns None for impossible ids instead of letting the DB driver fail (HTTP 500)."""
    if not is_possible_id(obj_id):
        return None
    return db.get(model, obj_id)
