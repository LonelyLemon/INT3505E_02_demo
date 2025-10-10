from flask import Flask, request, jsonify, make_response, url_for

app = Flask(__name__)

# Sample data
BOOKS = [
    {"id": 1, "title": "1984", "author": "Orwell", "year": 1949, "category": "novel"},
    {"id": 2, "title": "Clean Code", "author": "Martin", "year": 2008, "category": "tech"},
]

USERS = [
    {"id": 1, "name": "Alice"},
]


def ok(data=None, meta=None, status=200, location: str | None = None):
    body = {"data": data, "meta": meta}
    resp = make_response(jsonify(body), status)

    if location:
        resp.headers["Location"] = location

    return resp

def fail(message: str, status=400):
    return make_response(jsonify({"error": {"code": status, "message": message}}), status)

ALLOWED_SORT = {"title", "year", "author"}


@app.get("/api/v1/books")
def list_books():
    author = request.args.get("author")
    category = request.args.get("category")
    min_year = request.args.get("min_year", type=int)
    sort = request.args.get("sort")

    data = BOOKS
    if author:
        data = [b for b in data if b.get("author") == author]
    if category:
        data = [b for b in data if b.get("category") == category]
    if min_year is not None:
        data = [b for b in data if b.get("year") and b["year"] >= min_year]

    if sort:
        if sort not in ALLOWED_SORT:
            return fail("sort must be one of: title, year, author", 400)
        data = sorted(data, key=lambda x: x.get(sort))

    return ok(data=data, meta={"count": len(data)})

@app.post("/api/v1/books")
def create_book():
    if not request.is_json:
        return fail("Content-Type must be application/json", 415)
    
    payload = request.get_json() or {}
    title = payload.get("title")
    author = payload.get("author")
    year = payload.get("year")
    category = payload.get("category")

    if not title or not author:
        return fail("title and author are required", 400)

    new_id = (max(b["id"] for b in BOOKS) + 1) if BOOKS else 1
    new = {"id": new_id, "title": title, "author": author, "year": year, "category": category}
    BOOKS.append(new)

    return ok(
        data=new,
        status=201,
        location=url_for("get_book", book_id=new_id)
    )

@app.get("/api/v1/books/<int:book_id>")
def get_book(book_id: int):
    for b in BOOKS:
        if b["id"] == book_id:
            return ok(data=b)
    return fail("Book not found", 404)

@app.put("/api/v1/books/<int:book_id>")
def update_book(book_id: int):
    if not request.is_json:
        return fail("Content-Type must be application/json", 415)
    
    payload = request.get_json() or {}
    title = payload.get("title")
    author = payload.get("author")
    year = payload.get("year")
    category = payload.get("category")

    if not title or not author:
        return fail("title and author are required", 400)

    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS[i] = {"id": book_id, "title": title, "author": author, "year": year, "category": category}
            return ok(data=BOOKS[i])

    return fail("Book not found", 404)

@app.delete("/api/v1/books/<int:book_id>")
def delete_book(book_id: int):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return ("", 204)
    return fail("Book not found", 404)

@app.get("/api/v1/users/<int:user_id>")
def get_user(user_id: int):
    for u in USERS:
        if u["id"] == user_id:
            return ok(data=u)
    return fail("User not found", 404)

if __name__ == "__main__":
    app.run(debug=True, port=8001)
