from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RequestPostRequestSchema(BaseModel):
    time: Optional[datetime] = Field(default=datetime.today())
    user_id: int
    book: bytes
    book_title: str


class RequestCreate(BaseModel):
    result: Optional[list[str]] = []
