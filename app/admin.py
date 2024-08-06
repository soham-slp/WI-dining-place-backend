from flask import Blueprint, request, jsonify, abort
from app.db import db
from app.models import User
from functools import wraps
from config import Config
from http import HTTPStatus

admin_bp = Blueprint("admin", __name__)


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("x-api-key")
        if api_key and api_key == Config().ADMIN_API_KEY:
            return f(*args, **kwargs)
        else:
            abort(HTTPStatus.UNAUTHORIZED)

    return decorated_function


@admin_bp.route("/create_user", methods=["POST"])
@require_api_key
def create_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if User.query.filter_by(username=username).first():
        return jsonify(message="User already exists"), HTTPStatus.BAD_REQUEST

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message="User created"), HTTPStatus.OK


@admin_bp.route("/get_users", methods=["GET"])
@require_api_key
def get_users():
    users = User.query.all()
    users_list = [
        {"id": user.id, "username": user.username, "role": user.role} for user in users
    ]
    return jsonify(users=users_list)


@admin_bp.route("/delete_user/<int:user_id>", methods=["DELETE"])
@require_api_key
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(message="User deleted"), HTTPStatus.OK
    else:
        return jsonify(message="User not found"), HTTPStatus.NOT_FOUND
