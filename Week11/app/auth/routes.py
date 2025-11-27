from flask import Blueprint, request, jsonify
from app.models import User
from app.extensions import db, jwt, limiter
from flask_jwt_extended import create_access_token
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 400
    
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    logger.info(f"New user registered: {data['username']}")
    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        access_token = create_access_token(identity=user.id)
        logger.info(f"User logged in: {user.username}")
        return jsonify(access_token=access_token), 200
    
    logger.warning(f"Failed login attempt for: {data.get('username')}")
    return jsonify({"message": "Invalid credentials"}), 401