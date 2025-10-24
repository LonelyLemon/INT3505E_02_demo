import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from config import Base, engine
from router import api


BASE_DIR = Path(__file__).resolve().parent


def create_app():
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        static_url_path="/static",
    )

    # Tạo bảng
    Base.metadata.create_all(bind=engine)

    # API
    app.register_blueprint(api, url_prefix="/api/v1")

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok"})

    # Swagger UI
    SWAGGER_URL = "/docs"
    API_URL = "/static/openapi.yaml"
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "Library API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

    @app.route("/")
    def home():
        return "Swagger UI available at /docs"

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, port=port)
