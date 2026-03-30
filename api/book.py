from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from uuid import UUID

from schemas.book import BookCreate, BookResponse, BookStatus
from services.book import BookService
from repository.book import BookRepository
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/books", tags=["Books"])

def get_book_service(db: AsyncSession = Depends(get_db)) -> BookService:
    repository = BookRepository(db)
    return BookService(repository)

@router.get("/", response_model=List[BookResponse], status_code=status.HTTP_200_OK)
async def get_books(
    skip: int = Query(0, ge=0, description="Пагінація: offset (зміщення)"),
    limit: int = Query(10, ge=1, le=100, description="Пагінація: limit (скільки вибрати)"),
    status: Optional[BookStatus] = Query(None, description="Фільтр по статусу"),
    author: Optional[str] = Query(None, description="Фільтр по автору"),
    sort_by: Optional[str] = Query(None, description="Сортування ('title' або 'year')"),
    service: BookService = Depends(get_book_service)
):
    return await service.get_all_books(skip=skip, limit=limit, status=status, author=author, sort_by=sort_by)

@router.get("/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def get_book(
    book_id: UUID,
    service: BookService = Depends(get_book_service)
):
    return await service.get_book_by_id(book_id)

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    service: BookService = Depends(get_book_service)
):
    return await service.create_book(book)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    service: BookService = Depends(get_book_service)
):
    await service.delete_book(book_id)
