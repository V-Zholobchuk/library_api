import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient

from main import app
from database import get_db
from unittest.mock import AsyncMock, patch

class MockRedis:
    def __init__(self):
        self.data = {}
    async def zremrangebyscore(self, key, min, max):
        if key in self.data:
            self.data[key] = {k: v for k, v in self.data[key].items() if v > max}
    async def zcard(self, key):
        return len(self.data.get(key, {}))
    async def zadd(self, key, mapping):
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(mapping)
    async def expire(self, key, time):
        pass
    async def flushdb(self):
        self.data = {}
        
mock_redis_client = MockRedis()

async def override_get_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client["test_library_db"]
    client.close()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await client["test_library_db"].books.delete_many({})
    await client["test_library_db"].users.delete_many({})
    with patch("rate_limiter.redis_client", mock_redis_client):
        await mock_redis_client.flushdb()
        yield
    client.close()

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient):
    await async_client.post("/auth/register", json={"username": "testuser", "password": "testpassword"})
    resp = await async_client.post("/auth/login", data={"username": "testuser", "password": "testpassword"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_book(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.post(
        "/books/",
        json={
            "title": "Кобзар",
            "author": "Тарас Шевченко",
            "description": "Збірка поетичних творів",
            "status": "наявні в бібліотеці",
            "year": 1840
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Кобзар"

@pytest.mark.asyncio
async def test_get_all_books(async_client: AsyncClient, auth_headers: dict):
    await async_client.post("/books/", json={"title": "Test1", "author": "A1", "year": 2020}, headers=auth_headers)
    await async_client.post("/books/", json={"title": "Test2", "author": "A2", "year": 2021}, headers=auth_headers)
    
    response = await async_client.get("/books/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

@pytest.mark.asyncio
async def test_get_book_by_id(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post("/books/", json={"title": "Лісова пісня", "author": "Леся Українка", "year": 1911}, headers=auth_headers)
    book_id = create_resp.json()["id"]

    response = await async_client.get(f"/books/{book_id}", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_book_not_found(async_client: AsyncClient, auth_headers: dict):
    random_id = str(uuid4())
    response = await async_client.get(f"/books/{random_id}", headers=auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_book(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post("/books/", json={"title": "Захар", "author": "Іван Франко", "year": 1883}, headers=auth_headers)
    book_id = create_resp.json()["id"]

    delete_resp = await async_client.delete(f"/books/{book_id}", headers=auth_headers)
    assert delete_resp.status_code == 204
    get_resp = await async_client.get(f"/books/{book_id}", headers=auth_headers)
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_filter_and_sort_books(async_client: AsyncClient, auth_headers: dict):
    await async_client.post("/books/", json={"title": "C", "author": "Author1", "status": "наявні в бібліотеці", "year": 2000}, headers=auth_headers)
    await async_client.post("/books/", json={"title": "A", "author": "Author2", "status": "видані комусь", "year": 1990}, headers=auth_headers)
    await async_client.post("/books/", json={"title": "B", "author": "Author1", "status": "наявні в бібліотеці", "year": 2010}, headers=auth_headers)

    resp = await async_client.get("/books/?author=Author1", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    resp2 = await async_client.get("/books/?status=видані комусь", headers=auth_headers)
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 1
    assert resp2.json()["items"][0]["title"] == "A"

    resp3 = await async_client.get("/books/?sort_by=title", headers=auth_headers)
    titles = [b["title"] for b in resp3.json()["items"]]
    assert titles == ["A", "B", "C"]

    resp4 = await async_client.get("/books/?sort_by=year", headers=auth_headers)
    years = [b["year"] for b in resp4.json()["items"]]
    assert years == [1990, 2000, 2010]

@pytest.mark.asyncio
async def test_pagination(async_client: AsyncClient, auth_headers: dict):
    for i in range(5):
        await async_client.post("/books/", json={"title": f"Book {i}", "author": "Author", "year": 2000+i}, headers=auth_headers)
        
    resp = await async_client.get("/books/?skip=2&limit=2&sort_by=year", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["total"] == 5
    assert data["skip"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Book 2"
    assert data["items"][1]["title"] == "Book 3"

@pytest.mark.asyncio
async def test_update_book(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post("/books/", json={"title": "Original", "author": "Author", "year": 2000}, headers=auth_headers)
    book_id = create_resp.json()["id"]
    
    patch_resp = await async_client.patch(f"/books/{book_id}", json={"title": "Updated Title"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated Title"
    assert patch_resp.json()["author"] == "Author"

@pytest.mark.asyncio
async def test_search_and_desc_sort(async_client: AsyncClient, auth_headers: dict):
    await async_client.post("/books/", json={"title": "Harry Potter", "author": "J.K. Rowling", "year": 1997}, headers=auth_headers)
    await async_client.post("/books/", json={"title": "Lord of the Rings", "author": "J.R.R. Tolkien", "year": 1954}, headers=auth_headers)
    
    resp = await async_client.get("/books/?search_query=harry", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["title"] == "Harry Potter"
    resp2 = await async_client.get("/books/?sort_by=year&sort_desc=true", headers=auth_headers)
    assert resp2.json()["items"][0]["year"] == 1997

@pytest.mark.asyncio
async def test_rate_limit_anonymous(async_client: AsyncClient):
    resp1 = await async_client.get("/books/")
    assert resp1.status_code == 200
    
    resp2 = await async_client.get("/books/")
    assert resp2.status_code == 200
    
    resp3 = await async_client.get("/books/")
    assert resp3.status_code == 429

@pytest.mark.asyncio
async def test_rate_limit_authenticated(async_client: AsyncClient, auth_headers: dict):
    for _ in range(10):
        resp = await async_client.get("/books/", headers=auth_headers)
        assert resp.status_code == 200
        
    resp_limit = await async_client.get("/books/", headers=auth_headers)
    assert resp_limit.status_code == 429
