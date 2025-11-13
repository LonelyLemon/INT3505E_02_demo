from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app_v2.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "replace-this-with-a-strong-secret-for-v2"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=60)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    idempotency_key = db.Column(db.String(128), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    if not jti:
        return True
    return TokenBlocklist.query.filter_by(jti=jti).first() is not None

@app.before_first_request
def seed_books():
    if Book.query.count() == 0:
        sample = [
            Book(title="Clean Code", author="Robert C. Martin", price_cents=2500),
            Book(title="The Pragmatic Programmer", author="Andrew Hunt", price_cents=2000),
            Book(title="Fluent Python", author="Luciano Ramalho", price_cents=3000),
            Book(title="Design Patterns", author="Erich Gamma", price_cents=2200),
            Book(title="Refactoring", author="Martin Fowler", price_cents=2700),
        ]
        db.session.bulk_save_objects(sample)
        db.session.commit()

def deprecation_headers():
    return {
        "Deprecation": "true",
        "Sunset": "2026-02-14"
    }

@app.route("/v2/users/signup", methods=["POST"])
def signup_v2():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400
    if len(password) < 6:
        return jsonify({"msg": "password must be at least 6 characters"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "username already exists"}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    response = jsonify({"msg": "user created", "username": username})
    response.headers.update(deprecation_headers())
    return response, 201

@app.route("/v2/users/login", methods=["POST"])
def login_v2():
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
    resp = jsonify({"access_token": access, "refresh_token": refresh})
    resp.headers.update(deprecation_headers())
    return resp, 200

@app.route("/v2/users/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_v2():
    current_user_id = get_jwt_identity()
    new_access = create_access_token(identity=current_user_id)
    resp = jsonify({"access_token": new_access})
    resp.headers.update(deprecation_headers())
    return resp, 200

@app.route("/v2/users/logout_refresh", methods=["POST"])
@jwt_required(refresh=True)
def revoke_refresh():
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    resp = jsonify({"msg": "refresh token revoked"})
    resp.headers.update(deprecation_headers())
    return resp, 200

@app.route("/v2/users/me", methods=["GET"])
@jwt_required()
def me_v2():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "user not found"}), 404
    resp = jsonify({
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat()
    })
    resp.headers.update(deprecation_headers())
    return resp, 200

@app.route("/v2/books", methods=["GET"])
def list_books_v2():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except Exception:
        page = 1
    try:
        per_page = min(50, max(1, int(request.args.get("per_page", 10))))
    except Exception:
        per_page = 10
    qs = Book.query.order_by(Book.id)
    pagination = qs.paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for b in pagination.items:
        items.append({
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "price_cents": b.price_cents,
            "price": f"{b.price_cents/100:.2f}"
        })
    resp = jsonify({
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages
    })
    resp.headers.update(deprecation_headers())
    return resp, 200

@app.route("/v2/payments", methods=["POST"])
@jwt_required()
def create_payment_v2():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"msg": "book_id required"}), 400
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"msg": "book not found"}), 404

    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        existing = Payment.query.filter_by(idempotency_key=idempotency_key).first()
        if existing:
            resp = jsonify({
                "msg": "payment already processed for this idempotency key",
                "payment": {
                    "id": existing.id,
                    "user_id": existing.user_id,
                    "book_id": existing.book_id,
                    "amount_cents": existing.amount_cents,
                    "created_at": existing.created_at.isoformat()
                }
            })
            resp.headers.update(deprecation_headers())
            return resp, 200

    payment = Payment(
        user_id=user_id,
        book_id=book.id,
        amount_cents=book.price_cents,
        idempotency_key=idempotency_key
    )
    db.session.add(payment)
    db.session.commit()
    resp = jsonify({
        "msg": "payment recorded (mock)",
        "payment": {
            "id": payment.id,
            "user_id": payment.user_id,
            "book_id": payment.book_id,
            "amount_cents": payment.amount_cents,
            "created_at": payment.created_at.isoformat()
        }
    })
    resp.headers.update(deprecation_headers())
    return resp, 201

if __name__ == "__main__":
    app.run(debug=True, port=5001)
