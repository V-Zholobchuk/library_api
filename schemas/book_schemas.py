from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from enum import Enum
from uuid import UUID

class BookStatus(str, Enum):
    AVAILABLE = "наявні в бібліотеці"
    ISSUED = "видані комусь"

class BookBase(BaseModel):
    title: str = Field(..., description="Назва книги", min_length=1)
    author: str = Field(..., description="Автор книги", min_length=1)
    description: Optional[str] = Field(None, description="Опис книги")
    status: BookStatus = Field(default=BookStatus.AVAILABLE, description="Статус книги")
    year: int = Field(..., description="Рік випуску", gt=0)

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class PaginatedBookResponse(BaseModel):
    total: int = Field(..., description="Загальна кількість книг, що відповідають запиту")
    skip: int
    limit: int
    next_url: Optional[str] = Field(None, description="URL наступної сторінки")
    prev_url: Optional[str] = Field(None, description="URL попередньої сторінки")
    items: List[BookResponse]
