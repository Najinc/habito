from typing import Any

from pydantic import BaseModel, Field


class Listing(BaseModel):
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)
