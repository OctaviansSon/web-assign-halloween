"""Prefill the database with the sample data (8 wanted criminals, 14 hunt logs).

    python -m app.seed             # insert the data only if the tables are empty
    python -m app.seed --reset     # delete everything and insert the sample data again

In Docker:  docker compose exec api python -m app.seed --reset
"""
import sys
from datetime import timedelta

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal, engine, init_db
from .seed_data import CRIMINALS, HUNTS


def seed(db: Session) -> tuple[int, int]:
    """Insert the sample data. Hunt logs get timestamps spread over the last weeks."""
    now = models.utcnow()
    by_nickname: dict[str, models.WantedCriminal] = {}
    for data in CRIMINALS:
        criminal = models.WantedCriminal(**data)
        db.add(criminal)
        by_nickname[data["nickname"]] = criminal
    db.flush()  # assigns the ids

    for nickname, success, notes, days_ago in HUNTS:
        db.add(
            models.HuntLog(
                criminal_id=by_nickname[nickname].id,
                success=success,
                notes=notes,
                created_at=now - timedelta(days=days_ago),
            )
        )
    db.commit()
    return len(CRIMINALS), len(HUNTS)


def seed_if_empty(db: Session) -> bool:
    """Seed only an empty database, so restarts never create duplicates. Returns True if data was inserted."""
    if db.scalar(select(func.count()).select_from(models.WantedCriminal)):
        return False
    seed(db)
    return True


def reset(db: Session) -> None:
    """Remove all rows. On PostgreSQL the id counters are restarted too, so ids begin at 1 again."""
    if engine.dialect.name == "postgresql":
        db.execute(text("TRUNCATE TABLE hunt_logs, wanted_criminals RESTART IDENTITY"))
    else:
        db.execute(delete(models.HuntLog))
        db.execute(delete(models.WantedCriminal))
    db.commit()


def main(argv: list[str]) -> None:
    init_db()
    with SessionLocal() as db:
        if "--reset" in argv:
            reset(db)
            criminals, hunts = seed(db)
            print(f"Database reset: inserted {criminals} criminals and {hunts} hunt logs.")
        elif seed_if_empty(db):
            print(f"Inserted {len(CRIMINALS)} criminals and {len(HUNTS)} hunt logs.")
        else:
            print("Database already contains data - nothing to do (use --reset to re-create the sample data).")


if __name__ == "__main__":
    main(sys.argv[1:])
