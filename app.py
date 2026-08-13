from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import datetime, timedelta
import os
import json

from config import Config
from models import db, User, Category, Brand, Product, ProductImage, ProductVariant, Cart, Wishlist, Order, OrderItem, Address, Review, Coupon, Discount, Payment, Inventory, Supplier, Notification, Message, NewsletterSubscriber, WebsiteSetting, ActivityLog
from forms import *

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
mail = Mail(app)

# Ensure the instance folder exists and create all tables.
# This runs at import time so it works under WSGI (PythonAnywhere),
# where the `if __name__ == '__main__'` block never executes.
with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(email='admin@aamart.com').first():
        admin = User(
            username='admin',
            email='admin@aamart.com',
            full_name='Admin',
            is_admin=True,
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: admin@aamart.com / admin123')
    # Create default categories
    if not Category.query.first():
        categories_data = [
            'Grocery', 'Bakery', 'Fresh Food', 'Men', 'Women', 'Kids',
            'Electronics', 'Mobile Accessories', 'Computer Accessories',
            'Household', 'Beauty', 'Health', 'Sports', 'Toys & Games',
            'Office', 'Pet Supplies'
        ]
        for name in categories_data:
            cat = Category(name=name, slug=name.lower().replace(' ', '-'))
            db.session.add(cat)
        db.session.commit()
        print('Default categories created')

# Context Processors
@app.context_processor
def inject_globals():
    categories = Category.query.filter_by(is_active=True, parent_id=None).order_by(Category.sort_order).all()
    brands = Brand.query.filter_by(is_active=True).all()
    cart_count = 0
    wishlist_count = 0
    if current_user.is_authenticated:
        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    
    settings = {}
    for setting in WebsiteSetting.query.all():
        settings[setting.key] = setting.value
    
    return dict(
        categories=categories,
        brands=brands,
        cart_count=cart_count,
        wishlist_count=wishlist_count,
        settings=settings,
        now=datetime.utcnow()
    )

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Import and register blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.products import product_bp
from routes.cart import cart_bp
from routes.customer import customer_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(product_bp, url_prefix='/products')
app.register_blueprint(cart_bp, url_prefix='/cart')
app.register_blueprint(customer_bp, url_prefix='/customer')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Route
@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    new_products = Product.query.filter_by(is_new=True, is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    best_sellers = Product.query.filter_by(is_best_seller=True, is_active=True).order_by(Product.sales_count.desc()).limit(8).all()
    deals = Product.query.filter(Product.discount_price.isnot(None), Product.is_active==True).order_by(Product.discount_price.asc()).limit(8).all()
    return render_template('index.html', 
                         featured_products=featured_products,
                         new_products=new_products,
                         best_sellers=best_sellers,
                         deals=deals)

# Static Pages
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-conditions')
def terms_conditions():
    return render_template('terms_conditions.html')

@app.route('/return-policy')
def return_policy():
    return render_template('return_policy.html')

@app.route('/shipping-policy')
def shipping_policy():
    return render_template('shipping_policy.html')

# Search Route
@app.route('/search')
def search():
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    brand_id = request.args.get('brand', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    rating = request.args.get('rating', type=float)
    sort = request.args.get('sort', 'newest')
    
    products_query = Product.query.filter_by(is_active=True)
    
    if query:
        products_query = products_query.filter(
            Product.name.ilike(f'%{query}%') | 
            Product.description.ilike(f'%{query}%') |
            Product.tags.ilike(f'%{query}%')
        )
    
    if category_id:
        products_query = products_query.filter_by(category_id=category_id)
    if brand_id:
        products_query = products_query.filter_by(brand_id=brand_id)
    if min_price:
        products_query = products_query.filter(Product.price >= min_price)
    if max_price:
        products_query = products_query.filter(Product.price <= max_price)
    if rating:
        products_query = products_query.filter(Product.rating >= rating)
    
    if sort == 'oldest':
        products_query = products_query.order_by(Product.created_at.asc())
    elif sort == 'price_low':
        products_query = products_query.order_by(Product.price.asc())
    elif sort == 'price_high':
        products_query = products_query.order_by(Product.price.desc())
    elif sort == 'popularity':
        products_query = products_query.order_by(Product.sales_count.desc())
    elif sort == 'rating':
        products_query = products_query.order_by(Product.rating.desc())
    else:
        products_query = products_query.order_by(Product.created_at.desc())
    
    products = products_query.paginate(page=request.args.get('page', 1, type=int), per_page=12, error_out=False)
    
    return render_template('search.html', products=products, query=query)

# Newsletter Subscription
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if not existing:
            sub = NewsletterSubscriber(email=email)
            db.session.add(sub)
            db.session.commit()
            flash('Successfully subscribed to newsletter!', 'success')
        else:
            flash('Email already subscribed!', 'info')
    return redirect(request.referrer or url_for('index'))

# Offer Page
@app.route('/offers')
def offers():
    deals = Product.query.filter(Product.discount_price.isnot(None), Product.is_active==True).order_by(Product.discount_price.asc()).all()
    return render_template('offers.html', deals=deals)

@app.route('/brands')
def brands():
    all_brands = Brand.query.filter_by(is_active=True).all()
    return render_template('brands.html', brands=all_brands)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
