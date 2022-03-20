import email
from os import access
from urllib import request
from flask import *
import jwt
from werkzeug.security import check_password_hash, generate_password_hash
from src.constants.http_status_code import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT
import validators
from src.models.User import User
from src.database import db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import Swagger, swag_from



auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.post("/register")
@swag_from('./docs/auth/register.yaml')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if(len(password) < 6):
        return jsonify({"error": "Password is too short"}), HTTP_400_BAD_REQUEST

    if(len(username) < 4):
        return jsonify({"error": "Username is too short"}), HTTP_400_BAD_REQUEST

    if not username.isalnum() or  " " in username:
        return jsonify({"error": "Username should be alphanumeric and without spaces"}), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({"error": "Email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Email is already taken"}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "Username is already taken"}), HTTP_409_CONFLICT

    # Hash password 
    pwd_hash = generate_password_hash(password)
    
    user = User(username=username, password=pwd_hash, email=email)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created',
        'user': {
            'username' : username, 'email' : email
        }
    }), HTTP_201_CREATED

@auth.post('/login')
@swag_from('./docs/auth/login.yaml')
def login():
    # Get credentials from json body
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    # Search for a coresponding user in db
    user=User.query.filter_by(email=email).first()
    # If we found one
    if user:
        # Check password
        is_password_correct=check_password_hash(user.password, password)
        # If it's correct, lets send back access and refresh tokens
        if(is_password_correct):
            refresh_token=create_refresh_token(identity=user.id)
            access_token=create_access_token(identity=user.id)
            return jsonify({
                'user': {
                    'refresh': refresh_token,
                    'access':  access_token,
                    'username' : user.username,
                    'email' : user.email
                }
            }), HTTP_200_OK
    return jsonify({
        'error' : 'Wrong credentials'
    }), HTTP_401_UNAUTHORIZED        





@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    return jsonify({
        "username" : user.username,
        "email" : user.email
    }), HTTP_200_OK


@auth.get("/token/refresh")
@jwt_required(refresh=True)
def refresh_user_token():
    identity = get_jwt_identity()
    access_token=create_access_token(identity=identity)

    return jsonify({
        "access" : access_token,
    }), HTTP_200_OK

