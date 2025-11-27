from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.services import BookService, WebhookService

books_bp = Blueprint('books', __name__)

book_service = BookService()
webhook_service = WebhookService()

@books_bp.route('/', methods=['GET'])
def get_books():
    return jsonify(book_service.get_books()), 200

@books_bp.route('/', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    book = book_service.add_book(data['title'], data['author'])
    return jsonify(book), 201

@books_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    success = book_service.delete_book(book_id)
    if success:
        return jsonify({"message": "Book deleted"}), 200
    return jsonify({"message": "Not found"}), 404

@books_bp.route('/webhooks', methods=['POST'])
@jwt_required()
def register_webhook():
    """Người dùng đăng ký nhận thông báo khi có sự kiện"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    webhook = webhook_service.register_webhook(
        user_id=current_user_id,
        url=data['url'],
        event_type=data['event']
    )
    return jsonify({"message": "Webhook registered", "data": webhook}), 201