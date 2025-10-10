# app.py
from flask import Flask, request, jsonify, make_response, Response
import hashlib, json

app = Flask(__name__)

# ================== #
# - Sample Data       
# ================== #

BOOKS = {
    1: {"id": 1, "title": "Clean Architecture", "author": "Robert C. Martin", "available": True},
    2: {"id": 2, "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "available": False},
}
NEXT_ID = 3

# ================== #
# - Helper functions
# ================== #
def success_response(data=None, message=None, status_code=200):
    return jsonify({"status": "success", "data": data, "message": message}), status_code

def error_response(message, status_code=400):
    return jsonify({"status": "error", "data": None, "message": message}), status_code

def require_json():
    return request.is_json

def etag_for(obj) -> str:
    body = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()

def cacheable_json(data, max_age=60):
    tag = etag_for({"status":"success","data":data,"message":None})
    inm = request.headers.get("If-None-Match")

    if inm and inm == tag:
        resp = make_response("", 304)
        resp.headers["ETag"] = tag
        resp.headers["Cache-Control"] = f"public, max-age={max_age}"
        return resp
    
    resp = make_response(json.dumps({"status":"success","data":data,"message":None}))
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    resp.headers["ETag"] = tag
    resp.headers["Cache-Control"] = f"public, max-age={max_age}"

    return resp

def list_books():
    return [BOOKS[i] for i in sorted(BOOKS)]

def get_book_or_404(book_id: int):
    b = BOOKS.get(book_id)

    if not b:
        return None
    
    return b

# ================== #
# - V1: Client - Server
# ================== #
@app.get("/api/v1/books")
def v1_list_books():
    return success_response(list_books())

# ================== #
# - V2: Uniform Interface
# ================== #
@app.get("/api/v2/books")
def v2_list_books():
    return success_response(list_books())

@app.get("/api/v2/books/<int:book_id>")
def v2_get_book(book_id: int):
    b = get_book_or_404(book_id)

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
    created = BOOKS[NEXT_ID]
    NEXT_ID += 1

    resp = jsonify({"status":"success","data":created,"message":"Book created"})
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v2/books/{created['id']}"

    return resp

# ================== #
# - V3: Stateless
# ================== #
REQUIRED_TOKEN = "demo-token"
def require_bearer():
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return error_response("Missing Bearer token", 401)
    
    token = auth.split(" ", 1)[1].strip()

    if token != REQUIRED_TOKEN:
        return error_response("Invalid token", 403)
    
    return None

@app.get("/api/v3/books")
def v3_list_books():
    err = require_bearer()

    if err: 
        return err
    
    return success_response(list_books())

@app.post("/api/v3/books")
def v3_create_book():
    global NEXT_ID

    err = require_bearer()

    if err: 
        return err
    if not require_json():
        return error_response("Content-Type must be application/json", 415)
    
    data = request.get_json() or {}

    if not data.get("title") or not data.get("author"):
        return error_response("Missing title or author", 400)
    
    BOOKS[NEXT_ID] = {"id": NEXT_ID, "title": data["title"], "author": data["author"], "available": True}
    created = BOOKS[NEXT_ID]
    NEXT_ID += 1

    return success_response(created, "Book created", 201)

# ================== #
# - V4: Cacheable
# ================== #
@app.get("/api/v4/books")
def v4_list_books():
    return cacheable_json(list_books(), max_age=120)

@app.get("/api/v4/books/<int:book_id>")
def v4_get_book(book_id: int):
    b = get_book_or_404(book_id)

    if not b:
        return error_response("Book not found", 404)
    
    return cacheable_json(b, max_age=180)

# ================== #
# - V5: Code on demand
# ================== #
@app.get("/api/v5/page")
def v5_page():
    html = """
<!doctype html><meta charset="utf-8"><title>v5 Code on Demand</title>
<body>
  <div id="app"></div>
  <script>document.getElementById('app').innerText='Book Management';</script>
</body>
"""
    return Response(html, mimetype="text/html")

@app.get("/api/v5/books")
def v5_list_books():
    return success_response(list_books())

if __name__ == "__main__":
    app.run(debug=True, port=5001)
