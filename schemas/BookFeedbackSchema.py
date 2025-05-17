from pydantic import BaseModel
from datetime import datetime
class UserShort(BaseModel):
    email: str
    rating: float
    class Config:
        orm_mode = True


class BookFeedbackSchema(BaseModel):
    id: int
    rating: float
    comment: str | None
    created_at: datetime
    user: UserShort

    class Config:
        orm_mode = True
