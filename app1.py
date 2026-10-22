from flask import Flask, request

app1 = Flask(__name__)

students = [
    {
        "id": 1,
        "Fname": "Ali",
        "lname": "plaisir",
        "Reports": [
            {
                "title": "Bla Bla",
                "type": "Mini Senior Project",
            }
        ]
    }
]

@app1.get("/students")  # return all students inside your list
def get_students():
    return {"students": students}


@app1.get("/students/<int:student_id>")  # return one student by ID
def get_student_by_id(student_id):
    student = next((s for s in students if s["id"] == student_id), None)

    if student is None:
        return {"message": "Student not found"}, 404

    return student, 200


@app1.post("/students")
def add_student():
    request_data = request.get_json()

    new_id = max((s["id"] for s in students), default=0) + 1

    new_student = {
        "id": new_id,
        "Fname": request_data.get("Fname"),
        "lname": request_data.get("lname"),
        "Reports": request_data.get("Reports", []),
    }

    students.append(new_student)
    return new_student, 201


@app1.post("/students/<int:student_id>/report")
def add_report(student_id):
    request_data = request.get_json()

    student = next((s for s in students if s["id"] == student_id), None)

    if student is None:
        return {"message": "Student not found"}, 404

    new_report = {
        "title": request_data.get("title"),
        "type": request_data.get("type"),
    }

    student["Reports"].append(new_report)

    return {
        "message": "Report added successfully",
        "report": new_report
    }, 201
@app1.get("/students/<int:student_id>/report")
def get_student_reports(student_id):
    student = next((s for s in students if s["id"] == student_id), None)

    if student is None:
        return {"message": "Student not found"}, 404

    return {"reports": student["Reports"]}, 200


if __name__ == "__main__":
    app1.run(host="0.0.0.0", port=5000, debug=False)