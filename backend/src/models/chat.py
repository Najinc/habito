from typing import Any

from pydantic import BaseModel, Field


class CandidateItem(BaseModel):
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatAdviceRequest(BaseModel):
    query: str
    city: str
    question: str | None = None
    results: list[CandidateItem] = Field(default_factory=list)


class ChatAdviceResponse(BaseModel):
    answer: str
    recommended_url: str | None = None
