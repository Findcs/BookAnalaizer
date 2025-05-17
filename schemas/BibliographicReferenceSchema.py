from datetime import datetime

from pydantic import BaseModel, field_serializer, Field
from typing import Optional, List


class BookSchema(BaseModel):
    id: int
    bookTitle: str
    tags: Optional[List[str]] = None
    is_public: bool
    time: datetime

    class Config:
        orm_mode = True


class BibliographicReferenceSchema(BaseModel):
    id: int
    title: str
    author: str
    publisher: str
    isbn: str
    year: int
    city: str
    pages: int
    average_rating: float
    rating_count: int
    book: Optional[BookSchema]

    gost_citation: Optional[str] = Field(default=None)

    @field_serializer("gost_citation")
    def get_gost(self, value, _info):
        return f"{self.author}. {self.title}. – {self.city}: {self.publisher}, {self.year}. – {self.pages} с."


class Config:
        orm_mode = True
