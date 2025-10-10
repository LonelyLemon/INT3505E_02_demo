from flask import Flask, jsonify

app = Flask(__name__)

# Sample data
BOOKS = {
    1: {"id": 1, "title": "Clean Architecture", "author": "Robert C. Martin", "available": True},
    2: {"id": 2, "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "available": False},
}

# Helper
def success_response(data=None, message=None, status_code=200):
    return jsonify({"status": "success", "data": data, "message": message}), status_code

def list_books():
    return [BOOKS[i] for i in sorted(BOOKS)]

# V1: Client–Server
@app.get("/api/v1/books")
def v1_list_books():
    return success_response(list_books())

if __name__ == "__main__":
    app.run(debug=True, port=5001)
