from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from pymongo.database import Database
from schemas.book_schemas import BookStatus

class BookRepository:
    def __init__(self, db: Database):
        self.collection = db.books

    def get_all(
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
            
        total = self.collection.count_documents(query)
        cursor = self.collection.find(query, {"_id": 0})
        
        direction = -1 if sort_desc else 1
        
        if sort_by == 'title':
            cursor = cursor.sort("title", direction)
        elif sort_by == 'year':
            cursor = cursor.sort("year", direction)
        else:
            cursor = cursor.sort("id", direction)
            
        cursor = cursor.skip(skip).limit(limit)
        books = list(cursor)
        
        return total, books

    def get_by_id(self, book_id: UUID) -> Optional[dict]:
        return self.collection.find_one({"id": str(book_id)}, {"_id": 0})

    def create(self, book_data: dict) -> dict:
        book_data["id"] = str(uuid4())
        self.collection.insert_one(book_data.copy())
        return book_data

    def update(self, book_id: UUID, update_data: dict) -> Optional[dict]:
        if update_data:
            self.collection.update_one({"id": str(book_id)}, {"$set": update_data})
        return self.get_by_id(book_id)

    def delete(self, book_id: UUID) -> None:
        self.collection.delete_one({"id": str(book_id)})
