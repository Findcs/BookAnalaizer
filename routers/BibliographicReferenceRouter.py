from fastapi import APIRouter, Depends, HTTPException, status

from schemas.BibliographicReferenceSchema import BibliographicReferenceSchema
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
        isbn: str,
        year: int,
        city:str,
        pages:int,
        service: BibliographicReferenceService = Depends(),
):
    """
    Эндпоинт для создания библиографической справки.
    """
    try:
        result = await service.create_reference(book_id, title, author, publisher, isbn, year, city, pages)
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
        raise HTTPException(status_code=500, detail=(e))

@BibliographicRouter.get(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def get_all_references(
        service: BibliographicReferenceService = Depends(),
):
    try:
        result = await service.get_all_references()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@BibliographicRouter.get(
    "/tags",
    status_code=status.HTTP_201_CREATED,
    response_model=list[BibliographicReferenceSchema]
)
async def get_all_references(
        service: BibliographicReferenceService = Depends(),
):
    try:
        result = await service.get_all_references_with_tags()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@BibliographicRouter.get("/by-section/{section_id}", response_model=list[BibliographicReferenceSchema])
async def get_references_by_section(
        section_id: int,
        service: BibliographicReferenceService = Depends()
):
    try:
        return await service.get_references_by_section(section_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")