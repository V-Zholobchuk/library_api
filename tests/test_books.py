import pytest
from uuid import uuid4
from pymongo import MongoClient

from main import app as flask_app
from database import get_db

@pytest.fixture(scope="session")
def mongo_client():
    client = MongoClient("mongodb://localhost:27017")
    yield client
    client.close()

@pytest.fixture(scope="session")
def test_db(mongo_client):
    return mongo_client["test_library_db"]

@pytest.fixture(scope="session", autouse=True)
def override_db(test_db):
    import api.resources
    api.resources.get_db = lambda: test_db
    yield

@pytest.fixture(autouse=True)
def prepare_db(test_db):
    test_db.books.delete_many({})
    yield

@pytest.fixture()
def client():
    flask_app.config.update({"TESTING": True})
    with flask_app.test_client() as client:
        yield client

def test_create_book(client):
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
    data = response.get_json()
    assert "id" in data
    assert data["title"] == "Кобзар"

def test_get_all_books(client):
    client.post("/books/", json={"title": "Test1", "author": "A1", "year": 2020})
    client.post("/books/", json={"title": "Test2", "author": "A2", "year": 2021})
    
    response = client.get("/books/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

def test_get_book_by_id(client):
    create_resp = client.post("/books/", json={"title": "Лісова пісня", "author": "Леся Українка", "year": 1911})
    book_id = create_resp.get_json()["id"]

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200

def test_get_book_not_found(client):
    random_id = str(uuid4())
    response = client.get(f"/books/{random_id}")
    assert response.status_code == 404

def test_delete_book(client):
    create_resp = client.post("/books/", json={"title": "Захар", "author": "Іван Франко", "year": 1883})
    book_id = create_resp.get_json()["id"]

    delete_resp = client.delete(f"/books/{book_id}")
    assert delete_resp.status_code == 204
    get_resp = client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404

def test_filter_and_sort_books(client):
    client.post("/books/", json={"title": "C", "author": "Author1", "status": "наявні в бібліотеці", "year": 2000})
    client.post("/books/", json={"title": "A", "author": "Author2", "status": "видані комусь", "year": 1990})
    client.post("/books/", json={"title": "B", "author": "Author1", "status": "наявні в бібліотеці", "year": 2010})

    resp = client.get("/books/?author=Author1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert all(b["author"] == "Author1" for b in data["items"])

    resp2 = client.get("/books/?status=видані комусь")
    assert resp2.status_code == 200
    assert resp2.get_json()["total"] == 1
    assert resp2.get_json()["items"][0]["title"] == "A"

    resp3 = client.get("/books/?sort_by=title")
    titles = [b["title"] for b in resp3.get_json()["items"]]
    assert titles == ["A", "B", "C"]

    resp4 = client.get("/books/?sort_by=year")
    years = [b["year"] for b in resp4.get_json()["items"]]
    assert years == [1990, 2000, 2010]

def test_pagination(client):
    for i in range(5):
        client.post("/books/", json={"title": f"Book {i}", "author": "Author", "year": 2000+i})
        
    resp = client.get("/books/?skip=2&limit=2&sort_by=year")
    assert resp.status_code == 200
    data = resp.get_json()
    
    assert data["total"] == 5
    assert data["skip"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Book 2"
    assert data["items"][1]["title"] == "Book 3"

def test_update_book(client):
    create_resp = client.post("/books/", json={"title": "Original", "author": "Author", "year": 2000})
    book_id = create_resp.get_json()["id"]
    
    patch_resp = client.patch(f"/books/{book_id}", json={"title": "Updated Title"})
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["title"] == "Updated Title"
    assert patch_resp.get_json()["author"] == "Author"

def test_search_and_desc_sort(client):
    client.post("/books/", json={"title": "Harry Potter", "author": "J.K. Rowling", "year": 1997})
    client.post("/books/", json={"title": "Lord of the Rings", "author": "J.R.R. Tolkien", "year": 1954})
    
    resp = client.get("/books/?search_query=harry")
    assert resp.status_code == 200
    assert len(resp.get_json()["items"]) == 1
    assert resp.get_json()["items"][0]["title"] == "Harry Potter"
    
    resp2 = client.get("/books/?sort_by=year&sort_desc=true")
    assert resp2.get_json()["items"][0]["year"] == 1997
