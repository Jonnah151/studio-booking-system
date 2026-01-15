import os
import sqlite3
from flask import Flask, redirect, request, render_template, session, url_for

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"

DB_PATH = os.path.join("/tmp", "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT "pending"
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template("booking.html")


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form.get("name", "").strip()
        service = request.form.get("service", "").strip()
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()

        # Basic validation
        if not name or not service or not date or not time:
            return render_template("booking.html", error="Please fill all required fields.")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if slot already booked with pending/approved
        cursor.execute(
            "SELECT id FROM bookings WHERE service=? AND date=? AND time=? AND status IN (?, ?)",
            (service, date, time, "pending", "approved")
        )
        exist = cursor.fetchone()

        if exist:
            conn.close()
            return render_template("booking.html", error="This time slot is already booked.")

        cursor.execute(
            "INSERT INTO bookings(name, service, date, time, status) VALUES(?,?,?,?,?)",
            (name, service, date, time, "pending")
        )
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()

        return redirect(url_for("check_status_post", booking_id=booking_id))

    return render_template("booking.html")


@app.route("/bookings")
def bookings():
    # Admin should see this page only if logged in (optional but recommended)
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings_rows = cursor.fetchall()
    conn.close()

    return render_template("bookings.html", bookings=bookings_rows)


@app.route("/approve/<int:booking_id>", methods=["POST"])
def approve_booking(booking_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", ("approved", booking_id))
    conn.commit()
    conn.close()
    return redirect(url_for("bookings"))


@app.route("/reject/<int:booking_id>", methods=["POST"])
def reject_booking(booking_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", ("rejected", booking_id))
    conn.commit()
    conn.close()
    return redirect(url_for("bookings"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("bookings"))

        return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))


@app.route("/check_status", methods=["GET", "POST"])
def check_status():
    if request.method == "POST":
        booking_id = request.form.get("booking_id", "").strip()

        if not booking_id.isdigit():
            return render_template("check_status.html", error="Please enter a valid Booking ID.")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id=?", (int(booking_id),))
        booking_row = cursor.fetchone()
        conn.close()

        if booking_row is None:
            return render_template("check_status.html", error="Booking ID not found")

        return render_template("status.html", booking=booking_row)

    return render_template("check_status.html")


@app.route("/status/<int:booking_id>", methods=["GET"])
def check_status_post(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    booking_row = cursor.fetchone()
    conn.close()

    if booking_row is None:
        return render_template("check_status.html", error="Booking ID not found")

    return render_template("status.html", booking=booking_row)


@app.before_request
def log_method():
    # Shows requests in Render logs (useful for debugging)
    print("URL:", request.path, "METHOD:", request.method)

if __name__ == "__main__":
    app.run()
