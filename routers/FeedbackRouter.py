from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from uuid import UUID

from configs.Database import User
from schemas.BookFeedbackSchema import BookFeedbackSchema
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


@FeedbackRouter.get(
    "/{bibliographic_reference_id}",
    status_code=status.HTTP_201_CREATED,
)
async def get_by_bibliographic_reference_id(
    manager: FeedbackService = Depends(),
    bibliographic_reference_id: int = None
):
    try:
        result = await manager.get_by_bibliographic_reference_id(bibliographic_reference_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@FeedbackRouter.get("/by-book/{book_id}", response_model=list[BookFeedbackSchema])
async def get_feedback_for_book(book_id: int, service: FeedbackService = Depends()):
    try:
        return await service.get_feedbacks_for_book(book_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")