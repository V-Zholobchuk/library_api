from typing import List, Optional
from uuid import UUID
from repository.book_repo import BookRepository
from schemas.book_schemas import BookCreate, BookUpdate, BookResponse, BookStatus, PaginatedBookResponse

class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    def get_all_books(
        self, 
        skip: int = 0,
        limit: int = 10,
        status: Optional[BookStatus] = None, 
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        search_query: Optional[str] = None
    ) -> PaginatedBookResponse:
        total, books = self.repository.get_all(
            skip=skip, 
            limit=limit, 
            status=status, 
            author=author,
            sort_by=sort_by,
            sort_desc=sort_desc,
            search_query=search_query
        )
        return PaginatedBookResponse(
            total=total,
            skip=skip,
            limit=limit,
            next_url=None,
            prev_url=None,
            items=[BookResponse.model_validate(book) for book in books]
        )

    def get_book_by_id(self, book_id: UUID) -> Optional[BookResponse]:
        book_data = self.repository.get_by_id(book_id)
        if not book_data:
            return None
        return BookResponse.model_validate(book_data)

    def create_book(self, book: BookCreate) -> BookResponse:
        book_dict = book.model_dump()
        created_book = self.repository.create(book_dict)
        return BookResponse.model_validate(created_book)

    def update_book(self, book_id: UUID, book_update: BookUpdate) -> Optional[BookResponse]:
        update_data = book_update.model_dump(exclude_unset=True)
        updated_book = self.repository.update(book_id, update_data)
        if not updated_book:
            return None
        return BookResponse.model_validate(updated_book)

    def delete_book(self, book_id: UUID) -> None:
        self.repository.delete(book_id)
