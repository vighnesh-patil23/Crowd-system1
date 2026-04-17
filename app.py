from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database.db"

# ---------- FOLDER ----------
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # LIVE RECORDS
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
        name TEXT,
        phone TEXT,
        village TEXT,
        message TEXT,
        image TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- ADMIN LOGIN ----------
AUTH_USERS = {
    "admin": "1234",
    "police": "9999"
}

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    msg = ""

    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        # ADMIN
        if role == "authority":
            if username in AUTH_USERS and AUTH_USERS[username] == password:
                session["user"] = username
                session["role"] = "admin"
                return redirect("/dashboard")
            else:
                msg = "Invalid Username or Password"

        # CITIZEN
        else:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session["user"] = username
                session["role"] = "citizen"
                return redirect("/dashboard")
            else:
                msg = "User not found"

    return render_template("login.html", message=msg)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    msg = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = sqlite3.connect(DB)
            conn.execute("INSERT INTO users(username,password) VALUES(?,?)",
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

# ---------- LIVE ----------
@app.route("/live", methods=["GET","POST"])
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

# ---------- CITIZEN COMPLAINT PAGE ----------
@app.route("/citizen_complaint")
def citizen_complaint():
    if "user" not in session:
        return redirect("/")
    return render_template("citizen_complaint.html")

# ---------- SUBMIT COMPLAINT ----------
@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():

    name = request.form.get("name")
    phone = request.form.get("phone")
    village = request.form.get("village")
    message = request.form.get("message")
    image = request.files["image"]

    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
    image.save("static/uploads/" + filename)

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO complaints(name,phone,village,message,image,status) VALUES(?,?,?,?,?,?)",
        (name, phone, village, message, filename, "Pending")
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------- ADMIN COMPLAINT ----------
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

# ---------- ADMIN RESOLVE ----------
@app.route("/resolve/<int:id>")
def resolve(id):

    conn = sqlite3.connect(DB)
    conn.execute("UPDATE complaints SET status='Resolved' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/complaint")

# ---------- CITIZEN VIEW ----------
@app.route("/my_complaints")
def my_complaints():

    if "user" not in session:
        return redirect("/")

    name = session.get("user")

    conn = sqlite3.connect(DB)
    data = conn.execute(
        "SELECT * FROM complaints WHERE name=? ORDER BY id DESC",
        (name,)
    ).fetchall()
    conn.close()

    return render_template("my_complaints.html", data=data)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
