from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, unset_jwt_cookies, get_jwt
from models import db, User, Book, Borrow
from schemas import ma, UserSchema, BookSchema, BorrowSchema
from exceptions import BadRequest, NotFound, Conflict, Unauthorized
from utils import hash_password, verify_password, issue_tokens_response, issue_tokens_cookie_response

bp = Blueprint("api", __name__)
user_schema = UserSchema()
book_schema = BookSchema()
books_schema = BookSchema(many=True)
borrow_schema = BorrowSchema()
borrows_schema = BorrowSchema(many=True)

@bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise BadRequest("username and password are required")
    if User.query.filter_by(username=username).first():
        raise Conflict("username already exists")
    u = User(username=username, password_hash=hash_password(password))
    db.session.add(u)
    db.session.commit()
    return user_schema.jsonify(u), 201

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise BadRequest("username and password are required")
    u = User.query.filter_by(username=username).first()
    if not u or not verify_password(password, u.password_hash):
        raise Unauthorized("invalid credentials")
    claims = {"username": u.username}
    return issue_tokens_response(identity=u.id, additional_claims=claims)

@bp.route("/auth/login-cookie", methods=["POST"])
def login_cookie():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise BadRequest("username and password are required")
    u = User.query.filter_by(username=username).first()
    if not u or not verify_password(password, u.password_hash):
        raise Unauthorized("invalid credentials")
    claims = {"username": u.username}
    return issue_tokens_cookie_response(identity=u.id, additional_claims=claims)

@bp.route("/auth/logout-cookie", methods=["POST"])
def logout_cookie():
    from flask import jsonify, make_response
    resp = make_response(jsonify({"detail": "logged out"}))
    unset_jwt_cookies(resp)
    return resp

@bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = {"username": User.query.get(identity).username if identity else ""}
    token = create_access_token(identity=identity, additional_claims=claims)
    return jsonify({"access_token": token})

@bp.route("/books", methods=["GET"])
@jwt_required()
def list_books():
    q = Book.query.all()
    return books_schema.jsonify(q)

@bp.route("/books/<int:book_id>", methods=["GET"])
@jwt_required()
def get_book(book_id):
    b = Book.query.get(book_id)
    if not b:
        raise NotFound("book not found")
    return book_schema.jsonify(b)

@bp.route("/books", methods=["POST"])
@jwt_required()
def create_book():
    data = request.get_json(silent=True) or {}
    book_name = data.get("book_name")
    author = data.get("author")
    if not book_name or not author:
        raise BadRequest("book_name and author are required")
    b = Book(book_name=book_name, author=author, status="free")
    db.session.add(b)
    db.session.commit()
    return book_schema.jsonify(b), 201

@bp.route("/books/<int:book_id>", methods=["DELETE"])
@jwt_required()
def delete_book(book_id):
    b = Book.query.get(book_id)
    if not b:
        raise NotFound("book not found")
    if Borrow.query.filter_by(book_id=book_id, status="borrowed").first():
        raise Conflict("book currently borrowed")
    db.session.delete(b)
    db.session.commit()
    return jsonify({"detail": "deleted"})

@bp.route("/books/<int:book_id>/borrow", methods=["POST"])
@jwt_required()
def borrow_book(book_id):
    identity = get_jwt_identity()
    b = Book.query.get(book_id)
    if not b:
        raise NotFound("book not found")
    if b.status != "free":
        raise Conflict("book not available")
    bor = Borrow(user_id=identity, book_id=book_id, status="borrowed")
    b.status = "borrowed"
    db.session.add(bor)
    db.session.commit()
    return borrow_schema.jsonify(bor), 201

@bp.route("/books/<int:book_id>/return", methods=["POST"])
@jwt_required()
def return_book(book_id):
    identity = get_jwt_identity()
    bor = Borrow.query.filter_by(user_id=identity, book_id=book_id, status="borrowed").first()
    if not bor:
        raise NotFound("active borrow not found")
    b = Book.query.get(book_id)
    bor.status = "returned"
    bor.returned_at = datetime.utcnow()
    b.status = "free"
    db.session.commit()
    return borrow_schema.jsonify(bor)

@bp.route("/me/borrows", methods=["GET"])
@jwt_required()
def my_borrows():
    identity = get_jwt_identity()
    items = Borrow.query.filter_by(user_id=identity).order_by(Borrow.borrowed_at.desc()).all()
    return borrows_schema.jsonify(items)
