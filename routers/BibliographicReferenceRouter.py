from fastapi import APIRouter, Depends, HTTPException, status
from services.BibliographicReferenceService import BibliographicReferenceService
from services.RecommendationService import RecommendationService

BibliographicRouter = APIRouter(prefix="/v1/bibliographic", tags=["bibliographic"])


@BibliographicRouter.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_bibliographic_reference(
        book_id: int,
        title: str,
        author: str,
        publisher: str,
        service: BibliographicReferenceService = Depends(),
):
    """
    Эндпоинт для создания библиографической справки.
    """
    try:
        result = await service.create_reference(book_id, title, author, publisher)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@BibliographicRouter.get(
    "/recs",
    status_code=status.HTTP_201_CREATED,
)
async def create_bibliographic_reference(
        book_id: int,
        recommendation_service: RecommendationService = Depends()):
    try:
        result = await recommendation_service.get_recommendations(book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
