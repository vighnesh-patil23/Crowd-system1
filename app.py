from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import time

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔐 USERS
users = {
    "admin": "123"
}

# 📦 DATABASE INIT
def init_db():
    conn = sqlite3.connect("data.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        village TEXT,
        chowk TEXT,
        count INTEGER,
        image TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# 🔐 LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u] == p:
            session["user"] = u
            return redirect("/dashboard")

    return render_template("login.html")

# 📊 DASHBOARD
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "user" not in session:
        return redirect("/")

    village = request.form.get("village")
    chowk = request.form.get("chowk")

    conn = sqlite3.connect("data.db")

    if village and chowk:
        data = conn.execute(
            "SELECT * FROM records WHERE village=? AND chowk=? ORDER BY id DESC",
            (village, chowk)
        ).fetchall()
    else:
        data = conn.execute(
            "SELECT * FROM records ORDER BY id DESC"
        ).fetchall()

    conn.close()

    return render_template("dashboard.html", data=data)

# 📤 UPLOAD FROM PI
@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["image"]
    count = request.form["count"]
    village = request.form["village"]
    chowk = request.form["chowk"]

    filename = str(int(time.time())) + ".jpg"
    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)

    conn = sqlite3.connect("data.db")
    conn.execute(
        "INSERT INTO records (time,village,chowk,count,image) VALUES (?,?,?,?,?)",
        (time.ctime(), village, chowk, count, filename)
    )
    conn.commit()
    conn.close()

    return "OK"

# 🗑 DELETE
@app.route("/delete", methods=["POST"])
def delete():

    village = request.form["village"]
    chowk = request.form["chowk"]

    conn = sqlite3.connect("data.db")
    conn.execute(
        "DELETE FROM records WHERE village=? AND chowk=?",
        (village, chowk)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# 🖼 IMAGE
@app.route("/uploads/<filename>")
def show_image(filename):
    return open(os.path.join(UPLOAD_FOLDER, filename), "rb").read()

# 🔓 LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# 🚀 RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
