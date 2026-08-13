from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from datetime import datetime

from models import db, Product, Category, Brand, ProductImage, Review, Wishlist, Cart
from forms import ReviewForm

product_bp = Blueprint('products', __name__)

@product_bp.route('/')
def shop():
    category_id = request.args.get('category', type=int)
    brand_id = request.args.get('brand', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    if brand_id:
        query = query.filter_by(brand_id=brand_id)
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    if sort == 'oldest':
        query = query.order_by(Product.created_at.asc())
    elif sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'popularity':
        query = query.order_by(Product.sales_count.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()
    brands = Brand.query.filter_by(is_active=True).all()
    
    return render_template('products.html', products=products, categories=categories, brands=brands)

@product_bp.route('/category/<slug>')
def category(slug):
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    products = Product.query.filter_by(category_id=category.id, is_active=True)\
        .order_by(Product.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)
    
    return render_template('category.html', category=category, products=products)

@product_bp.route('/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Increment view count
    product.views += 1
    db.session.commit()
    
    # Get related products
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(8).all()
    
    # Get reviews
    reviews = Review.query.filter_by(product_id=product.id, is_approved=True).order_by(Review.created_at.desc()).all()
    
    # Check if in wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
    
    form = ReviewForm()
    
    return render_template('product_details.html', 
                         product=product, 
                         related=related, 
                         reviews=reviews, 
                         in_wishlist=in_wishlist,
                         form=form)

@product_bp.route('/review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        # Check if user already reviewed
        existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing:
            flash('You have already reviewed this product!', 'warning')
            return redirect(url_for('products.product_detail', slug=product.slug))
        
        review = Review(
            user_id=current_user.id,
            product_id=product_id,
            rating=form.rating.data,
            title=form.title.data,
            content=form.content.data,
            order_id=request.form.get('order_id', type=int)
        )
        db.session.add(review)
        
        # Update product rating
        all_reviews = Review.query.filter_by(product_id=product_id, is_approved=True).all()
        if all_reviews:
            product.rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        else:
            product.rating = form.rating.data
        product.review_count = len(all_reviews)
        
        db.session.commit()
        flash('Review submitted successfully!', 'success')
    
    return redirect(url_for('products.product_detail', slug=product.slug))

@product_bp.route('/wishlist/add/<int:product_id>')
@login_required
def add_to_wishlist(product_id):
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not existing:
        wish = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wish)
        db.session.commit()
        flash('Product added to wishlist!', 'success')
    else:
        flash('Product already in wishlist!', 'info')
    return redirect(request.referrer or url_for('products.product_detail', slug=Product.query.get(product_id).slug))

@product_bp.route('/wishlist/remove/<int:product_id>')
@login_required
def remove_from_wishlist(product_id):
    wish = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if wish:
        db.session.delete(wish)
        db.session.commit()
        flash('Product removed from wishlist!', 'success')
    return redirect(request.referrer or url_for('index'))

@product_bp.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template('wishlist.html', wishlist_items=items)

@product_bp.route('/new-arrivals')
def new_arrivals():
    products = Product.query.filter_by(is_new=True, is_active=True).order_by(Product.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=12, error_out=False
    )
    return render_template('new_arrivals.html', products=products)

@product_bp.route('/best-sellers')
def best_sellers():
    products = Product.query.filter_by(is_best_seller=True, is_active=True).order_by(Product.sales_count.desc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=12, error_out=False
    )
    return render_template('best_sellers.html', products=products)

@product_bp.route('/deals')
def deals():
    products = Product.query.filter(Product.discount_price.isnot(None), Product.is_active==True)\
        .order_by(Product.discount_price.asc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=12, error_out=False
    )
    return render_template('deals.html', products=products)
