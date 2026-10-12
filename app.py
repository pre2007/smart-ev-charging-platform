from flask import Flask, jsonify, request

app = Flask(__name__)

stations = [
    {"id": 1, "name": "Coimbatore EV Station",
     "location": "Coimbatore"}
]

chargers = {
    1: {"available": True, "status": "Available"}
}

reservations = {}
sessions = {}
next_reservation_id = 1


@app.get("/api/stations")
def search_stations():
    location = request.args.get("location", "")
    result = [
        s for s in stations
        if location.lower() in s["location"].lower()
    ]
    return jsonify(result), 200


@app.get("/api/chargers/<int:charger_id>/availability")
def check_availability(charger_id):
    charger = chargers.get(charger_id)
    if charger is None:
        return jsonify({"error": "Charger not found"}), 404
    return jsonify(charger), 200


@app.post("/api/reservations")
def reserve_charger():
    global next_reservation_id

    data = request.get_json(silent=True) or {}
    charger_id = data.get("charger_id")
    user_id = data.get("user_id")

    if not isinstance(charger_id, int) or not isinstance(user_id, int):
        return jsonify({"error": "Valid user_id and charger_id required"}), 400

    charger = chargers.get(charger_id)
    if charger is None:
        return jsonify({"error": "Charger not found"}), 404

    if not charger["available"]:
        return jsonify({"error": "Charger unavailable"}), 409

    charger["available"] = False
    charger["status"] = "Reserved"

    rid = next_reservation_id
    next_reservation_id += 1

    reservations[rid] = {
        "reservation_id": rid,
        "user_id": user_id,
        "charger_id": charger_id,
        "status": "Reserved"
    }

    return jsonify(reservations[rid]), 201


@app.post("/api/sessions/<int:reservation_id>/start")
def start_charging(reservation_id):
    reservation = reservations.get(reservation_id)

    if reservation is None:
        return jsonify({"error": "Reservation not found"}), 404

    if reservation["status"] != "Reserved":
        return jsonify({"error": "Reservation is not active"}), 409

    reservation["status"] = "Charging"
    sessions[reservation_id] = {
        "session_id": reservation_id,
        "status": "Charging"
    }

    chargers[reservation["charger_id"]]["status"] = "Charging"

    return jsonify(sessions[reservation_id]), 200


@app.get("/api/sessions/<int:session_id>/status")
def get_charging_status(session_id):
    session = sessions.get(session_id)

    if session is None:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(session), 200


@app.post("/api/sessions/<int:session_id>/end")
def end_charging(session_id):
    session = sessions.get(session_id)

    if session is None:
        return jsonify({"error": "Session not found"}), 404

    if session["status"] != "Charging":
        return jsonify({"error": "Session already ended"}), 409

    session["status"] = "Completed"
    reservation = reservations[session_id]
    reservation["status"] = "Completed"

    charger_id = reservation["charger_id"]
    chargers[charger_id]["available"] = True
    chargers[charger_id]["status"] = "Available"

    return jsonify(session), 200


if __name__ == "__main__":
    app.run(debug=True)
