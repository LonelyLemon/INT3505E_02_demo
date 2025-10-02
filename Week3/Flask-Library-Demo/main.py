from flask import Flask, request, jsonify, abort, url_for

app = Flask(__name__)

BOOKS = {}
NEXT_ID = 1
VALID_STATUS = {"available", "borrowed"}

def json_error(status_code, message):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response

@app.errorhandler(404)
def not_found(e):
    return json_error(404, "Resource not found")

@app.errorhandler(400)
def bad_request(e):
    return json_error(400, "Bad request")

@app.errorhandler(415)
def unsupported_media(e):
    return json_error(415, "Unsupported media type")

def require_json():
    if not request.is_json:
        abort(415)

def get_book_or_404(book_id):
    book = BOOKS.get(book_id)
    if not book:
        abort(404)
    return book

@app.post("/books")
def create_book():
    global NEXT_ID
    require_json()
    data = request.get_json()
    title = data.get("title")
    author = data.get("author")
    status = data.get("status", "available")
    if not title or not author:
        abort(400)
    if status not in VALID_STATUS:
        abort(400)
    book = {"id": NEXT_ID, "title": title, "author": author, "status": status}
    BOOKS[NEXT_ID] = book
    NEXT_ID += 1
    resp = jsonify(book)
    resp.status_code = 201
    resp.headers["Location"] = url_for("get_book", book_id=book["id"])
    return resp

@app.get("/books")
def list_books():
    return jsonify(list(BOOKS.values()))

@app.get("/books/<int:book_id>")
def get_book(book_id):
    book = get_book_or_404(book_id)
    return jsonify(book)

@app.put("/books/<int:book_id>/status")
def update_status(book_id):
    require_json()
    data = request.get_json()
    status = data.get("status")
    if status not in VALID_STATUS:
        abort(400)
    book = get_book_or_404(book_id)
    book["status"] = status
    return jsonify(book)

@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    book = get_book_or_404(book_id)
    del BOOKS[book_id]
    return ("", 204)

if __name__ == "__main__":
    app.run(debug=True)
