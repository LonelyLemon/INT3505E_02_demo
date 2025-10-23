import datetime as dt
from functools import wraps
from typing import Optional

import jwt
from flask import request
from sqlalchemy import select

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SessionLocal
from exceptions import UnauthorizedError, BadRequestError
from models import User

# -------- JSON Helper --------
def get_json_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequestError("Invalid JSON body")
    return data

# -------- Pagination --------
def paginate_query_offset_limit(query, offset, limit):
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return total, items

def parse_offset_limit():
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        raise BadRequestError("Invalid pagination")
    offset = 0 if offset < 0 else offset
    limit = 1 if limit < 1 else limit
    return offset, limit

# -------- Password (hash) --------
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(raw: str) -> str:
    return generate_password_hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return check_password_hash(hashed, raw)

# -------- JWT --------
def create_access_token(sub: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + dt.timedelta(minutes=expires_minutes),
        "token_type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid token")

def get_current_user() -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise UnauthorizedError("Invalid token payload")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if not user:
            raise UnauthorizedError("User not found")
        return user

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        get_current_user()
        return fn(*args, **kwargs)
    return wrapper
