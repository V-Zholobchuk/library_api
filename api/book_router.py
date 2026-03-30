from fastapi import APIRouter, Depends, status, Query, Request
from typing import List, Optional
from uuid import UUID

from schemas.book_schemas import BookCreate, BookResponse, BookStatus, PaginatedBookResponse
from services.book_service import BookService
from repository.book_repo import BookRepository
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/books", tags=["Books"])

def get_book_service(db: AsyncSession = Depends(get_db)) -> BookService:
    repository = BookRepository(db)
    return BookService(repository)

@router.get("/", response_model=PaginatedBookResponse, status_code=status.HTTP_200_OK)
async def get_books(
    request: Request,
    cursor: Optional[str] = Query(None, description="Курсор для пагінації (base64)"),
    limit: int = Query(10, ge=1, le=100, description="Пагінація: limit "),
    status: Optional[BookStatus] = Query(None, description="Фільтр по статусу"),
    author: Optional[str] = Query(None, description="Фільтр по автору"),
    sort_by: Optional[str] = Query(None, description="Сортування ('title' або 'year')"),
    service: BookService = Depends(get_book_service)
):
    result = await service.get_all_books(limit=limit, cursor=cursor, status=status, author=author, sort_by=sort_by)
    
    if result.next_cursor:
        result.next_url = str(request.url.include_query_params(cursor=result.next_cursor, limit=limit))
        
    return result

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
