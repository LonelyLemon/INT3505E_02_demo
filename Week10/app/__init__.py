from flask import Flask
from app.extensions import db, jwt, limiter, metrics
from app.auth.routes import auth_bp
from app.books.routes import books_bp
import logging
import sys

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = '482e91425bd0a7ad5e00d94544cbc345'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    metrics.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')

    with app.app_context():
        db.create_all()

    return app