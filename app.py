import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Product, User, Cart, Wishlist

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

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            return "Username or Email already exists!"

        # Create new user
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route('/home')
def home():
    products = Product.query.all()
    logged_in = "user_id" in session
    return render_template("home.html", products=products, logged_in=logged_in)

@app.route("/buy/<int:product_id>", methods=["GET", "POST"])
def buy(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        # Collect specifications from form
        quantity = int(request.form["quantity"])
        color = request.form.get("color")
        size = request.form.get("size")
        payment_method = request.form["payment_method"]

        # Example: Save order to Cart table (or create an Orders table)
        order = Cart(
            user_id=session["user_id"],
            item_name=product.name,
            price=product.price * quantity,
        )
        db.session.add(order)
        db.session.commit()

        return redirect(url_for("cart"))

    return render_template("buy.html", product=product)


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
        items = Cart.query.filter_by(user_id=session["user_id"]).all()
        return render_template("cart.html", items=items)
    return redirect(url_for("login"))

@app.route("/add_to_cart/<item>/<price>")
def add_to_cart(item, price):
    if "user_id" in session:
        cart_item = Cart(user_id=session["user_id"], item_name=item, price=price)
        db.session.add(cart_item)
        db.session.commit()
        return redirect(url_for("cart"))
    return redirect(url_for("login"))

@app.route("/wishlist")
def wishlist():
    if "user_id" in session:
        items = Wishlist.query.filter_by(user_id=session["user_id"]).all()
        return render_template("wishlist.html", items=items)
    return redirect(url_for("login"))

@app.route("/add_to_wishlist/<item>")
def add_to_wishlist(item):
    if "user_id" in session:
        wish_item = Wishlist(user_id=session["user_id"], item_name=item)
        db.session.add(wish_item)
        db.session.commit()
        return redirect(url_for("wishlist"))
    return redirect(url_for("login"))

@app.route("/account")
def account():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        return render_template("account.html", username=user.username, email=user.email)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
