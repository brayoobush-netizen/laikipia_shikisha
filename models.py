from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())

    # Relationships
    products = db.relationship("Product", backref="seller", lazy=True)
    activities = db.relationship("Activity", backref="actor", lazy=True)
    reviews = db.relationship("Review", backref="reviewer", lazy=True)


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), default="default.png")  # main image
    extra_images = db.Column(db.Text, nullable=True)          # comma-separated list of extra image filenames
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default="pending")      # pending/approved/sold
    created_at = db.Column(db.DateTime, default=func.now())
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    activities = db.relationship("Activity", backref="product", lazy=True)
    reviews = db.relationship("Review", backref="product", lazy=True)


class Activity(db.Model):
    __tablename__ = "activity"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))


class Review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1–5 stars
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
