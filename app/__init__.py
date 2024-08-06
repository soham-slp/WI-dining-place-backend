from flask import Flask
from config import Config

from app.db import db, migrate
from app.auth import auth_bp
from app.admin import admin_bp
from app.dining_place import dining_bp
from flask_jwt_extended import JWTManager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(dining_bp, url_prefix="/api/dining-place")

    return app
