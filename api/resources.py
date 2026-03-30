from flask import request
from flask_restful import Resource
from pydantic import ValidationError
from uuid import UUID
import urllib.parse

from schemas.book_schemas import BookCreate, BookUpdate, BookStatus
from services.book_service import BookService
from repository.book_repo import BookRepository
from database import get_db

def get_service() -> BookService:
    db = get_db()
    repo = BookRepository(db)
    return BookService(repo)

class BookListResource(Resource):
    def get(self):
        """
        Отримати всі книги з пагінацією
        ---
        tags:
          - Books
        parameters:
          - in: query
            name: skip
            type: integer
            default: 0
            description: Offset для пагінації
          - in: query
            name: limit
            type: integer
            default: 10
            description: Кількість елементів
          - in: query
            name: author
            type: string
            description: Пошук по автору
          - in: query
            name: search_query
            type: string
            description: Нечіткий пошук в назві та авторі
        responses:
          200:
            description: Сповіщена структура пагінації
        """
        service = get_service()
        
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=10, type=int)
        author = request.args.get('author')
        
        status_val = request.args.get('status')
        status = None
        if status_val in [s.value for s in BookStatus]:
            status = BookStatus(status_val)
            
        sort_by = request.args.get('sort_by')
        sort_desc = request.args.get('sort_desc', default='false').lower() == 'true'
        search_query = request.args.get('search_query')

        paginated = service.get_all_books(
            skip=skip, limit=limit, status=status, author=author, 
            sort_by=sort_by, sort_desc=sort_desc, search_query=search_query
        )
        
        base_url = request.base_url
        args = request.args.to_dict()
        
        if skip > 0:
            prev_skip = max(0, skip - limit)
            args['skip'] = prev_skip
            paginated.prev_url = f"{base_url}?{urllib.parse.urlencode(args)}"
            
        if skip + limit < paginated.total:
            next_skip = skip + limit
            args['skip'] = next_skip
            paginated.next_url = f"{base_url}?{urllib.parse.urlencode(args)}"

        return paginated.model_dump(mode='json'), 200

    def post(self):
        """
        Створити книгу
        ---
        tags:
          - Books
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                  example: Harry Potter
                author:
                  type: string
                  example: J.K. Rowling
                year:
                  type: integer
                  example: 1997
        responses:
          201:
            description: Книга створена
          422:
            description: Помилка валідації
        """
        service = get_service()
        try:
            req_data = request.get_json() or {}
            book_create = BookCreate(**req_data)
        except ValidationError as e:
            return e.errors(), 422
            
        book = service.create_book(book_create)
        return book.model_dump(mode='json'), 201

class BookResource(Resource):
    def get(self, book_id):
        """
        Отримати книгу по ID
        ---
        tags:
          - Books
        parameters:
          - in: path
            name: book_id
            type: string
            required: true
        responses:
          200:
            description: Об'єкт книги
          404:
            description: Not found
        """
        service = get_service()
        try:
            uid = UUID(book_id)
        except ValueError:
            return {"detail": "Invalid UUID format"}, 400
            
        book = service.get_book_by_id(uid)
        if not book:
            return {"detail": "Книгу не знайдено"}, 404
        return book.model_dump(mode='json'), 200

    def patch(self, book_id):
        """
        Часткове оновлення книги
        ---
        tags:
          - Books
        parameters:
          - in: path
            name: book_id
            type: string
            required: true
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                author:
                  type: string
                status:
                  type: string
        responses:
          200:
            description: Книга оновлена
        """
        service = get_service()
        try:
            uid = UUID(book_id)
        except ValueError:
            return {"detail": "Invalid UUID format"}, 400
            
        try:
            req_data = request.get_json() or {}
            update_data = BookUpdate(**req_data)
        except ValidationError as e:
            return e.errors(), 422
            
        book = service.update_book(uid, update_data)
        if not book:
            return {"detail": "Книгу не знайдено"}, 404
        return book.model_dump(mode='json'), 200

    def delete(self, book_id):
        """
        Видалення книги
        ---
        tags:
          - Books
        parameters:
          - in: path
            name: book_id
            type: string
            required: true
        responses:
          204:
            description: Успіх
        """
        service = get_service()
        try:
            uid = UUID(book_id)
        except ValueError:
            return {"detail": "Invalid UUID format"}, 400
            
        service.delete_book(uid)
        return '', 204
