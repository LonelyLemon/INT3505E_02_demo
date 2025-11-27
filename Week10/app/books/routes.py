from flask import Blueprint, request, jsonify
from app.models import Book
from app.extensions import db, limiter
from flask_jwt_extended import jwt_required
import logging

books_bp = Blueprint('books', __name__)
logger = logging.getLogger(__name__)

@books_bp.route('/', methods=['GET'])
@limiter.limit("20 per minute")
def get_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books]), 200

@books_bp.route('/', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    new_book = Book(title=data['title'], author=data['author'])
    db.session.add(new_book)
    db.session.commit()
    logger.info(f"Book added: {new_book.title}")
    return jsonify(new_book.to_dict()), 201

@books_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    logger.info(f"Book deleted ID: {book_id}")
    return jsonify({"message": "Book deleted"}), 200