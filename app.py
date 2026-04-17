from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database.db"

# ---------- CREATE FOLDERS ----------
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS (Citizen)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # RECORDS (Raspberry alerts)
    c.execute("""
    CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        village TEXT,
        chowk TEXT,
        count INTEGER,
        image TEXT
    )
    """)

    # COMPLAINTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village TEXT,
        message TEXT,
        image TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- AUTHORITY USERS ----------
AUTH_USERS = {
    "admin": "1234",
    "police": "9999"
}

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    msg = ""

    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        # AUTHORITY LOGIN
        if role == "authority":
            if username in AUTH_USERS and AUTH_USERS[username] == password:
                session["user"] = username
                return redirect("/dashboard")
            else:
                msg = "Invalid Username or Password"

        # CITIZEN LOGIN
        else:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session["user"] = username
                return redirect("/dashboard")
            else:
                msg = "User not found"

    return render_template("login.html", message=msg)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                      (username, password))
            conn.commit()
            conn.close()
            msg = "Successfully Registered"

        except:
            msg = "Username already exists"

    return render_template("register.html", message=msg)

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------- LIVE MONITORING ----------
@app.route("/live", methods=["GET", "POST"])
def live():
    if "user" not in session:
        return redirect("/")

    village = request.form.get("village")
    chowk = request.form.get("chowk")

    conn = sqlite3.connect(DB)

    if village and chowk:
        data = conn.execute(
            "SELECT * FROM records WHERE village=? AND chowk=? ORDER BY id DESC",
            (village, chowk)
        ).fetchall()

        graph_data = conn.execute(
            "SELECT time, count FROM records WHERE village=? AND chowk=?",
            (village, chowk)
        ).fetchall()
    else:
        data = []
        graph_data = []

    conn.close()

    return render_template("live.html", data=data, graph_data=graph_data)

# ---------- COMPLAINT VIEW ----------
@app.route("/complaint")
def complaint():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect(DB)
    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("complaint.html", complaints=complaints)

# ---------- CITIZEN COMPLAINT SUBMIT ----------
@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():

    village = request.form.get("village")
    message = request.form.get("message")
    image = request.files["image"]

    filename = image.filename
    image.save("static/uploads/" + filename)

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO complaints(village,message,image) VALUES(?,?,?)",
        (village, message, filename)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------- RASPBERRY UPLOAD ----------
@app.route("/live_upload", methods=["POST"])
def live_upload():

    village = request.form.get("village")
    chowk = request.form.get("chowk")
    count = request.form.get("count")
    time_data = request.form.get("time")

    image = request.files["image"]

    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
    image.save("static/uploads/" + filename)

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO records(time,village,chowk,count,image) VALUES(?,?,?,?,?)",
        (time_data, village, chowk, count, filename)
    )
    conn.commit()
    conn.close()

    return "OK"

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
