from fastapi import FastAPI
from api.book import router as book_router

app = FastAPI(
    title="Library API",
    description="API для управління книгами у бібліотеці",
    version="1.0.0"
)

app.include_router(book_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to Library API! Go to /docs to see the Swagger UI."}
