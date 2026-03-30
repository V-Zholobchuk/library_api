import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

# Імпорт основного додатку та in-memory БД
from main import app
from models.book import books_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    # Очищення бази даних перед кожним тестом для ізоляції
    books_db.clear()

def test_create_book():
    response = client.post(
        "/books/",
        json={
            "title": "Кобзар",
            "author": "Тарас Шевченко",
            "description": "Збірка поетичних творів",
            "status": "наявні в бібліотеці",
            "year": 1840
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Кобзар"
    assert data["author"] == "Тарас Шевченко"
    assert data["status"] == "наявні в бібліотеці"
    assert data["year"] == 1840

def test_get_all_books():
    client.post("/books/", json={"title": "Test1", "author": "A1", "year": 2020})
    client.post("/books/", json={"title": "Test2", "author": "A2", "year": 2021})
    
    response = client.get("/books/")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_book_by_id():
    create_resp = client.post("/books/", json={"title": "Лісова пісня", "author": "Леся Українка", "year": 1911})
    book_id = create_resp.json()["id"]

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == "Лісова пісня"

def test_get_book_not_found():
    random_id = str(uuid4())
    response = client.get(f"/books/{random_id}")
    assert response.status_code == 404

def test_delete_book():
    create_resp = client.post("/books/", json={"title": "Захар Беркут", "author": "Іван Франко", "year": 1883})
    book_id = create_resp.json()["id"]

    # Delete book
    delete_resp = client.delete(f"/books/{book_id}")
    assert delete_resp.status_code == 204

    # GET endpoint should now return 404
    get_resp = client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404

    # Ідемпотентна операція: повторне видалення
    delete_again_resp = client.delete(f"/books/{book_id}")
    assert delete_again_resp.status_code == 204

def test_filter_and_sort_books():
    client.post("/books/", json={"title": "C", "author": "Author1", "status": "наявні в бібліотеці", "year": 2000})
    client.post("/books/", json={"title": "A", "author": "Author2", "status": "видані комусь", "year": 1990})
    client.post("/books/", json={"title": "B", "author": "Author1", "status": "наявні в бібліотеці", "year": 2010})

    # Фільтрація по автору
    resp = client.get("/books/?author=Author1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    assert all(b["author"] == "Author1" for b in resp.json())

    # Фільтрація по статусу
    resp2 = client.get("/books/?status=видані комусь")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["title"] == "A"

    # Сортування по title
    resp3 = client.get("/books/?sort_by=title")
    titles = [b["title"] for b in resp3.json()]
    assert titles == ["A", "B", "C"]

    # Сортування по year
    resp4 = client.get("/books/?sort_by=year")
    years = [b["year"] for b in resp4.json()]
    assert years == [1990, 2000, 2010]
