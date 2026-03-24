from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    city: str
    lat: float | None = None
    lng: float | None = None
    radius: int = 10000
