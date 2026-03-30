from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from schemas.book_schemas import BookStatus
from models.book_model import Book

class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[BookStatus] = None, 
        author: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Tuple[int, List[Book]]:
        base_query = select(Book)
        
        if status:
            base_query = base_query.where(Book.status == status)
        if author:
            base_query = base_query.where(Book.author == author)
            
        count_query = select(func.count(Book.id))
        if status:
            count_query = count_query.where(Book.status == status)
        if author:
            count_query = count_query.where(Book.author == author)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        query = base_query
        if sort_by == 'title':
            query = query.order_by(Book.title)
        elif sort_by == 'year':
            query = query.order_by(Book.year)
            
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return total, list(result.scalars().all())

    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        return await self.session.get(Book, book_id)

    async def create(self, book_data: dict) -> Book:
        book = Book(**book_data)
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: UUID) -> None:
        query = delete(Book).where(Book.id == book_id)
        await self.session.execute(query)
        await self.session.commit()
