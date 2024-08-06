from flask import Blueprint, request, jsonify
from app.db import db
from app.models import User
from http import HTTPStatus
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if User.query.filter_by(username=username).first():
        return (
            jsonify(
                {
                    "status": "User already exists.",
                    "status_code": 400,
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    new_user = User(username=username, password=password, email=data.get("email"))
    db.session.add(new_user)
    db.session.commit()
    return (
        jsonify(
            {
                "status": "Account successfully created",
                "status_code": 200,
                "user_id": new_user.id,
            }
        ),
        HTTPStatus.OK,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username, password=password).first()

    if user:
        access_token = create_access_token(
            identity={"user_id": user.id, "role": user.role}
        )
        return jsonify(
            {
                "status": "Login successful",
                "status_code": 200,
                "user_id": user.id,
                "access_token": access_token,
            }
        )
    else:
        return (
            jsonify(
                {
                    "status": "Incorrect username/password provided. Please retry",
                    "status_code": 401,
                }
            ),
            HTTPStatus.UNAUTHORIZED,
        )
