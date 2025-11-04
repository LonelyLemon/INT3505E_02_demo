from datetime import timedelta

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "aa5ed69bb54da657c749b17bf2910f9b"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {"id": self.id, "username": self.username}


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "book_name": self.book_name,
            "author": self.author,
            "created_by": self.created_by,
        }


@app.route("/users/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "username and password are required"}), 400

    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({"message": "username already exists"}), 409

    password_hash = generate_password_hash(password)
    user = User(username=username, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "user created", "user": user.to_dict()}), 201


@app.route("/users/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify(
        {
            "access_token": access_token,
            "user": user.to_dict(),
        }
    )


@app.route("/users/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "user not found"}), 404
    return jsonify(user.to_dict())


@app.route("/books", methods=["POST"])
@jwt_required()
def create_book():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    book_name = data.get("book_name")
    author = data.get("author")

    if not book_name or not author:
        return jsonify({"message": "book_name and author are required"}), 400

    book = Book(book_name=book_name, author=author, created_by=user_id)
    db.session.add(book)
    db.session.commit()

    return jsonify({"message": "book created", "book": book.to_dict()}), 201


@app.route("/books", methods=["GET"])
@jwt_required()
def list_books():
    books = Book.query.all()
    return jsonify([b.to_dict() for b in books])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
