from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import db, Product, User, Cart, Wishlist
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecret123"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///laikipia.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# ✅ Initialize db with app
db.init_app(app)

with app.app_context():
    db.create_all()

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

@app.route('/home')
def home():
    if "user_id" in session:
        # user is logged in
        products = Product.query.all()
        return render_template("home.html", products=products, logged_in=True)
    else:
        products = Product.query.all()
        return render_template("home.html", products=products, logged_in=False)


@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        try:
            name = request.form['productName']
            desc = request.form['productDesc']
            price = float(request.form['productPrice'])
            image_file = request.files['productImage']

            filename = image_file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_file.save(save_path)

            product = Product(name=name, description=desc, price=price, image=f'uploads/{filename}')
            db.session.add(product)
            db.session.commit()

            return jsonify({"message": "Product listed successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # ✅ When GET request → render the Sell form
    return render_template('sell.html')


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
