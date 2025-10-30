from flask import jsonify

class BadRequest(Exception):
    def __init__(self, message="Bad request"):
        self.message = message

class Unauthorized(Exception):
    def __init__(self, message="Unauthorized"):
        self.message = message

class NotFound(Exception):
    def __init__(self, message="Not found"):
        self.message = message

class Conflict(Exception):
    def __init__(self, message="Conflict"):
        self.message = message

def register_error_handlers(app):
    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return jsonify({"detail": e.message}), 400

    @app.errorhandler(Unauthorized)
    def handle_unauthorized(e):
        return jsonify({"detail": e.message}), 401

    @app.errorhandler(NotFound)
    def handle_notfound(e):
        return jsonify({"detail": e.message}), 404

    @app.errorhandler(Conflict)
    def handle_conflict(e):
        return jsonify({"detail": e.message}), 409
