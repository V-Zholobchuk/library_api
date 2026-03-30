import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db, Base
from schemas.book import BookStatus

TEST_DATABASE_URL = "sqlite+aiosqlite://"
engine_test = create_async_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine_test, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

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
    # Додаємо 5 книг
    for i in range(5):
        await async_client.post("/books/", json={"title": f"Book {i}", "author": "Author", "year": 2000+i})
        
    # Skip=2, limit=2 
    resp = await async_client.get("/books/?skip=2&limit=2&sort_by=year")
    assert resp.status_code == 200
    data = resp.json()
    
    # Головне: ми маємо бачити `total` = 5, хоча повертається лише 2 елементи
    assert data["total"] == 5
    assert data["skip"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Book 2"
    assert data["items"][1]["title"] == "Book 3"
