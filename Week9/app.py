from datetime import timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "replace-this-with-a-strong-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=60)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    author = db.Column(db.String(256), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)

@app.before_first_request
def seed_books():
    if Book.query.count() == 0:
        sample = [
            Book(title="Clean Code", author="Robert C. Martin", price_cents=2500),
            Book(title="The Pragmatic Programmer", author="Andrew Hunt", price_cents=2000),
            Book(title="Fluent Python", author="Luciano Ramalho", price_cents=3000),
        ]
        db.session.bulk_save_objects(sample)
        db.session.commit()

@app.route("/v1/users/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "username already exists"}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "user created", "username": username}), 201

@app.route("/v1/users/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "invalid credentials"}), 401
    access = create_access_token(identity=user.id)
    refresh = create_refresh_token(identity=user.id)
    return jsonify({"access_token": access, "refresh_token": refresh}), 200

@app.route("/v1/users/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access = create_access_token(identity=current_user_id)
    return jsonify({"access_token": new_access}), 200

@app.route("/v1/books", methods=["GET"])
def list_books():
    books = Book.query.all()
    out = []
    for b in books:
        out.append({
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "price_cents": b.price_cents,
            "price": f"{b.price_cents/100:.2f}"
        })
    return jsonify(out), 200

@app.route("/v1/payments", methods=["POST"])
@jwt_required()
def create_payment():
    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"msg": "book_id required"}), 400
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"msg": "book not found"}), 404
    user_id = get_jwt_identity()
    payment = Payment(user_id=user_id, book_id=book.id, amount_cents=book.price_cents)
    db.session.add(payment)
    db.session.commit()
    return jsonify({
        "msg": "payment recorded (mock)",
        "payment": {"id": payment.id, "user_id": payment.user_id, "book_id": payment.book_id, "amount_cents": payment.amount_cents}
    }), 201

if __name__ == "__main__":
    app.run(debug=True)
