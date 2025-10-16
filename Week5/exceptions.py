class NotFoundError(Exception):
    def __init__(self, message="Not found", status_code=404):
        self.message = message
        self.status_code = status_code

class BadRequestError(Exception):
    def __init__(self, message="Bad request", status_code=400):
        self.message = message
        self.status_code = status_code

class ConflictError(Exception):
    def __init__(self, message="Conflict", status_code=409):
        self.message = message
        self.status_code = status_code
