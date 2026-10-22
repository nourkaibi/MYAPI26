from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from functools import wraps
import secrets

app = Flask(__name__)

# Data storage
students = []
reports = []

# Token storage
access_tokens = {}
refresh_tokens = {}


# HOME
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to MYAPI26!",
        "status": "API is working"
    })


# STUDENTS - CREATE
@app.route("/students", methods=["POST"])
def create_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    required = ["idS", "FN", "LN", "DMjr", "level"]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if not isinstance(data["idS"], int) or isinstance(data["idS"], bool):
        return jsonify({"error": "idS must be an integer"}), 400

    if any(s["idS"] == data["idS"] for s in students):
        return jsonify({"error": "Student already exists"}), 409

    if not isinstance(data["FN"], str) or not data["FN"].strip():
        return jsonify({"error": "FN must be a non-empty string"}), 400

    if not isinstance(data["LN"], str) or not data["LN"].strip():
        return jsonify({"error": "LN must be a non-empty string"}), 400

    if data["DMjr"] not in (0, 1, True, False):
        return jsonify({"error": "DMjr must be 0 or 1"}), 400

    if (
        not isinstance(data["level"], int)
        or isinstance(data["level"], bool)
        or data["level"] not in (1, 2, 3, 4)
    ):
        return jsonify({"error": "level must be between 1 and 4"}), 400

    student = {
        "idS": data["idS"],
        "FN": data["FN"],
        "LN": data["LN"],
        "DMjr": int(data["DMjr"]),
        "level": data["level"]
    }

    students.append(student)

    return jsonify(student), 201


# STUDENTS - GET ALL (TOKEN REQUIRED)
def token_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({"error": "Token required"}), 401

        token = header.split(" ", 1)[1]
        expiry = access_tokens.get(token)

        if expiry is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        if datetime.now() >= expiry:
            access_tokens.pop(token, None)
            return jsonify({"error": "Invalid or expired token"}), 401

        return function(*args, **kwargs)

    return wrapper


@app.route("/students", methods=["GET"])
@token_required
def get_students():
    return jsonify(students), 200


# STUDENTS - GET ONE (TOKEN REQUIRED)
@app.route("/students/<int:student_id>", methods=["GET"])
@token_required
def get_student(student_id):
    for student in students:
        if student["idS"] == student_id:
            return jsonify(student), 200

    return jsonify({"error": "Student not found"}), 404


# STUDENTS - UPDATE
@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    student = next(
        (s for s in students if s["idS"] == student_id), None
    )

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    required = ["idS", "FN", "LN", "DMjr", "level"]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if data["idS"] != student_id:
        return jsonify({"error": "idS cannot be changed"}), 400

    if not isinstance(data["FN"], str) or not data["FN"].strip():
        return jsonify({"error": "Invalid FN"}), 400

    if not isinstance(data["LN"], str) or not data["LN"].strip():
        return jsonify({"error": "Invalid LN"}), 400

    if data["DMjr"] not in (0, 1, True, False):
        return jsonify({"error": "DMjr must be 0 or 1"}), 400

    if (
        not isinstance(data["level"], int)
        or isinstance(data["level"], bool)
        or data["level"] not in (1, 2, 3, 4)
    ):
        return jsonify({"error": "level must be between 1 and 4"}), 400

    student.update({
        "FN": data["FN"],
        "LN": data["LN"],
        "DMjr": int(data["DMjr"]),
        "level": data["level"]
    })

    return jsonify(student), 200


# STUDENTS - DELETE
@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = next(
        (s for s in students if s["idS"] == student_id), None
    )

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    students.remove(student)

    return jsonify({"message": "Student deleted"}), 200


# LOGIN - DEMONSTRATION TOKEN ISSUANCE
@app.route("/login", methods=["POST"])
def login():
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)

    access_tokens[access_token] = (
        datetime.now() + timedelta(minutes=15)
    )

    refresh_tokens[refresh_token] = (
        datetime.now() + timedelta(days=7)
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in_minutes": 15
    }), 200


# REFRESH TOKEN
@app.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    old_refresh_token = data.get("refresh_token")

    if old_refresh_token not in refresh_tokens:
        return jsonify({"error": "Invalid refresh token"}), 401

    if datetime.now() >= refresh_tokens[old_refresh_token]:
        refresh_tokens.pop(old_refresh_token, None)
        return jsonify({"error": "Refresh token expired"}), 401

    refresh_tokens.pop(old_refresh_token)

    new_access_token = secrets.token_urlsafe(32)
    new_refresh_token = secrets.token_urlsafe(32)

    access_tokens[new_access_token] = (
        datetime.now() + timedelta(minutes=15)
    )

    refresh_tokens[new_refresh_token] = (
        datetime.now() + timedelta(days=7)
    )

    return jsonify({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
        "expires_in_minutes": 15
    }), 200


# REPORTS - CREATE
@app.route("/reports", methods=["POST"])
def create_report():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    required = [
        "idR", "Title", "type", "K1", "K2", "K3", "Release date"
    ]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if not isinstance(data["idR"], int) or isinstance(data["idR"], bool):
        return jsonify({"error": "idR must be an integer"}), 400

    if any(r["idR"] == data["idR"] for r in reports):
        return jsonify({"error": "Report already exists"}), 409

    for field in ["Title", "type", "K1", "K2", "K3"]:
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({"error": f"{field} must be a non-empty string"}), 400

    try:
        datetime.strptime(data["Release date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        return jsonify({
            "error": "Release date must use YYYY-MM-DD format"
        }), 400

    report = {
        "idR": data["idR"],
        "Title": data["Title"],
        "type": data["type"],
        "K1": data["K1"],
        "K2": data["K2"],
        "K3": data["K3"],
        "Release date": data["Release date"]
    }

    reports.append(report)

    return jsonify(report), 201


# REPORTS - GET ALL
@app.route("/reports", methods=["GET"])
def get_reports():
    return jsonify(reports), 200


# REPORTS - GET ONE
@app.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    for report in reports:
        if report["idR"] == report_id:
            return jsonify(report), 200

    return jsonify({"error": "Report not found"}), 404


# REPORTS - UPDATE
@app.route("/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    report = next(
        (r for r in reports if r["idR"] == report_id), None
    )

    if report is None:
        return jsonify({"error": "Report not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    required = [
        "idR", "Title", "type", "K1", "K2", "K3", "Release date"
    ]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if data["idR"] != report_id:
        return jsonify({"error": "idR cannot be changed"}), 400

    for field in ["Title", "type", "K1", "K2", "K3"]:
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({"error": f"Invalid {field}"}), 400

    try:
        datetime.strptime(data["Release date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        return jsonify({
            "error": "Release date must use YYYY-MM-DD format"
        }), 400

    report.update({
        "Title": data["Title"],
        "type": data["type"],
        "K1": data["K1"],
        "K2": data["K2"],
        "K3": data["K3"],
        "Release date": data["Release date"]
    })

    return jsonify(report), 200


# REPORTS - DELETE
@app.route("/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    report = next(
        (r for r in reports if r["idR"] == report_id), None
    )

    if report is None:
        return jsonify({"error": "Report not found"}), 404

    reports.remove(report)

    return jsonify({"message": "Report deleted"}), 200


# ERROR HANDLING
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint or resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)