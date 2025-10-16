from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    borrows = relationship("BorrowRequest", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "username": self.username}

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    author = Column(String(200), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="free", index=True)
    borrows = relationship("BorrowRequest", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "author": self.author, "status": self.status}

class BorrowRequest(Base):
    __tablename__ = "borrow_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    status = Column(String(20), nullable=False, default="created", index=True)
    user = relationship("User", back_populates="borrows")
    book = relationship("Book", back_populates="borrows")

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "book_id": self.book_id, "status": self.status}
