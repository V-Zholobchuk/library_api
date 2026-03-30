from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import engine, Base
from api.book import router as book_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Library API",
    lifespan=lifespan
)

app.include_router(book_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to Library API! Go to /docs to see the Swagger UI."}
