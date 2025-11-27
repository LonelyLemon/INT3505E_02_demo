from flask import Flask
from app.extensions import db, jwt, limiter, metrics
from app.auth.routes import auth_bp
from app.books.routes import books_bp
from flasgger import Swagger
import logging
import sys

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your-super-secret-key'

    app.config['SWAGGER'] = {
        'title': 'Library API Documentation',
        'uiversion': 2
    }

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    metrics.init_app(app)
    
    Swagger(app, template_file='../swagger.yaml')

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')

    with app.app_context():
        db.create_all()

    return app