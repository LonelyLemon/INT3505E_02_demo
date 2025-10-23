from flask import Blueprint, jsonify, request
from sqlalchemy import select
from config import SessionLocal
from models import User, Book, BorrowRequest
from schemas import (
    RegisterSchema, LoginSchema, TokenResponse,
    UserCreateSchema, UserUpdateSchema,
    BookCreateSchema, BookUpdateSchema, BorrowCreateSchema
)
from exceptions import NotFoundError, BadRequestError, ConflictError, UnauthorizedError, ForbiddenError
from utils import (
    get_json_or_400, paginate_query_offset_limit, parse_offset_limit,
    hash_password, verify_password, create_access_token,
    login_required, get_current_user
)

api = Blueprint("api", __name__)

# ========== Error Handling ==========
@api.errorhandler(NotFoundError)
def handle_not_found(e): return jsonify({"error": e.message}), e.status_code

@api.errorhandler(BadRequestError)
def handle_bad_request(e): return jsonify({"error": e.message}), e.status_code

@api.errorhandler(ConflictError)
def handle_conflict(e): return jsonify({"error": e.message}), e.status_code

@api.errorhandler(UnauthorizedError)
def handle_unauth(e): return jsonify({"error": e.message}), e.status_code

@api.errorhandler(ForbiddenError)
def handle_forbidden(e): return jsonify({"error": e.message}), e.status_code

@api.errorhandler(ValueError)
def handle_value_error(e): return jsonify({"error": str(e)}), 400

def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== Auth (OAuth2 Password) ==========
@api.post("/auth/register")
def register():
    data = get_json_or_400()
    try:
        payload = RegisterSchema(**data)
    except TypeError:
        raise BadRequestError("username and password are required")
    with next(db_session()) as db:
        if db.scalar(select(User).where(User.username == payload.username)):
            raise ConflictError("Username already exists")
        user = User(username=payload.username, password=hash_password(payload.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return jsonify(user.to_dict()), 201

@api.post("/auth/login")
def login():
    """
    OAuth2 Password flow: gửi form JSON {username, password}
    trả về {access_token, token_type="bearer"} (JWT).
    """
    data = get_json_or_400()
    try:
        payload = LoginSchema(**data)
    except TypeError:
        raise BadRequestError("username and password are required")
    with next(db_session()) as db:
        user = db.scalar(select(User).where(User.username == payload.username))
        if not user or not verify_password(payload.password, user.password):
            raise UnauthorizedError("Invalid credentials")
        token = create_access_token(sub=user.username)
        return jsonify(TokenResponse(access_token=token).__dict__)

# ========== User ==========
@api.get("/users/me")
@login_required
def get_me():
    user = get_current_user()
    return jsonify(user.to_dict())

# ========== Books ==========
@api.post("/books")
@login_required
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
@login_required
def list_books():
    offset, limit = parse_offset_limit()
    with next(db_session()) as db:
        query = db.query(Book).order_by(Book.id.asc())
        total, items = paginate_query_offset_limit(query, offset, limit)
        return jsonify({"total": total, "offset": offset, "limit": limit, "items": [b.to_dict() for b in items]})

@api.get("/books/<int:book_id>")
@login_required
def get_book(book_id: int):
    with next(db_session()) as db:
        book = db.get(Book, book_id)
        if not book:
            raise NotFoundError("Book not found")
        return jsonify(book.to_dict())

@api.put("/books/<int:book_id>")
@login_required
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
            if book.status != payload.status:
                raise BadRequestError("Use borrow/return endpoints to change status")
        db.commit()
        db.refresh(book)
        return jsonify(book.to_dict())

@api.delete("/books/<int:book_id>")
@login_required
def delete_book(book_id: int):
    with next(db_session()) as db:
        book = db.get(Book, book_id)
        if not book:
            raise NotFoundError("Book not found")
        db.delete(book)
        db.commit()
        return jsonify({"deleted": True})

@api.get("/books/search")
@login_required
def search_books():
    q = request.args.get("q", "", type=str).strip()
    if not q:
        raise BadRequestError("q is required")
    offset, limit = parse_offset_limit()
    with next(db_session()) as db:
        query = db.query(Book).filter((Book.name.like(f"%{q}%")) | (Book.author.like(f"%{q}%"))).order_by(Book.id.asc())
        total, items = paginate_query_offset_limit(query, offset, limit)
        return jsonify({"total": total, "offset": offset, "limit": limit, "items": [b.to_dict() for b in items]})

@api.post("/books/<int:book_id>/borrow")
@login_required
def borrow_book(book_id: int):
    user = get_current_user()
    with next(db_session()) as db:
        book = db.get(Book, book_id)
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

@api.post("/books/<int:book_id>/return")
@login_required
def return_book(book_id: int):
    user = get_current_user()
    with next(db_session()) as db:
        book = db.get(Book, book_id)
        if not book:
            raise NotFoundError("Book not found")
        if book.status != "borrowed":
            raise ConflictError("Book is not borrowed")
        br = (
            db.query(BorrowRequest)
            .filter(BorrowRequest.book_id == book.id, BorrowRequest.status == "created")
            .order_by(BorrowRequest.id.desc())
            .first()
        )
        if br:
            br.status = "returned"
        book.status = "free"
        db.commit()
        db.refresh(book)
        return jsonify({"book": book.to_dict(), "borrow_status": br.status if br else "no_record"})
