from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample data
BOOKS = [
    {"id": 1, "title": "1984", "author": "Orwell", "year": 1949, "category": "novel"},
    {"id": 2, "title": "Clean Code", "author": "Martin", "year": 2008, "category": "tech"},
]
USERS = [
    {"id": 1, "name": "Alice"},
]

# Không có versioning
# Vi phạm naming khi sử dụng động từ 

@app.get("/getAllBooks")
def getAllBooks():
    # Return dictionary thẳng, không có schema rõ ràng
    return jsonify(BOOKS)

@app.post("/createBook")
def createBook():
    # Không xác thực schema rõ ràng cho các dữ liệu đầu vào.
    title = request.args.get("title") or request.form.get("title")
    author = request.args.get("author") or request.form.get("author")

    new = {"id": len(BOOKS) + 1, "title": title, "author": author}
    BOOKS.append(new)

    # Response không đồng nhất giữa các route
    return jsonify({"message": "ok", "book": new})

@app.post("/updateBook/<int:id>")
def updateBook(id: int):
    # Dùng sai HTTP method để update(POST thay vì PUT)
    title = request.args.get("title") or request.form.get("title")
    author = request.args.get("author") or request.form.get("author")

    for b in BOOKS:
        if b["id"] == id:
            if title:
                b["title"] = title
            if author:
                b["author"] = author
            # Return kết quả không đồng nhất
            return jsonify({"ok": True})

    # Return kết quả không đồng nhất
    return jsonify({"ok": False})

@app.get("/users")
def getUserById():
    # Return value không rõ ràng
    # Không định nghĩa rõ http error 404 not found
    user_id = request.args.get("id", type=int)
    for u in USERS:
        if u["id"] == user_id:
            return jsonify(u)
    return "not found"

@app.get("/getBooksByAuthor")
def getBooksByAuthor():
    # Tham số a có tên mơ hồ, không rõ ràng
    a = request.args.get("a")
    return jsonify([b for b in BOOKS if b.get("author") == a])

if __name__ == "__main__":
    app.run(debug=True, port=8001)
