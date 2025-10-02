from fastapi import FastAPI
from typing import Optional

app = FastAPI(title="Week 3 - Sample")

BOOKS = [
    {"id": 1, "title": "1984", "author": "Orwell", "year": 1949, "category": "novel"},
    {"id": 2, "title": "Clean Code", "author": "Martin", "year": 2008, "category": "tech"},
]

USERS = [
    {"id": 1, "name": "Alice"},
]

@app.get("/getAllBooks")
def getAllBooks():
    return BOOKS

@app.post("/createBook")
def createBook(title: str, author: str):
    new = {"id": len(BOOKS) + 1, "title": title, "author": author}
    BOOKS.append(new)
    return {"message": "ok", "book": new}

@app.post("/updateBook/{id}")
def updateBook(id: int, title: Optional[str] = None, author: Optional[str] = None):
    for b in BOOKS:
        if b["id"] == id:
            if title:
                b["title"] = title
            if author:
                b["author"] = author
            return {"ok": True}
    return {"ok": False}

@app.get("/users")
def getUserById(id: int):
    for u in USERS:
        if u["id"] == id:
            return u
    return "not found"

@app.get("/getBooksByAuthor")
def getBooksByAuthor(a: str):
    return [b for b in BOOKS if b.get("author") == a]
