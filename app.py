from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE SETUP ----------
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
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
    message = ""

    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        # AUTHORITY LOGIN
        if role == "authority":
            if username in AUTH_USERS and AUTH_USERS[username] == password:
                session["user"] = username
                session["role"] = "authority"
                return redirect("/dashboard")
            else:
                message = "❌ Invalid Username or Password"

        # CITIZEN LOGIN
        else:
            conn = sqlite3.connect(DB_NAME)
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
                message = "❌ User not found. Please register"

    return render_template("login.html", message=message)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    try:
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            # check duplicate
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            existing = c.fetchone()

            if existing:
                message = "⚠ Username already exists"
            else:
                c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                          (username, password))
                conn.commit()
                message = "✅ Successfully Registered! Please Login"

            conn.close()

    except Exception as e:
        message = f"❌ Error: {str(e)}"

    return render_template("register.html", message=message)

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html",
                           user=session["user"],
                           role=session["role"])

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
