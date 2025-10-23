from dataclasses import dataclass


@dataclass
class RegisterSchema:
    username: str
    password: str

@dataclass
class LoginSchema:
    username: str
    password: str

@dataclass
class TokenResponse:
    access_token: str
    token_type: str = "bearer"

@dataclass
class UserCreateSchema:
    username: str
    password: str

@dataclass
class UserUpdateSchema:
    username: str | None = None
    password: str | None = None

@dataclass
class BookCreateSchema:
    name: str
    author: str
    status: str | None = None

@dataclass
class BookUpdateSchema:
    name: str | None = None
    author: str | None = None
    status: str | None = None

@dataclass
class BorrowCreateSchema:
    user_id: int
    book_id: int
