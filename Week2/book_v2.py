from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample data
BOOKS = {
    1: {"id": 1, "title": "Clean Architecture", "author": "Robert C. Martin", "available": True},
    2: {"id": 2, "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "available": False},
}
NEXT_ID = 3

# Helpers
def success_response(data=None, message=None, status_code=200):
    return jsonify({"status": "success", "data": data, "message": message}), status_code

def error_response(message, status_code=400):
    return jsonify({"status": "error", "data": None, "message": message}), status_code

def require_json():
    return request.is_json

def list_books():
    return [BOOKS[i] for i in sorted(BOOKS)]

def get_book_or_none(book_id: int):
    return BOOKS.get(book_id)

# V2: Uniform Interface
@app.get("/api/v2/books")
def v2_list_books():
    return success_response(list_books())

@app.get("/api/v2/books/<int:book_id>")
def v2_get_book(book_id: int):
    b = get_book_or_none(book_id)

    if not b:
        return error_response("Book not found", 404)
    
    return success_response(b)

@app.post("/api/v2/books")
def v2_create_book():
    global NEXT_ID

    if not require_json():
        return error_response("Content-Type must be application/json", 415)
    
    data = request.get_json() or {}

    if not data.get("title") or not data.get("author"):
        return error_response("Missing title or author", 400)

    BOOKS[NEXT_ID] = {"id": NEXT_ID, "title": data["title"], "author": data["author"], "available": True}
    created = BOOKS[NEXT_ID]; NEXT_ID += 1

    resp = jsonify({"status": "success", "data": created, "message": "Book created"})
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v2/books/{created['id']}"
    
    return resp

if __name__ == "__main__":
    app.run(debug=True, port=5001)
