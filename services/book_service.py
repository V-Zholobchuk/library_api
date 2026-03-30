from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from repository.book_repo import BookRepository
from schemas.book_schemas import BookCreate, BookResponse, BookStatus, PaginatedBookResponse

class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def get_all_books(
        self, 
        limit: int = 10,
        cursor: Optional[str] = None,
        status: Optional[BookStatus] = None, 
        author: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> PaginatedBookResponse:
        total, books, next_cursor = await self.repository.get_all(
            limit=limit, 
            cursor=cursor,
            status=status, 
            author=author,
            sort_by=sort_by
        )
        items = [BookResponse.model_validate(book) for book in books]
        return PaginatedBookResponse(
            total=total,
            limit=limit,
            next_cursor=next_cursor,
            items=items
        )

    async def get_book_by_id(self, book_id: UUID) -> BookResponse:
        book_data = await self.repository.get_by_id(book_id)
        if not book_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книгу не знайдено")
        return BookResponse.model_validate(book_data)

    async def create_book(self, book: BookCreate) -> BookResponse:
        book_dict = book.model_dump()
        created_book = await self.repository.create(book_dict)
        return BookResponse.model_validate(created_book)

    async def delete_book(self, book_id: UUID) -> None:
        await self.repository.delete(book_id)
