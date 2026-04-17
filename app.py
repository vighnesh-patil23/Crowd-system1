from flask import Flask, render_template, request, redirect, session
import sqlite3, os, time

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- ADMIN USERS ----------------
gram_admins = {
    "tirpan": {"username": "tirpan_admin", "password": "123"},
    "kotoli": {"username": "kotoli_admin", "password": "123"},
    "shirgao": {"username": "shirgao_admin", "password": "123"},
    "kerli": {"username": "kerli_admin", "password": "123"}
}

police_admin = {
    "username": "police",
    "password": "123"
}

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("data.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY,
        village TEXT,
        message TEXT,
        image TEXT,
        time TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY,
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

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    u = request.form["username"]
    p = request.form["password"]

    conn = sqlite3.connect("data.db")
    conn.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- USER LOGIN ----------------
@app.route("/user_login", methods=["POST"])
def user_login():
    u = request.form["username"]
    p = request.form["password"]

    conn = sqlite3.connect("data.db")
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
    conn.close()

    if user:
        session["role"] = "user"
        return redirect("/dashboard")

    return "Invalid User"

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["POST"])
def admin_login():

    username = request.form["username"]
    password = request.form["password"]

    # Police
    if username == police_admin["username"] and password == police_admin["password"]:
        session["role"] = "police"
        return redirect("/dashboard")

    # Gram
    for village in gram_admins:
        if username == gram_admins[village]["username"] and password == gram_admins[village]["password"]:
            session["role"] = "gram"
            session["village"] = village
            return redirect("/dashboard")

    return "Invalid Admin"

# ---------------- COMPLAINT ----------------
@app.route("/complaint", methods=["POST"])
def complaint():

    village = request.form["village"]
    msg = request.form["message"]
    file = request.files["image"]

    filename = str(int(time.time())) + ".jpg"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    conn = sqlite3.connect("data.db")
    conn.execute(
        "INSERT INTO complaints (village,message,image,time) VALUES (?,?,?,?)",
        (village,msg,filename,time.ctime())
    )
    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- RASPBERRY UPLOAD ----------------
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

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "role" not in session:
        return redirect("/")

    village = request.form.get("village")
    chowk = request.form.get("chowk")

    conn = sqlite3.connect("data.db")

    # LIVE DATA
    if village and chowk:
        data = conn.execute(
            "SELECT * FROM records WHERE village=? AND chowk=? ORDER BY id DESC",
            (village, chowk)
        ).fetchall()
    else:
        data = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()

    # COMPLAINT DATA
    if session["role"] == "gram":
        complaints = conn.execute(
            "SELECT * FROM complaints WHERE village=? ORDER BY id DESC",
            (session["village"],)
        ).fetchall()
    else:
        complaints = conn.execute(
            "SELECT * FROM complaints ORDER BY id DESC"
        ).fetchall()

    conn.close()

    return render_template("dashboard.html", data=data, complaints=complaints)

# ---------------- DELETE RECORD (WITH IMAGE DELETE) ----------------
@app.route("/delete", methods=["POST"])
def delete():

    if "role" not in session:
        return redirect("/")

    record_id = request.form["id"]

    conn = sqlite3.connect("data.db")

    # Get filename
    file = conn.execute("SELECT image FROM records WHERE id=?", (record_id,)).fetchone()

    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file[0])
        if os.path.exists(filepath):
            os.remove(filepath)   # 🔥 delete image file

    conn.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- DELETE COMPLAINT ----------------
@app.route("/delete_complaint", methods=["POST"])
def delete_complaint():

    record_id = request.form["id"]

    conn = sqlite3.connect("data.db")

    file = conn.execute("SELECT image FROM complaints WHERE id=?", (record_id,)).fetchone()

    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file[0])
        if os.path.exists(filepath):
            os.remove(filepath)

    conn.execute("DELETE FROM complaints WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- IMAGE ----------------
@app.route("/uploads/<filename>")
def show_image(filename):
    return open(os.path.join(UPLOAD_FOLDER, filename), "rb").read()

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
