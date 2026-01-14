import sqlite3

def get_db_connection():
    conn = sqlite3.connect("database.db")
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
                status TEXT NOT NULL DEFAULT "Pending"
                )
            """)
    conn.commit()
    conn.close()

from flask import Flask, redirect, request, render_template,session, url_for

app = Flask(__name__)

app.secret_key = "your_secret_key"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"

@app.route('/')
def home():
    return render_template("booking.html")

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form["name"]
        service = request.form["service"]
        date = request.form["date"]
        status = "pending"
        time = request.form.get("time")
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bookings WHERE service=? AND date=? AND time=? AND status=?", (service, date, time, "pending"))
        exist = cursor.fetchone()

        if exist:
            conn.close()
            return render_template("booking.html", error="This time slot is already booked.")

        cursor.execute("INSERT INTO bookings(name,service,date,time,status) VALUES(?,?,?,?,?)", (name,service,date,time,"pending"))

        conn.commit()  
        booking_id = cursor.lastrowid
        conn.close()

        return redirect(f"/status/{booking_id}")
    return render_template("booking.html")

@app.route("/bookings")
def bookings():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    bookings = cursor.fetchall()
    conn.close()
    return render_template("bookings.html", bookings=bookings)

@app.route("/approve/<int:booking_id>", methods=["POST"])
def approve_booking(booking_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))


    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", ("approved", booking_id))
    conn.commit()
    conn.close()
    return redirect("/bookings")

@app.route("/reject/<int:booking_id>", methods=["POST"])
def reject_booking(booking_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", ("rejected", booking_id))
    conn.commit()
    conn.close()
    return redirect("/bookings")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        if username==ADMIN_USERNAME and password==ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/bookings")
        return render_template("admin_login.html", error="Invalid credentials")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

@app.route("/check_status", methods=["GET", "POST"])
def check_status():
    if request.method == "POST":
        booking_id = request.form.get("booking_id")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id=?",(booking_id,))
        booking = cursor.fetchone()
        conn.close()

        if booking is None:
            return render_template("check_status.html", error="Booking ID not found")
        return render_template("status.html", booking=booking)

    return render_template("check_status.html")

@app.route("/status/<int:booking_id>", methods=["GET", "POST"])
def check_status_post(booking_id):
    if request.method == "POST":
        booking_id = request.form.get("booking_id")
    # For GET, booking_id comes from the URL
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    if booking is None:
        return render_template("check_status.html", error="Booking ID not found")
    return render_template("status.html", booking=booking)

@app.before_request
def log_method():
    print("URL:", request.path, "METHOD:", request.method)

if __name__ == "__main__":
    init_db()
    app.run()
                                                                                                                                     