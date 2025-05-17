from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from uuid import UUID

from configs.Database import User
from services.FeedbackService import FeedbackService
from services.BookService import BookService
from services.UserService import current_active_user

DocumentRouter = APIRouter(prefix="/v1/documents", tags=["documents"])

@DocumentRouter.get(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def get_all_user_books(
        manager: BookService = Depends(),
        user: User = Depends(current_active_user)
):
    try:
        result = await manager.get_all_user_books(user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


