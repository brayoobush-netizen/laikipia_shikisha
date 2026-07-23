from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change this later

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("laikipia.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect("laikipia.db")
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    # Cart table
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    # Wishlist table
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()


init_db()

# --- Routes ---
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username or Email already exists!"
        finally:
            conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route("/home")
def home():
    if "user_id" in session:
        return render_template("home.html")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))

@app.route("/categories")
def categories():
    return render_template("categories.html")

@app.route("/cart")
def cart():
    if "user_id" in session:
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        c.execute("SELECT item_name, price FROM cart WHERE user_id=?", (session["user_id"],))
        items = c.fetchall()
        conn.close()
        return render_template("cart.html", items=items)
    return redirect(url_for("login"))

@app.route("/add_to_cart/<item>/<price>")
def add_to_cart(item, price):
    if "user_id" in session:
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        c.execute("INSERT INTO cart (user_id, item_name, price) VALUES (?, ?, ?)",
                  (session["user_id"], item, price))
        conn.commit()
        conn.close()
        return redirect(url_for("cart"))
    return redirect(url_for("login"))


@app.route("/wishlist")
def wishlist():
    if "user_id" in session:
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        c.execute("SELECT item_name FROM wishlist WHERE user_id=?", (session["user_id"],))
        items = c.fetchall()
        conn.close()
        return render_template("wishlist.html", items=items)
    return redirect(url_for("login"))

@app.route("/add_to_wishlist/<item>")
def add_to_wishlist(item):
    if "user_id" in session:
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        c.execute("INSERT INTO wishlist (user_id, item_name) VALUES (?, ?)",
                  (session["user_id"], item))
        conn.commit()
        conn.close()
        return redirect(url_for("wishlist"))
    return redirect(url_for("login"))


@app.route("/account")
def account():
    if "user_id" in session:
        # Example: fetch user info from DB
        conn = sqlite3.connect("laikipia.db")
        c = conn.cursor()
        c.execute("SELECT username, email FROM users WHERE id=?", (session["user_id"],))
        user = c.fetchone()
        conn.close()
        return render_template("account.html", username=user[0], email=user[1])
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
