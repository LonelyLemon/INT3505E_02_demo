from app.models import Book, Webhook
from app.extensions import db

class BookRepository:
    def get_all(self):
        return Book.query.all()

    def create(self, title, author):
        book = Book(title=title, author=author)
        db.session.add(book)
        db.session.commit()
        return book

    def delete(self, book_id):
        book = Book.query.get(book_id)
        if book:
            db.session.delete(book)
            db.session.commit()
            return True
        return False

class WebhookRepository:
    def get_by_event(self, event_type):
        return Webhook.query.filter_by(event_type=event_type).all()

    def create(self, user_id, url, event_type):
        webhook = Webhook(user_id=user_id, url=url, event_type=event_type)
        db.session.add(webhook)
        db.session.commit()
        return webhook