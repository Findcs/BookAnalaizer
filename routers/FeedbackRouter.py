from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from uuid import UUID

from configs.Database import User
from services.FeedbackService import FeedbackService
from services.BookService import BookService
from services.UserService import current_active_user

FeedbackRouter = APIRouter(prefix="/v1/feedback", tags=["feedback"])


@FeedbackRouter.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def add_feedback(
    user_id: UUID,
    bibliographic_reference_id: int,
    rating: float,
    comment: str = None,
    manager: FeedbackService = Depends()
):
    try:
        result = await manager.add_feedback(user_id, bibliographic_reference_id, rating, comment)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))