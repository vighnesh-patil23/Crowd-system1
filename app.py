from flask import Flask, render_template, request, redirect, session
import sqlite3, os, time

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- USERS ----------------
users = {
    "gram": "123",
    "patil": "123",
    "station": "123",
    "police": "123"
}

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
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
    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u] == p:
            session["user"] = u
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
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
        (village, chowk)).fetchall()
    else:
        data = conn.execute(
        "SELECT * FROM records ORDER BY id DESC").fetchall()

    conn.close()

    return render_template("dashboard.html", data=data)

# ---------------- UPLOAD API ----------------
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
    (time.ctime(), village, chowk, count, filename))
    conn.commit()
    conn.close()

    return "OK"

# ---------------- IMAGE SHOW ----------------
@app.route("/uploads/<name>")
def get_file(name):
    return open(os.path.join(UPLOAD_FOLDER, name), "rb").read()

# ---------------- RUN ----------------
app.run(host="0.0.0.0", port=5000)