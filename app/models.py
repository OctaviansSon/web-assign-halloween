from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WantedCriminal(Base):
    """A criminal from the bounty database."""

    __tablename__ = "wanted_criminals"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 10", name="ck_criminal_difficulty_range"),
        CheckConstraint("reward >= 0", name="ck_criminal_reward_non_negative"),
        CheckConstraint("latitude IS NULL OR latitude BETWEEN -90 AND 90", name="ck_criminal_latitude_range"),
        CheckConstraint("longitude IS NULL OR longitude BETWEEN -180 AND 180", name="ck_criminal_longitude_range"),
        # last known position is either a full (latitude, longitude) pair or no coordinates at all
        CheckConstraint("(latitude IS NULL) = (longitude IS NULL)", name="ck_criminal_coordinates_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)  # real name, may be unknown
    nickname: Mapped[str] = mapped_column(String(80), index=True)
    reward: Mapped[int] = mapped_column(Integer, index=True)
    # last known position: coordinates and/or a free-text note
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer)  # 1 (easy) .. 10 (very hard)
    armed: Mapped[bool] = mapped_column(Boolean, default=False)
    has_crew: Mapped[bool] = mapped_column(Boolean, default=False)
    escape_master: Mapped[bool] = mapped_column(Boolean, default=False)

    # one criminal -> many hunt attempts
    hunts: Mapped[list["HuntLog"]] = relationship(
        back_populates="criminal", cascade="all, delete-orphan", order_by="HuntLog.id"
    )


class HuntLog(Base):
    """One entry of the bounty hunters' journal: a single capture attempt."""

    __tablename__ = "hunt_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    criminal_id: Mapped[int] = mapped_column(
        ForeignKey("wanted_criminals.id", ondelete="CASCADE"), index=True
    )
    success: Mapped[bool] = mapped_column(Boolean)  # True = the criminal was captured
    notes: Mapped[str] = mapped_column(Text, default="")
    # always set by the server (never read from the request body)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    criminal: Mapped[WantedCriminal] = relationship(back_populates="hunts")
