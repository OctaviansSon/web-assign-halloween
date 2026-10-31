from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import MAX_ID, get_by_id, get_db

router = APIRouter(prefix="/criminals", tags=["Wanted criminals"])


@router.get(
    "/",
    response_model=list[schemas.CriminalOut],
    responses={422: {"description": "Invalid query parameter"}},
)
def list_criminals(
    min_reward: int | None = Query(default=None, ge=0, le=MAX_ID, description="Minimum bounty (inclusive)"),
    max_reward: int | None = Query(default=None, ge=0, le=MAX_ID, description="Maximum bounty (inclusive)"),
    armed: bool | None = Query(default=None, description="true / false"),
    has_crew: bool | None = Query(default=None, description="true / false"),
    escape_master: bool | None = Query(default=None, description="true / false"),
    sort: Literal["reward", "-reward"] | None = Query(
        default=None, description="`reward` = cheapest first, `-reward` = most expensive first"
    ),
    db: Session = Depends(get_db),
):
    """List wanted criminals. All filters are optional and are combined with AND."""
    if min_reward is not None and max_reward is not None and min_reward > max_reward:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "min_reward must not be greater than max_reward")

    stmt = select(models.WantedCriminal)
    if min_reward is not None:
        stmt = stmt.where(models.WantedCriminal.reward >= min_reward)
    if max_reward is not None:
        stmt = stmt.where(models.WantedCriminal.reward <= max_reward)
    # `is not None` (not truthiness): armed=false must filter too, it is not "no filter"
    if armed is not None:
        stmt = stmt.where(models.WantedCriminal.armed == armed)
    if has_crew is not None:
        stmt = stmt.where(models.WantedCriminal.has_crew == has_crew)
    if escape_master is not None:
        stmt = stmt.where(models.WantedCriminal.escape_master == escape_master)

    # the id tie-breaker keeps the order stable when several criminals have the same reward
    if sort == "reward":
        stmt = stmt.order_by(models.WantedCriminal.reward.asc(), models.WantedCriminal.id)
    elif sort == "-reward":
        stmt = stmt.order_by(models.WantedCriminal.reward.desc(), models.WantedCriminal.id)
    else:
        stmt = stmt.order_by(models.WantedCriminal.id)
    return db.scalars(stmt).all()


@router.get(
    "/{criminal_id}/",
    response_model=schemas.CriminalOut,
    responses={404: {"description": "Criminal not found"}},
)
def get_criminal(criminal_id: int, db: Session = Depends(get_db)):
    criminal = get_by_id(db, models.WantedCriminal, criminal_id)
    if criminal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Criminal not found")
    return criminal
