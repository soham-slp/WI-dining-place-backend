from app.db import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    email = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


class DiningPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone_no = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(200))
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    booked_slots = db.Column(db.JSON, nullable=False, default=[])

    def __repr__(self):
        return f"<DiningPlace {self.name}>"
