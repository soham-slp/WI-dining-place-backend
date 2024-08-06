from flask import Blueprint, request, jsonify, current_app
from app.db import db
from app.models import DiningPlace
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from datetime import datetime
from http import HTTPStatus

dining_bp = Blueprint("dining", __name__)


def require_admin_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("x-api-key")
        if api_key and api_key == current_app.config["ADMIN_API_KEY"]:
            return f(*args, **kwargs)
        else:
            return (
                jsonify(
                    {"status": "Unauthorized: Invalid API Key", "status_code": 401}
                ),
                HTTPStatus.UNAUTHORIZED,
            )

    return decorated_function


def require_admin_login(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        identity = get_jwt_identity()
        role = identity.get("role")
        if role == "admin":
            return f(*args, **kwargs)
        else:
            return (
                jsonify(
                    {
                        "status": "Unauthorized: Admin access required",
                        "status_code": 403,
                    }
                ),
                HTTPStatus.FORBIDDEN,
            )

    return decorated_function


@dining_bp.route("/create", methods=["POST"])
@require_admin_login
@require_admin_api_key
def create_dining_place():
    data = request.get_json()
    name = data.get("name")
    address = data.get("address")
    phone_no = data.get("phone_no")
    website = data.get("website")
    open_time = datetime.strptime(
        data["operational_hours"]["open_time"], "%H:%M:%S"
    ).time()
    close_time = datetime.strptime(
        data["operational_hours"]["close_time"], "%H:%M:%S"
    ).time()
    booked_slots = data.get("booked_slots", [])

    existing_place = DiningPlace.query.filter_by(name=name).first()
    if existing_place:
        return (
            jsonify(
                {
                    "status": "Dining place with this name already exists.",
                    "status_code": 400,
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    new_place = DiningPlace(
        name=name,
        address=address,
        phone_no=phone_no,
        website=website,
        open_time=open_time,
        close_time=close_time,
        booked_slots=booked_slots,
    )
    db.session.add(new_place)
    db.session.commit()
    return (
        jsonify(
            {
                "message": "Dining place added successfully",
                "place_id": new_place.id,
                "status_code": 200,
            }
        ),
        HTTPStatus.OK,
    )


@dining_bp.route("/", methods=["GET"])
@jwt_required()
def search_dining_place():
    search_query = request.args.get("name")
    places = DiningPlace.query.filter(DiningPlace.name.ilike(f"%{search_query}%")).all()
    results = []
    for place in places:
        results.append(
            {
                "place_id": place.id,
                "name": place.name,
                "address": place.address,
                "phone_no": place.phone_no,
                "website": place.website,
                "operational_hours": {
                    "open_time": place.open_time.strftime("%H:%M:%S"),
                    "close_time": place.close_time.strftime("%H:%M:%S"),
                },
                "booked_slots": place.booked_slots,
            }
        )
    return jsonify({"results": results})


@dining_bp.route("/availability", methods=["GET"])
@jwt_required()
def check_availability():
    place_id = request.args.get("place_id")
    start_time = datetime.strptime(request.args.get("start_time"), "%Y-%m-%dT%H:%M:%SZ")
    end_time = datetime.strptime(request.args.get("end_time"), "%Y-%m-%dT%H:%M:%SZ")

    place = DiningPlace.query.get(place_id)
    if not place:
        return (
            jsonify({"status": "Dining place not found", "status_code": 404}),
            HTTPStatus.NOT_FOUND,
        )

    if start_time < datetime.combine(
        datetime.today(), place.open_time
    ) or end_time > datetime.combine(datetime.today(), place.close_time):
        return (
            jsonify(
                {
                    "status": "Requested time is outside operational hours",
                    "status_code": 400,
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    for slot in place.booked_slots:
        slot_start = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
        slot_end = datetime.fromisoformat(slot["end_time"].replace("Z", "+00:00"))
        if start_time < slot_end and end_time > slot_start:
            next_available = slot_end if end_time <= slot_end else None
            return jsonify(
                {
                    "place_id": place.id,
                    "name": place.name,
                    "phone_no": place.phone_no,
                    "available": False,
                    "next_available_slot": (
                        next_available.isoformat() if next_available else None
                    ),
                }
            )

    return jsonify(
        {
            "place_id": place.id,
            "name": place.name,
            "phone_no": place.phone_no,
            "available": True,
            "next_available_slot": None,
        }
    )


@dining_bp.route("/book", methods=["POST"])
@jwt_required()
def book_slot():
    data = request.get_json()
    place_id = data.get("place_id")
    start_time = datetime.fromisoformat(data.get("start_time").replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(data.get("end_time").replace("Z", "+00:00"))

    # Ensure the start_time is before the end_time
    if start_time >= end_time:
        return (
            jsonify(
                {
                    "status": "Invalid time slot: Start time must be before end time.",
                    "status_code": 400,
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    # Retrieve the dining place
    place = DiningPlace.query.get(place_id)
    if not place:
        return (
            jsonify({"status": "Dining place not found.", "status_code": 404}),
            HTTPStatus.NOT_FOUND,
        )

    # Extract the time part from start_time and end_time
    start_time_only = start_time.time()
    end_time_only = end_time.time()

    # Check if the requested slot is within operational hours
    if not (
        place.open_time <= start_time_only < place.close_time
        and place.open_time < end_time_only <= place.close_time
    ):
        return (
            jsonify(
                {
                    "status": "Requested time is outside operational hours",
                    "status_code": 400,
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    # Check if the requested slot overlaps with existing bookings
    for booked_slot in place.booked_slots:
        booked_start = datetime.fromisoformat(booked_slot["start_time"])
        booked_end = datetime.fromisoformat(booked_slot["end_time"])
        if start_time < booked_end and end_time > booked_start:
            return (
                jsonify(
                    {
                        "status": "Slot is not available at this moment, please try some other place",
                        "status_code": 400,
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )

    # Add the new booking slot
    new_booking = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    place.booked_slots.append(new_booking)
    db.session.commit()

    return (
        jsonify(
            {
                "status": "Slot booked successfully",
                "status_code": 200,
                "booking_id": new_booking.get("id"),  # Adjust this if needed
            }
        ),
        HTTPStatus.OK,
    )
