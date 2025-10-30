from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies

def hash_password(p):
    return generate_password_hash(p)

def verify_password(p, h):
    return check_password_hash(h, p)

def issue_tokens_response(identity, additional_claims=None):
    access_token = create_access_token(identity=identity, additional_claims=additional_claims or {})
    refresh_token = create_refresh_token(identity=identity)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token})

def issue_tokens_cookie_response(identity, additional_claims=None):
    from flask import jsonify, make_response
    access_token = create_access_token(identity=identity, additional_claims=additional_claims or {})
    refresh_token = create_refresh_token(identity=identity)
    resp = make_response(jsonify({"detail": "logged in via cookies"}))
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp
