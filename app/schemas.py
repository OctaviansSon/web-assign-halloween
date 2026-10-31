from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt


class CriminalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = Field(description="Real name, null when unknown")
    nickname: str
    reward: int
    latitude: float | None = Field(description="Last known latitude, null when only a text note is known")
    longitude: float | None = Field(description="Last known longitude, null when only a text note is known")
    location_note: str | None = Field(description="Free-text note about the last known position")
    difficulty: int = Field(description="Overall difficulty rating, 1..10")
    armed: bool
    has_crew: bool
    escape_master: bool


class HuntCreate(BaseModel):
    """Body of POST /api/hunts/. `created_at` is not accepted: the server sets it (unknown fields are ignored)."""

    criminal_id: StrictInt = Field(examples=[3])
    success: StrictBool = Field(examples=[False])
    notes: str = Field(default="", max_length=5000, examples=["Target escaped through an asteroid field."])


class HuntUpdate(BaseModel):
    """Body of PATCH /api/hunts/{id}/ - only `success` and `notes` can be changed."""

    success: StrictBool | None = None
    notes: str | None = Field(default=None, max_length=5000)


class HuntOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    success: bool
    notes: str
    created_at: datetime
