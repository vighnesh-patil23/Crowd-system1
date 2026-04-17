from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database.db"

# ---------- DATABASE INIT ----------
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

    # ALERT DATA (Raspberry uploads)
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

# ---------- AUTHORITY LOGIN ----------
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

        # AUTHORITY
        if role == "authority":
            if username in AUTH_USERS and AUTH_USERS[username] == password:
                session["user"] = username
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
            c = conn.cursor()

            c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                      (username, password))

            conn.commit()
            conn.close()

            msg = "Successfully Registered"

        except:
            msg = "Username already exists"

    return render_template("register.html", message=msg)

# ---------- DASHBOARD (2 OPTIONS) ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------- LIVE MONITORING ----------
@app.route("/live", methods=["GET","POST"])
def live():

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
        data = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
        graph_data = []

    conn.close()

    return render_template("live.html", data=data, graph_data=graph_data)

# ---------- COMPLAINT ----------
@app.route("/complaint")
def complaint():
    conn = sqlite3.connect(DB)
    complaints = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("complaint.html", complaints=complaints)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
