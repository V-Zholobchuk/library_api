from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from repository.book import BookRepository
from schemas.book import BookCreate, BookResponse, BookStatus

class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def get_all_books(
        self, 
        status: Optional[BookStatus] = None, 
        author: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[BookResponse]:
        books_data = await self.repository.get_all(status=status, author=author)
        
        # Сортування
        if sort_by == 'title':
            books_data.sort(key=lambda x: x["title"])
        elif sort_by == 'year':
            books_data.sort(key=lambda x: x["year"].__int__())
            
        return [BookResponse(**book) for book in books_data]

    async def get_book_by_id(self, book_id: UUID) -> BookResponse:
        book_data = await self.repository.get_by_id(book_id)
        if not book_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книгу не знайдено")
        return BookResponse(**book_data)

    async def create_book(self, book: BookCreate) -> BookResponse:
        book_dict = book.model_dump()
        created_book = await self.repository.create(book_dict)
        return BookResponse(**created_book)

    async def delete_book(self, book_id: UUID) -> None:
        # Виклик репозиторію; ідемпотентно: помилку не викидаємо, якщо книги вже немає
        await self.repository.delete(book_id)
