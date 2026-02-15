from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "supersecretkey"

def login_required():
    return "user_id" in session

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            return redirect("/dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s,%s,'teacher')",
            (username, password)
        )
        conn.commit()

    cursor.execute("SELECT id, username, role FROM users WHERE role='teacher'")
    teachers = cursor.fetchall()

    print("DEBUG teachers:", teachers)  # 👈 add this

    cursor.close()
    conn.close()

    return render_template("admin_dashboard.html", teachers=teachers)


"""@app.route("/students")
def students():
    if not login_required():
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("students.html", students=students)

@app.route("/student/add", methods=["GET","POST"])
def add_student():
    if not login_required():
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        cls = request.form["class"]
        marks = request.form["marks"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, roll_no, class, marks) VALUES (%s,%s,%s,%s)",
                       (name, roll, cls, marks))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/students")

    return render_template("student_form.html")
"""
@app.route("/student/<int:id>")
def student_profile(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("student_profile.html", student=student)

"""@app.route("/student/pdf/<int:id>")
def student_pdf(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Student Report: {student['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Roll: {student['roll_no']}", ln=True)
    pdf.cell(200, 10, txt=f"Class: {student['class']}", ln=True)

    pdf.output("report.pdf")

    return send_file("report.pdf", as_attachment=True)
"""
@app.route("/student/add", methods=["GET", "POST"])
def add_student():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        cls = request.form["class"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, roll_no, class) VALUES (%s,%s,%s)",
            (name, roll, cls)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/students")

    return render_template("student_form.html", student=None)

@app.route("/students")
def students():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("students.html", students=students)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get teacher class
    cursor.execute("SELECT class_teacher FROM users WHERE id=%s", (session["user_id"],))
    teacher = cursor.fetchone()
    teacher_class = teacher["class_teacher"]

    # Students of that class
    cursor.execute("SELECT id, name, roll_no, marks FROM students WHERE class=%s", (teacher_class,))
    students = cursor.fetchall()

    # Avg marks for that class
    cursor.execute(
        "SELECT COALESCE(AVG(marks), 0) AS avg_marks FROM students WHERE class=%s",
        (teacher_class,)
    )
    avg_row = cursor.fetchone()

    cursor.close()
    conn.close()

    labels = [s["name"] for s in students]
    values = [s["marks"] or 0 for s in students]

    return render_template(
        "teacher_dashboard.html",
        teacher_class=teacher_class,
        students=students,
        labels=labels,
        values=values,
        avg_marks=float(avg_row["avg_marks"])
    )

@app.route("/performance", methods=["GET", "POST"])
def student_performance():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get teacher class
    cursor.execute("SELECT class_teacher FROM users WHERE id=%s", (session["user_id"],))
    teacher = cursor.fetchone()
    teacher_class = teacher["class_teacher"]

    # Get students of this class
    cursor.execute("SELECT id, name FROM students WHERE class=%s", (teacher_class,))
    students = cursor.fetchall()

    selected_student = None
    selected_test = None
    marks = None

    overall_labels = ["Unit 1", "Unit 2", "Half Yearly", "Final"]
    overall_values = [0, 0, 0, 0]   # default for GET

    if request.method == "POST":
        student_id = request.form["student_id"]
        selected_test = request.form["test_name"]

        # Selected student info
        cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
        selected_student = cursor.fetchone()

        # Marks for selected test
        cursor.execute("""
            SELECT subject1, subject2, subject3, subject4, subject5
            FROM student_marks 
            WHERE student_id=%s AND test_name=%s
        """, (student_id, selected_test))
        marks = cursor.fetchone()

        # ✅ Overall average per exam for pie chart
        def get_avg(test_name):
            cursor.execute("""
                SELECT 
                  COALESCE(AVG(subject1 + subject2 + subject3 + subject4 + subject5) / 5, 0) AS avg_marks
                FROM student_marks
                WHERE student_id=%s AND test_name=%s
            """, (student_id, test_name))
            row = cursor.fetchone()
            return float(row["avg_marks"]) if row and row["avg_marks"] is not None else 0

        unit1_avg = get_avg("unit1")
        unit2_avg = get_avg("unit2")
        halfyearly_avg = get_avg("halfyearly")
        final_avg = get_avg("final")

        overall_values = [unit1_avg, unit2_avg, halfyearly_avg, final_avg]

    cursor.close()
    conn.close()

    return render_template(
        "student_performance.html",
        students=students,
        teacher_class=teacher_class,
        selected_student=selected_student,
        selected_test=selected_test,
        marks=marks,
        overall_labels=overall_labels,
        overall_values=overall_values
    )



@app.route("/student/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch existing student
    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found", 404

    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        student_class = request.form["class"]

        cursor.execute("""
            UPDATE students 
            SET name=%s, roll_no=%s, class=%s
            WHERE id=%s
        """, (name, roll_no, student_class, id))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/students")

    cursor.close()
    conn.close()

    return render_template("edit_student.html", student=student)

@app.route("/student/delete/<int:id>")
def delete_student(id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/students")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
