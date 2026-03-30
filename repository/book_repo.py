from typing import List, Optional, Tuple
from uuid import UUID
import base64
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from schemas.book_schemas import BookStatus
from models.book_model import Book

def encode_cursor(id: UUID, value: any) -> str:
    data = {"i": str(id), "v": value}
    return base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')

def decode_cursor(cursor: str) -> Optional[dict]:
    try:
        return json.loads(base64.b64decode(cursor.encode('utf-8')).decode('utf-8'))
    except Exception:
        return None

class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self, 
        limit: int = 100,
        cursor: Optional[str] = None,
        is_prev: bool = False,
        status: Optional[BookStatus] = None, 
        author: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Tuple[int, List[Book], Optional[str], Optional[str]]:
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
        cursor_data = decode_cursor(cursor) if cursor else None
        
        if sort_by == 'title':
            col = Book.title
        elif sort_by == 'year':
            col = Book.year
        else:
            col = Book.id
            
        if is_prev:
            if col is not Book.id:
                query = query.order_by(col.desc(), Book.id.desc())
                if cursor_data:
                    cursor_uuid = UUID(cursor_data['i'])
                    query = query.where(
                        (col < cursor_data['v']) | 
                        ((col == cursor_data['v']) & (Book.id < cursor_uuid))
                    )
            else:
                query = query.order_by(Book.id.desc())
                if cursor_data:
                    cursor_uuid = UUID(cursor_data['i'])
                    query = query.where(Book.id < cursor_uuid)
        else:
            if col is not Book.id:
                query = query.order_by(col.asc(), Book.id.asc())
                if cursor_data:
                    cursor_uuid = UUID(cursor_data['i'])
                    query = query.where(
                        (col > cursor_data['v']) | 
                        ((col == cursor_data['v']) & (Book.id > cursor_uuid))
                    )
            else:
                query = query.order_by(Book.id.asc())
                if cursor_data:
                    cursor_uuid = UUID(cursor_data['i'])
                    query = query.where(Book.id > cursor_uuid)

        query = query.limit(limit + 1)
        
        result = await self.session.execute(query)
        books = list(result.scalars().all())
        
        has_more = len(books) > limit
        if has_more:
            books.pop()
            
        if is_prev:
            books.reverse()
            
        next_cursor = None
        prev_cursor = None
        
        if len(books) > 0:
            first_book = books[0]
            last_book = books[-1]
            
            def make_cur(b: Book):
                if sort_by == 'title': v = b.title
                elif sort_by == 'year': v = b.year
                else: v = str(b.id)
                return encode_cursor(b.id, v)

            if is_prev:
                if has_more:
                    prev_cursor = make_cur(first_book)
                next_cursor = make_cur(last_book)
            else:
                if cursor:
                    prev_cursor = make_cur(first_book)
                if has_more:
                    next_cursor = make_cur(last_book)
                    
        return total, books, next_cursor, prev_cursor

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
