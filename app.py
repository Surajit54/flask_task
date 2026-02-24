import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, instance_relative_config=True)
app.secret_key = "SUPER_SECRET_KEY_CHANGE_THIS"

DATABASE = os.path.join(app.instance_path, "database.db")
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"pdf"}

os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()

    db.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    );

    CREATE TABLE IF NOT EXISTS notices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        filename TEXT,
        date TEXT
    );

    CREATE TABLE IF NOT EXISTS results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        filename TEXT,
        date TEXT
    );

    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        post TEXT,
        created_at TEXT
    );
    """)

    # Default Admin
    try:
        db.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            ("admin", generate_password_hash("admin123"))
        )
    except:
        pass

    db.commit()
    db.close()

# ---------------- SECURITY ----------------

@app.before_request
def protect_admin():
    if request.path.startswith("/admin") or request.path.startswith("/upload"):
        if "user" not in session:
            return redirect(url_for("login"))

# ---------------- PUBLIC ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/notices")
def notices():
    db = get_db()
    data = db.execute("SELECT * FROM notices ORDER BY id DESC").fetchall()
    return render_template("notices.html", data=data)

@app.route("/results")
def results():
    db = get_db()
    data = db.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
    return render_template("results.html", data=data)

@app.route("/apply", methods=["GET","POST"])
def apply():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO applications (name,email,phone,post,created_at) VALUES (?,?,?,?,?)",
            (
                request.form["name"],
                request.form["email"],
                request.form["phone"],
                request.form["post"],
                datetime.now().strftime("%d-%m-%Y")
            )
        )
        db.commit()
        flash("Application Submitted Successfully")
    return render_template("apply.html")

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid Credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- ADMIN ----------------

@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_notice", methods=["POST"])
def upload_notice():
    title = request.form["title"]
    file = request.files["file"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        db = get_db()
        db.execute(
            "INSERT INTO notices (title,filename,date) VALUES (?,?,?)",
            (title, filename, datetime.now().strftime("%d-%m-%Y"))
        )
        db.commit()

    return redirect("/admin")

@app.route("/upload_result", methods=["POST"])
def upload_result():
    title = request.form["title"]
    file = request.files["file"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        db = get_db()
        db.execute(
            "INSERT INTO results (title,filename,date) VALUES (?,?,?)",
            (title, filename, datetime.now().strftime("%d-%m-%Y"))
        )
        db.commit()

    return redirect("/admin")

@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------------- RUN ----------------

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)