from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Product, Activity, db, Review
from sqlalchemy import func, extract
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename

# Create Flask app once
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Configure upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize db
db.init_app(app)

# Setup migrations
migrate = Migrate(app, db)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        # Logged in → go straight to products
        return redirect(url_for('account_page'))
    # Not logged in → show public home page
    return render_template("index.html")



@app.route('/buy/<int:product_id>', methods=['GET', 'POST'])
@login_required
def buy_page(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'GET':
        # Show confirmation page
        return render_template("buy.html", product=product)

    if request.method == 'POST':
        if product.status != "approved":
            flash("❌ This product is not available for purchase yet.")
            return redirect(url_for('account_page'))

        # Payment logic would go here
        product.status = "sold"
        db.session.commit()

        # Log activity for admin dashboard
        new_activity = Activity(
            action="purchase_completed",
            user_id=current_user.id,
            product_id=product.id
        )
        db.session.add(new_activity)
        db.session.commit()

        flash(f"✅ You purchased {product.name} successfully!")
        return redirect(url_for('account_page'))

@app.route('/activity/<int:product_id>')
@login_required
def activity_details(product_id):
    product = Product.query.get_or_404(product_id)

    # Example: get the most recent activity for this product
    activity = Activity.query.filter_by(product_id=product.id).order_by(Activity.timestamp.desc()).first()

    if activity:
        return jsonify({
            "product": product.name,
            "action": activity.action,
            "actor": activity.actor.nickname,
            "timestamp": activity.timestamp.strftime("%Y-%m-%d %H:%M")
        })
    else:
        return jsonify({
            "product": product.name,
            "action": "No activity recorded",
            "actor": "N/A",
            "timestamp": "N/A"
        })





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # safer than ['identifier']
        password = request.form.get('password')

        if not identifier or not password:
            return render_template("login.html", error=True)

        # Try email first, then username
        user = User.query.filter(
            (User.email == identifier) | (User.nickname == identifier)
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return render_template("login.html", success=True)
        else:
            return render_template("login.html", error=True)

    return render_template("login.html")

@app.route('/admin/notifications')
@login_required
def admin_notifications():
    if not current_user.is_admin:
        return []

    recent = Activity.query.order_by(Activity.timestamp.desc()).limit(5).all()
    notes = []
    for act in recent:
        msg = f"{act.action} by {act.actor.nickname}"
        if act.product:
            msg += f" (Product: {act.product.name})"
        notes.append(msg)
    return jsonify(notes)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for('index'))

    sellers = db.session.query(User).join(Product).all()
    buyers = db.session.query(User).join(Activity).filter(Activity.action=="purchase_completed").all()
    products = Product.query.all()
    activities = Activity.query.order_by(Activity.timestamp.desc()).limit(20).all()
    reviews = Review.query.order_by(Review.created_at.desc()).limit(20).all()

    return render_template(
        "admin_dashboard.html",
        sellers=sellers,
        buyers=buyers,
        products=products,
        activities=activities,
        reviews=reviews
    )








@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nickname = request.form['nickname']

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Show error popup, stay on signup page
            return render_template("signup.html", error=True)

        # Create new user
        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(email=email, password=hashed_pw, nickname=nickname)
        db.session.add(new_user)
        db.session.commit()

        # ✅ Log the user in immediately after signup
        login_user(new_user, remember=True)  # remember=True keeps them logged in until logout

        # Show success popup with confetti
        return render_template("signup.html", success=True)

    return render_template("signup.html")

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_page():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])

        # Handle image upload
        image_file = request.files['image']
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_product = Product(
            name=name,
            description=description,
            price=price,
            image=f"uploads/{filename}" if filename else None,
            seller=current_user,
            status="pending"
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product listed successfully, awaiting approval.")
        return redirect(url_for('account_page'))

    return render_template('sell.html')

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    # Optional: check if product is available
    if product.status != "approved":
        flash("❌ This product is not available for purchase yet.")
        return redirect(url_for('account_page'))

    # Store cart items in session (simple prototype)
    cart = session.get('cart', [])
    if product_id not in cart:
        cart.append(product_id)
        session['cart'] = cart
        flash(f"🛒 {product.name} added to cart!")
    else:
        flash("⚠️ Product already in cart.")

    return redirect(url_for('account_page'))

@app.route('/cart')
@login_required
def view_cart():
    cart_ids = session.get('cart', [])
    products = Product.query.filter(Product.id.in_(cart_ids)).all()

    return render_template("cart.html", products=products)
@app.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    cart_ids = session.get('cart', [])
    products = Product.query.filter(Product.id.in_(cart_ids)).all()

    for product in products:
        product.status = "sold"
        db.session.commit()

        # Log activity
        new_activity = Activity(
            action="purchase_completed",
            user_id=current_user.id,
            product_id=product.id
        )
        db.session.add(new_activity)
        db.session.commit()

    # Clear cart
    session['cart'] = []
    flash("✅ Checkout complete! Products purchased successfully.")
    return redirect(url_for('account_page'))
@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
@login_required
def review_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Only allow reviews if product was purchased by this user
    purchase = Activity.query.filter_by(
        user_id=current_user.id,
        product_id=product.id,
        action="purchase_completed"
    ).first()

    if not purchase:
        flash("❌ You can only review products you have purchased.")
        return redirect(url_for('account_page'))

    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']

        new_review = Review(
            rating=rating,
            comment=comment,
            user_id=current_user.id,
            product_id=product.id
        )
        db.session.add(new_review)
        db.session.commit()

        flash("✅ Review submitted successfully!")
        return redirect(url_for('buy_page', product_id=product.id))

    return render_template("review.html", product=product)

@app.route('/categories')
def categories_page():
    # For now, just show a placeholder
    return render_template("categories.html")

@app.route('/account')
@login_required
def account_page():
    # Products listed by the current user
    my_products = Product.query.filter_by(seller_id=current_user.id).all()

    # Purchases made by the current user
    my_purchases = Activity.query.filter_by(
        user_id=current_user.id,
        action="purchase_completed"
    ).all()

    return render_template(
        "account.html",
        my_products=my_products,
        my_purchases=my_purchases
    )
@app.route('/shop')
def shop_page():
    products = Product.query.filter_by(status="approved").all()
    return render_template("shop.html", products=products)

@app.route('/admin/approve/<int:product_id>')
@login_required
def approve_product(product_id):
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for('index'))

    product = Product.query.get_or_404(product_id)
    product.status = "approved"
    db.session.commit()
    flash(f"Product '{product.name}' approved.")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<int:product_id>')
@login_required
def reject_product(product_id):
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for('index'))

    product = Product.query.get_or_404(product_id)
    product.status = "rejected"
    db.session.commit()
    flash(f"Product '{product.name}' rejected.")
    return redirect(url_for('admin_dashboard'))











@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        # ⚠️ Reset tables to match current model
        db.drop_all()
        db.create_all()

        # ✅ Create default admin if not exists
        if not User.query.filter_by(email="brayoobush@gmail.com").first():
            admin_user = User(
                email="brayoobush@gmail.com",
                password=generate_password_hash("22778779", method="pbkdf2:sha256"),
                nickname="Admin",
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: email='brayoobush@gmail.com', password='22778779'")

    app.run(debug=True)
