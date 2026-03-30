from typing import List, Dict, Optional
from uuid import UUID, uuid4
from schemas.book import BookStatus
from models.book import books_db

class BookRepository:
    def __init__(self):
        # Посилання на наше in-memory "сховище"
        self.books = books_db

    async def get_all(self, status: Optional[BookStatus] = None, author: Optional[str] = None) -> List[Dict]:
        result = self.books
        if status:
            result = [b for b in result if b["status"] == status]
        if author:
            result = [b for b in result if b["author"].lower() == author.lower()]
        return result

    async def get_by_id(self, book_id: UUID) -> Optional[Dict]:
        for book in self.books:
            if book["id"] == book_id:
                return book
        return None

    async def create(self, book_data: dict) -> dict:
        book_dict = book_data.copy()
        book_dict["id"] = uuid4()
        self.books.append(book_dict)
        return book_dict

    async def delete(self, book_id: UUID) -> None:
        # Модифікуємо список "на місці" (in-place), щоб зберегти посилання на `books_db`
        self.books[:] = [book for book in self.books if book["id"] != book_id]
