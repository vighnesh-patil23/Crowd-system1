from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
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

# ---------- HOME ----------
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
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session["user"] = username
                session["role"] = "citizen"
                return redirect("/dashboard")
            else:
                message = "❌ User not found"

    return render_template("login.html", message=message)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("INSERT INTO users(username,password) VALUES(?,?)", (username, password))
        conn.commit()
        conn.close()

        message = "✅ Successfully Registered! Please Login"

    return render_template("register.html", message=message)

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html", user=session["user"], role=session["role"])

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
