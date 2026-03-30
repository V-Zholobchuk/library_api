from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.book_schemas import BookStatus

class BookRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.books

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[BookStatus] = None, 
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        search_query: Optional[str] = None
    ) -> Tuple[int, List[dict]]:
        query = {}
        if status:
            query["status"] = status
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
            
        if search_query:
            query["$or"] = [
                {"title": {"$regex": search_query, "$options": "i"}},
                {"author": {"$regex": search_query, "$options": "i"}}
            ]
            
        total = await self.collection.count_documents(query)
        
        cursor = self.collection.find(query)
        
        direction = -1 if sort_desc else 1
        
        if sort_by == 'title':
            cursor = cursor.sort("title", direction)
        elif sort_by == 'year':
            cursor = cursor.sort("year", direction)
        else:
            cursor = cursor.sort("id", direction)
            
        cursor = cursor.skip(skip).limit(limit)
        books = await cursor.to_list(length=limit)
        
        return total, books

    async def get_by_id(self, book_id: UUID) -> Optional[dict]:
        return await self.collection.find_one({"id": str(book_id)})

    async def create(self, book_data: dict) -> dict:
        book_data["id"] = str(uuid4())
        await self.collection.insert_one(book_data)
        return book_data

    async def update(self, book_id: UUID, update_data: dict) -> Optional[dict]:
        if update_data:
            await self.collection.update_one({"id": str(book_id)}, {"$set": update_data})
        return await self.get_by_id(book_id)

    async def delete(self, book_id: UUID) -> None:
        await self.collection.delete_one({"id": str(book_id)})
