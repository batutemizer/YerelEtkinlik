from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "your_secret_key"
CORS(app)  # React Native istekleri için CORS aktif

# --- Yardımcı Fonksiyon ---
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- WEB: Kayıt Sayfası ---
@app.route("/kayit", methods=["GET", "POST"])
def kayit():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
                               (username, email, phone, password))
                conn.commit()
                return render_template("kayit.html", success=True)
            except sqlite3.IntegrityError:
                return render_template("kayit.html", error="Bu kullanıcı adı zaten alınmış.")

    return render_template("kayit.html")

# --- API: Kayıt ---
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
                           (username, email, phone, password))
            conn.commit()
            return jsonify({"success": True, "message": "Kayıt başarılı."})
        except sqlite3.IntegrityError:
            return jsonify({"success": False, "message": "Bu kullanıcı adı zaten alınmış."})

# --- WEB: Giriş Sayfası ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()

            if user:
                session["username"] = username
                return redirect(url_for('home'))
            else:
                return render_template("login.html", error="Kullanıcı adı veya şifre yanlış.")

    return render_template("login.html")

# --- API: Giriş ---
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()  # JSON verisini alıyoruz
    username = data.get("username")
    password = data.get("password")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            return jsonify({"success": True, "message": "Giriş başarılı."})
        else:
            return jsonify({"success": False, "message": "Kullanıcı adı veya şifre yanlış."})

# --- Ana Sayfa ---
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for('login'))
    return render_template("home.html", username=session["username"])

# --- Çıkış ---
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for('login'))
@app.route("/van")
def van():
    return render_template("van.html")

@app.route("/malatya")
def malatya():
    return render_template("malatya.html")

@app.route("/kars")
def kars():
    return render_template("kars.html")

@app.route("/elazig")
def elazig():
    return render_template("elazig.html")

@app.route("/erzurum")
def erzurum():
    return render_template("erzurum.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


