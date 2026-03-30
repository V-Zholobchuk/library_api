from fastapi import FastAPI
from api.book_router import router as book_router

app = FastAPI(title="Library API")
app.include_router(book_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to Library API (MongoDB Edition)! Go to /docs to see the Swagger UI."}
