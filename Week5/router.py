from flask import Blueprint, jsonify, request
from sqlalchemy import select
from config import SessionLocal
from models import User, Book, BorrowRequest
from schemas import UserCreateSchema, UserUpdateSchema, BookCreateSchema, BookUpdateSchema, BorrowCreateSchema
from exceptions import NotFoundError, BadRequestError, ConflictError
from utils import get_json_or_400, paginate_query_offset_limit, parse_offset_limit

api = Blueprint("api", __name__)


#----- Error Handling -----
@api.errorhandler(NotFoundError)
def handle_not_found(e):
    return jsonify({"error": e.message}), e.status_code

@api.errorhandler(BadRequestError)
def handle_bad_request(e):
    return jsonify({"error": e.message}), e.status_code

@api.errorhandler(ConflictError)
def handle_conflict(e):
    return jsonify({"error": e.message}), e.status_code

@api.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400

def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#----- User section -----
@api.post("/users")
def create_user():
    data = get_json_or_400()
    try:
        payload = UserCreateSchema(**data)
    except TypeError:
        raise BadRequestError("username and password are required")
    with next(db_session()) as db:
        if db.scalar(select(User).where(User.username == payload.username)):
            raise ConflictError("Username already exists")
        user = User(username=payload.username, password=payload.password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return jsonify(user.to_dict()), 201

@api.get("/users/<int:user_id>")
def get_user(user_id: int):
    with next(db_session()) as db:
        user = db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        return jsonify(user.to_dict())

@api.put("/users/<int:user_id>")
def update_user(user_id: int):
    data = get_json_or_400()
    try:
        payload = UserUpdateSchema(**data)
    except TypeError:
        raise BadRequestError("Invalid fields")
    with next(db_session()) as db:
        user = db.get(User, user_id)

        if not user:
            raise NotFoundError("User not found")
        
        if payload.username is not None:
            if db.scalar(select(User).where(User.username == payload.username, User.id != user_id)):
                raise ConflictError("Username already exists")
            user.username = payload.username

        if payload.password is not None:
            user.password = payload.password
            
        db.commit()
        db.refresh(user)
        return jsonify(user.to_dict())

@api.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    with next(db_session()) as db:
        user = db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        db.delete(user)
        db.commit()
        return jsonify({"deleted": True})

@api.post("/books")
def create_book():
    data = get_json_or_400()
    try:
        payload = BookCreateSchema(**data)
    except TypeError:
        raise BadRequestError("name and author are required")
    status = payload.status if payload.status in {"free", "borrowed", None} else None
    if status is None:
        status = "free"
    with next(db_session()) as db:
        book = Book(name=payload.name, author=payload.author, status=status)
        db.add(book)
        db.commit()
        db.refresh(book)
        return jsonify(book.to_dict()), 201

@api.get("/books")
def list_books():
    offset, limit = parse_offset_limit()
    with next(db_session()) as db:
        query = db.query(Book).order_by(Book.id.asc())
        total, items = paginate_query_offset_limit(query, offset, limit)
        return jsonify({"total": total, "offset": offset, "limit": limit, "items": [b.to_dict() for b in items]})


@api.get("/books/<int:book_id>")
def get_book(book_id: int):
    with next(db_session()) as db:
        book = db.get(Book, book_id)
        if not book:
            raise NotFoundError("Book not found")
        return jsonify(book.to_dict())

@api.put("/books/<int:book_id>")
def update_book(book_id: int):
    data = get_json_or_400()
    try:
        payload = BookUpdateSchema(**data)
    except TypeError:
        raise BadRequestError("Invalid fields")
    with next(db_session()) as db:
        book = db.get(Book, book_id)
        if not book:
            raise NotFoundError("Book not found")
        if payload.name is not None:
            book.name = payload.name
        if payload.author is not None:
            book.author = payload.author
        if payload.status is not None:
            if payload.status not in {"free", "borrowed"}:
                raise BadRequestError("Invalid status")
            book.status = payload.status
        db.commit()
        db.refresh(book)
        return jsonify(book.to_dict())

@api.delete("/books/<int:book_id>")
def delete_book(book_id: int):
    with next(db_session()) as db:
        book = db.get(Book, book_id)
        if not book:
            raise NotFoundError("Book not found")
        db.delete(book)
        db.commit()
        return jsonify({"deleted": True})

@api.get("/books/search")
def search_books():
    q = request.args.get("q", "", type=str).strip()
    if not q:
        raise BadRequestError("q is required")
    offset, limit = parse_offset_limit()
    with next(db_session()) as db:
        query = db.query(Book).filter((Book.name == q) | (Book.author == q)).order_by(Book.id.asc())
        total, items = paginate_query_offset_limit(query, offset, limit)
        return jsonify({"total": total, "offset": offset, "limit": limit, "items": [b.to_dict() for b in items]})

@api.post("/borrows")
def create_borrow():
    data = get_json_or_400()
    try:
        payload = BorrowCreateSchema(**data)
    except TypeError:
        raise BadRequestError("user_id and book_id are required")
    with next(db_session()) as db:
        user = db.get(User, payload.user_id)
        if not user:
            raise NotFoundError("User not found")
        book = db.get(Book, payload.book_id)
        if not book:
            raise NotFoundError("Book not found")
        if book.status != "free":
            raise ConflictError("Book is not available")
        borrow = BorrowRequest(user_id=user.id, book_id=book.id, status="created")
        book.status = "borrowed"
        db.add(borrow)
        db.commit()
        db.refresh(borrow)
        db.refresh(book)
        return jsonify({"borrow": borrow.to_dict(), "book": book.to_dict()}), 201
