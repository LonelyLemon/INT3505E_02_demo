from datetime import timezone

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="free")

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="borrowed")
    borrowed_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    returned_at = db.Column(db.DateTime)
    user = db.relationship("User")
    book = db.relationship("Book")
