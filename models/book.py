import uuid
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum, String, Integer, Uuid
from database import Base
from schemas.book import BookStatus

class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[BookStatus] = mapped_column(SQLEnum(BookStatus), default=BookStatus.AVAILABLE, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
