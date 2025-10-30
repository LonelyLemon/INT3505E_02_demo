from flask_marshmallow import Marshmallow

ma = Marshmallow()

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username")

class BookSchema(ma.Schema):
    class Meta:
        fields = ("id", "book_name", "author", "status")

class BorrowSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "book_id", "status", "borrowed_at", "returned_at")
