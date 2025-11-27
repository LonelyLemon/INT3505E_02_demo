from app.core.repositories import BookRepository, WebhookRepository
from app.core.events import EventManager

class BookService:
    def __init__(self):
        self.book_repo = BookRepository()
        self.event_manager = EventManager()

    def get_books(self):
        return [b.to_dict() for b in self.book_repo.get_all()]

    def add_book(self, title, author):
        new_book = self.book_repo.create(title, author)
        
        payload = {"event": "book_created", "data": new_book.to_dict()}
        self.event_manager.notify("book_created", payload)
        
        return new_book.to_dict()

    def delete_book(self, book_id):
        return self.book_repo.delete(book_id)

class WebhookService:
    def __init__(self):
        self.webhook_repo = WebhookRepository()

    def register_webhook(self, user_id, url, event_type):
        webhook = self.webhook_repo.create(user_id, url, event_type)
        return webhook.to_dict()