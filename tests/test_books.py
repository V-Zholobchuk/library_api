import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient

from main import app
from database import get_db

async def override_get_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client["test_library_db"]
    client.close()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await client["test_library_db"].books.delete_many({})
    yield

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_book(async_client: AsyncClient):
    response = await async_client.post(
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

@pytest.mark.asyncio
async def test_get_all_books(async_client: AsyncClient):
    await async_client.post("/books/", json={"title": "Test1", "author": "A1", "year": 2020})
    await async_client.post("/books/", json={"title": "Test2", "author": "A2", "year": 2021})
    
    response = await async_client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

@pytest.mark.asyncio
async def test_get_book_by_id(async_client: AsyncClient):
    create_resp = await async_client.post("/books/", json={"title": "Лісова пісня", "author": "Леся Українка", "year": 1911})
    book_id = create_resp.json()["id"]

    response = await async_client.get(f"/books/{book_id}")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_book_not_found(async_client: AsyncClient):
    random_id = str(uuid4())
    response = await async_client.get(f"/books/{random_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_book(async_client: AsyncClient):
    create_resp = await async_client.post("/books/", json={"title": "Захар", "author": "Іван Франко", "year": 1883})
    book_id = create_resp.json()["id"]

    delete_resp = await async_client.delete(f"/books/{book_id}")
    assert delete_resp.status_code == 204
    get_resp = await async_client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_filter_and_sort_books(async_client: AsyncClient):
    await async_client.post("/books/", json={"title": "C", "author": "Author1", "status": "наявні в бібліотеці", "year": 2000})
    await async_client.post("/books/", json={"title": "A", "author": "Author2", "status": "видані комусь", "year": 1990})
    await async_client.post("/books/", json={"title": "B", "author": "Author1", "status": "наявні в бібліотеці", "year": 2010})

    resp = await async_client.get("/books/?author=Author1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert all(b["author"] == "Author1" for b in data["items"])

    resp2 = await async_client.get("/books/?status=видані комусь")
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 1
    assert resp2.json()["items"][0]["title"] == "A"

    resp3 = await async_client.get("/books/?sort_by=title")
    titles = [b["title"] for b in resp3.json()["items"]]
    assert titles == ["A", "B", "C"]

    resp4 = await async_client.get("/books/?sort_by=year")
    years = [b["year"] for b in resp4.json()["items"]]
    assert years == [1990, 2000, 2010]

@pytest.mark.asyncio
async def test_pagination(async_client: AsyncClient):
    for i in range(5):
        await async_client.post("/books/", json={"title": f"Book {i}", "author": "Author", "year": 2000+i})
        
    resp = await async_client.get("/books/?skip=2&limit=2&sort_by=year")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["total"] == 5
    assert data["skip"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Book 2"
    assert data["items"][1]["title"] == "Book 3"


@pytest.mark.asyncio
async def test_update_book(async_client: AsyncClient):
    create_resp = await async_client.post("/books/", json={"title": "Original", "author": "Author", "year": 2000})
    book_id = create_resp.json()["id"]
    
    patch_resp = await async_client.patch(f"/books/{book_id}", json={"title": "Updated Title"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated Title"
    assert patch_resp.json()["author"] == "Author"

@pytest.mark.asyncio
async def test_search_and_desc_sort(async_client: AsyncClient):
    await async_client.post("/books/", json={"title": "Harry Potter", "author": "J.K. Rowling", "year": 1997})
    await async_client.post("/books/", json={"title": "Lord of the Rings", "author": "J.R.R. Tolkien", "year": 1954})
    
    # Search test
    resp = await async_client.get("/books/?search_query=harry")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["title"] == "Harry Potter"
    
    # Desc sort test
    resp2 = await async_client.get("/books/?sort_by=year&sort_desc=true")
    assert resp2.json()["items"][0]["year"] == 1997
