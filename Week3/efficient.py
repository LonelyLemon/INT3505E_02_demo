from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Week 3 - Sample")

class BookCreate(BaseModel):
    title: str
    author: str
    year: Optional[int] = None
    category: Optional[str] = None

BOOKS = [
    {"id": 1, "title": "1984", "author": "Orwell", "year": 1949, "category": "novel"},
    {"id": 2, "title": "Clean Code", "author": "Martin", "year": 2008, "category": "tech"},
]

USERS = [
    {"id": 1, "name": "Alice"},
]

@app.get("/api/v1/books")
def list_books(
    author: Optional[str] = None,
    category: Optional[str] = None,
    min_year: Optional[int] = None,
    sort: Optional[str] = Query(default=None, pattern="^(title|year|author)$")
):
    data = BOOKS
    if author:
        data = [b for b in data if b.get("author") == author]
    if category:
        data = [b for b in data if b.get("category") == category]
    if min_year is not None:
        data = [b for b in data if b.get("year") and b["year"] >= min_year]
    if sort:
        data = sorted(data, key=lambda x: x.get(sort))
    return {"data": data, "meta": {"count": len(data)}}

@app.post("/api/v1/books", status_code=201)
def create_book(payload: BookCreate):
    new = {"id": len(BOOKS) + 1, **payload.model_dump()}
    BOOKS.append(new)
    return {"data": new}

@app.get("/api/v1/books/{book_id}")
def get_book(book_id: int):
    for b in BOOKS:
        if b["id"] == book_id:
            return {"data": b}
    raise HTTPException(status_code=404, detail="Book not found")

@app.put("/api/v1/books/{book_id}")
def update_book(book_id: int, payload: BookCreate):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS[i] = {"id": book_id, **payload.model_dump()}
            return {"data": BOOKS[i]}
    raise HTTPException(status_code=404, detail="Book not found")

@app.delete("/api/v1/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return
    raise HTTPException(status_code=404, detail="Book not found")

@app.get("/api/v1/users/{user_id}")
def get_user(user_id: int):
    for u in USERS:
        if u["id"] == user_id:
            return {"data": u}
    raise HTTPException(status_code=404, detail="User not found")
