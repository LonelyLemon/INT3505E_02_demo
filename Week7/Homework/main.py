from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from schemas import ma
from exceptions import register_error_handlers
from router import bp

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)
    db.init_app(app)
    ma.init_app(app)
    JWTManager(app)
    CORS(app, supports_credentials=True)
    register_error_handlers(app)
    app.register_blueprint(bp, url_prefix="/api")
    @app.route("/")
    def root():
        return send_from_directory("static", "index.html")
    with app.app_context():
        db.create_all()
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
