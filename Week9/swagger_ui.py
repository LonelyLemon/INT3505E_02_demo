from flask import Flask, send_from_directory, redirect
from flask_swagger_ui import get_swaggerui_blueprint
import os

SWAGGER_URL = "/docs"
API_URL = "/swagger.yaml"

app = Flask(__name__, static_folder=".")
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Books & Payments API v2"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route("/swagger.yaml")
def swagger_spec():
    return send_from_directory(".", "swagger.yaml")

if __name__ == "__main__":
    app.run(port=5010, debug=True)
