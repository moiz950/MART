from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
import os
import json

from models import db, User, Category, Brand, Product, ProductImage, ProductVariant, Cart, Wishlist, Order, OrderItem, Address, Review, Coupon, Discount, Payment, Inventory, Supplier, Notification, Message, NewsletterSubscriber, WebsiteSetting, ActivityLog
from forms import *
from utils import save_image, delete_image, generate_sku

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied! Admin only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.grand_total)).filter(Order.status == 'delivered').scalar() or 0
    pending_orders = Order.query.filter_by(status='pending').count()
    low_stock = Product.query.filter(Product.stock <= Product.min_stock).count()
    total_messages = Message.query.filter_by(is_read=False).count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Monthly sales data for chart
    today = datetime.utcnow()
    monthly_sales = []
    for i in range(6):
        month_start = datetime(today.year, today.month - i, 1) if today.month > i else datetime(today.year - 1, 12 + today.month - i, 1)
        if i == 0:
            month_end = today
        else:
            next_month = month_start.month + 1
            month_end = datetime(month_start.year if next_month <= 12 else month_start.year + 1, 
                                next_month if next_month <= 12 else 1, 1) - timedelta(days=1)
        sales = db.session.query(db.func.sum(Order.grand_total)).filter(
            Order.created_at >= month_start,
            Order.created_at <= month_end,
            Order.status == 'delivered'
        ).scalar() or 0
        monthly_sales.append({
            'month': month_start.strftime('%B'),
            'sales': float(sales)
        })
    monthly_sales.reverse()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders,
                         low_stock=low_stock,
                         total_messages=total_messages,
                         recent_orders=recent_orders,
                         monthly_sales=json.dumps(monthly_sales))

# ============ PRODUCT MANAGEMENT ============
@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/products.html', products=products)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.brand_id.choices = [(0, 'Select Brand')] + [(b.id, b.name) for b in Brand.query.filter_by(is_active=True).all()]
    form.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            slug=form.name.data.lower().replace(' ', '-') + '-' + datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            sku=form.sku.data or generate_sku(Category.query.get(form.category_id.data).name, Product.query.count() + 1),
            barcode=form.barcode.data,
            category_id=form.category_id.data,
            brand_id=form.brand_id.data if form.brand_id.data != 0 else None,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
            price=form.price.data,
            discount_price=form.discount_price.data,
            cost_price=form.cost_price.data,
            stock=form.stock.data,
            min_stock=form.min_stock.data or 0,
            max_stock=form.max_stock.data or 0,
            weight=form.weight.data,
            unit=form.unit.data or 'pcs',
            description=form.description.data,
            short_description=form.short_description.data,
            tags=form.tags.data,
            is_featured=form.is_featured.data,
            is_new=form.is_new.data,
            is_best_seller=form.is_best_seller.data,
            is_active=form.is_active.data,
            meta_title=form.meta_title.data or form.name.data,
            meta_description=form.meta_description.data or form.short_description.data
        )
        db.session.add(product)
        db.session.flush()
        
        # Handle images
        images = request.files.getlist('images')
        for i, img in enumerate(images):
            if img and img.filename:
                image_path = save_image(img, 'products', (800, 800))
                if image_path:
                    prod_img = ProductImage(
                        product_id=product.id,
                        image_url=image_path,
                        is_primary=(i == 0),
                        sort_order=i
                    )
                    db.session.add(prod_img)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action='Product Added',
            details=f'Added product: {product.name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', form=form, title='Add Product')

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.brand_id.choices = [(0, 'Select Brand')] + [(b.id, b.name) for b in Brand.query.filter_by(is_active=True).all()]
    form.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.sku = form.sku.data
        product.barcode = form.barcode.data
        product.category_id = form.category_id.data
        product.brand_id = form.brand_id.data if form.brand_id.data != 0 else None
        product.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        product.price = form.price.data
        product.discount_price = form.discount_price.data
        product.cost_price = form.cost_price.data
        product.stock = form.stock.data
        product.min_stock = form.min_stock.data or 0
        product.max_stock = form.max_stock.data or 0
        product.weight = form.weight.data
        product.unit = form.unit.data
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.tags = form.tags.data
        product.is_featured = form.is_featured.data
        product.is_new = form.is_new.data
        product.is_best_seller = form.is_best_seller.data
        product.is_active = form.is_active.data
        product.meta_title = form.meta_title.data
        product.meta_description = form.meta_description.data
        
        # Handle new images
        images = request.files.getlist('images')
        for i, img in enumerate(images):
            if img and img.filename:
                image_path = save_image(img, 'products', (800, 800))
                if image_path:
                    prod_img = ProductImage(
                        product_id=product.id,
                        image_url=image_path,
                        sort_order=i
                    )
                    db.session.add(prod_img)
        
        log = ActivityLog(
            user_id=current_user.id,
            action='Product Updated',
            details=f'Updated product: {product.name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', form=form, title='Edit Product', product=product)

@admin_bp.route('/products/delete/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    
    log = ActivityLog(
        user_id=current_user.id,
        action='Product Deleted',
        details=f'Deleted product: {name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))

# ============ CATEGORY MANAGEMENT ============
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()
    form.parent_id.choices = [(0, 'None (Top Level)')] + [(c.id, c.name) for c in Category.query.filter_by(parent_id=None).all()]
    
    if form.validate_on_submit():
        cat = Category(
            name=form.name.data,
            slug=form.slug.data or form.name.data.lower().replace(' ', '-'),
            description=form.description.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
            icon=form.icon.data,
            sort_order=form.sort_order.data or 0,
            is_active=form.is_active.data
        )
        if form.image.data:
            image_path = save_image(form.image.data, 'categories', (400, 400))
            if image_path:
                cat.image = image_path
        
        db.session.add(cat)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', form=form, title='Add Category')

@admin_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    form = CategoryForm(obj=cat)
    form.parent_id.choices = [(0, 'None (Top Level)')] + [(c.id, c.name) for c in Category.query.filter_by(parent_id=None).all()]
    
    if form.validate_on_submit():
        cat.name = form.name.data
        cat.slug = form.slug.data
        cat.description = form.description.data
        cat.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        cat.icon = form.icon.data
        cat.sort_order = form.sort_order.data or 0
        cat.is_active = form.is_active.data
        
        if form.image.data and form.image.data.filename:
            if cat.image and 'default' not in cat.image:
                delete_image(cat.image)
            image_path = save_image(form.image.data, 'categories', (400, 400))
            if image_path:
                cat.image = image_path
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', form=form, title='Edit Category', category=cat)

@admin_bp.route('/categories/delete/<int:id>')
@login_required
@admin_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))

# ============ BRAND MANAGEMENT ============
@admin_bp.route('/brands')
@login_required
@admin_required
def brands():
    brands = Brand.query.order_by(Brand.name).all()
    return render_template('admin/brands.html', brands=brands)

@admin_bp.route('/brands/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_brand():
    form = BrandForm()
    if form.validate_on_submit():
        brand = Brand(
            name=form.name.data,
            slug=form.slug.data or form.name.data.lower().replace(' ', '-'),
            description=form.description.data,
            website=form.website.data,
            is_active=form.is_active.data
        )
        if form.logo.data and form.logo.data.filename:
            logo_path = save_image(form.logo.data, 'brands', (200, 200))
            if logo_path:
                brand.logo = logo_path
        
        db.session.add(brand)
        db.session.commit()
        flash('Brand added successfully!', 'success')
        return redirect(url_for('admin.brands'))
    
    return render_template('admin/brand_form.html', form=form, title='Add Brand')

@admin_bp.route('/brands/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_brand(id):
    brand = Brand.query.get_or_404(id)
    form = BrandForm(obj=brand)
    if form.validate_on_submit():
        brand.name = form.name.data
        brand.slug = form.slug.data
        brand.description = form.description.data
        brand.website = form.website.data
        brand.is_active = form.is_active.data
        
        if form.logo.data and form.logo.data.filename:
            if brand.logo and 'default' not in brand.logo:
                delete_image(brand.logo)
            logo_path = save_image(form.logo.data, 'brands', (200, 200))
            if logo_path:
                brand.logo = logo_path
        
        db.session.commit()
        flash('Brand updated successfully!', 'success')
        return redirect(url_for('admin.brands'))
    
    return render_template('admin/brand_form.html', form=form, title='Edit Brand', brand=brand)

@admin_bp.route('/brands/delete/<int:id>')
@login_required
@admin_required
def delete_brand(id):
    brand = Brand.query.get_or_404(id)
    db.session.delete(brand)
    db.session.commit()
    flash('Brand deleted successfully!', 'success')
    return redirect(url_for('admin.brands'))

# ============ ORDER MANAGEMENT ============
@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/orders.html', orders=orders, current_status=status)

@admin_bp.route('/orders/<int:id>')
@login_required
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/update-status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    valid_statuses = ['pending', 'confirmed', 'processing', 'packed', 'shipped', 'delivered', 'cancelled', 'refunded']
    
    if new_status in valid_statuses:
        order.status = new_status
        setattr(order, f'{new_status}_at', datetime.utcnow())
        
        # Create notification for user
        notif = Notification(
            user_id=order.user_id,
            title=f'Order {new_status.title()}',
            message=f'Your order #{order.order_number} has been {new_status}.',
            type='info',
            link=url_for('customer.order_detail', order_id=order.id)
        )
        db.session.add(notif)
        
        db.session.commit()
        flash(f'Order status updated to {new_status}!', 'success')
    
    return redirect(url_for('admin.order_detail', id=order.id))

# ============ COUPON MANAGEMENT ============
@admin_bp.route('/coupons')
@login_required
@admin_required
def coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

@admin_bp.route('/coupons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_coupon():
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(
            code=form.code.data.upper(),
            description=form.description.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_purchase=form.min_purchase.data or 0,
            max_discount=form.max_discount.data,
            usage_limit=form.usage_limit.data or 100,
            is_active=form.is_active.data,
            starts_at=form.starts_at.data,
            expires_at=form.expires_at.data
        )
        db.session.add(coupon)
        db.session.commit()
        flash('Coupon added successfully!', 'success')
        return redirect(url_for('admin.coupons'))
    return render_template('admin/coupon_form.html', form=form, title='Add Coupon')

@admin_bp.route('/coupons/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_coupon(id):
    coupon = Coupon.query.get_or_404(id)
    form = CouponForm(obj=coupon)
    if form.validate_on_submit():
        form.populate_obj(coupon)
        coupon.code = form.code.data.upper()
        db.session.commit()
        flash('Coupon updated successfully!', 'success')
        return redirect(url_for('admin.coupons'))
    return render_template('admin/coupon_form.html', form=form, title='Edit Coupon')

@admin_bp.route('/coupons/delete/<int:id>')
@login_required
@admin_required
def delete_coupon(id):
    coupon = Coupon.query.get_or_404(id)
    db.session.delete(coupon)
    db.session.commit()
    flash('Coupon deleted successfully!', 'success')
    return redirect(url_for('admin.coupons'))

# ============ CUSTOMER MANAGEMENT ============
@admin_bp.route('/customers')
@login_required
@admin_required
def customers():
    page = request.args.get('page', 1, type=int)
    customers = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/customers.html', customers=customers)

@admin_bp.route('/customers/<int:id>')
@login_required
@admin_required
def customer_detail(id):
    customer = User.query.get_or_404(id)
    orders = Order.query.filter_by(user_id=customer.id).order_by(Order.created_at.desc()).all()
    return render_template('admin/customer_detail.html', customer=customer, orders=orders)

# ============ SUPPLIER MANAGEMENT ============
@admin_bp.route('/suppliers')
@login_required
@admin_required
def suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('admin/suppliers.html', suppliers=suppliers)

@admin_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            is_active=form.is_active.data
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('admin.suppliers'))
    return render_template('admin/supplier_form.html', form=form, title='Add Supplier')

@admin_bp.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    form = SupplierForm(obj=supplier)
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        flash('Supplier updated successfully!', 'success')
        return redirect(url_for('admin.suppliers'))
    return render_template('admin/supplier_form.html', form=form, title='Edit Supplier')

@admin_bp.route('/suppliers/delete/<int:id>')
@login_required
@admin_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('admin.suppliers'))

# ============ MESSAGES ============
@admin_bp.route('/messages')
@login_required
@admin_required
def messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

@admin_bp.route('/messages/read/<int:id>')
@login_required
@admin_required
def read_message(id):
    msg = Message.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return render_template('admin/message_detail.html', message=msg)

@admin_bp.route('/messages/delete/<int:id>')
@login_required
@admin_required
def delete_message(id):
    msg = Message.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted!', 'success')
    return redirect(url_for('admin.messages'))

# ============ REVIEWS ============
@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@admin_bp.route('/reviews/approve/<int:id>')
@login_required
@admin_required
def approve_review(id):
    review = Review.query.get_or_404(id)
    review.is_approved = True
    db.session.commit()
    flash('Review approved!', 'success')
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/delete/<int:id>')
@login_required
@admin_required
def delete_review(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted!', 'success')
    return redirect(url_for('admin.reviews'))

# ============ SUBSCRIBERS ============
@admin_bp.route('/subscribers')
@login_required
@admin_required
def subscribers():
    subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()
    return render_template('admin/subscribers.html', subscribers=subscribers)

# ============ SETTINGS ============
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        keys = ['site_name', 'site_description', 'address', 'phone', 'email', 'facebook', 'twitter', 'instagram', 'youtube', 'delivery_charge', 'free_delivery_min', 'tax_rate']
        for key in keys:
            value = request.form.get(key, '')
            setting = WebsiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = WebsiteSetting(key=key, value=value)
                db.session.add(setting)
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    settings = {}
    for setting in WebsiteSetting.query.all():
        settings[setting.key] = setting.value
    
    return render_template('admin/settings.html', settings=settings)

# ============ REPORTS ============
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    # Sales by period
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    today_sales = db.session.query(db.func.sum(Order.grand_total)).filter(
        Order.created_at >= today, Order.status == 'delivered'
    ).scalar() or 0
    
    week_sales = db.session.query(db.func.sum(Order.grand_total)).filter(
        Order.created_at >= week_ago, Order.status == 'delivered'
    ).scalar() or 0
    
    month_sales = db.session.query(db.func.sum(Order.grand_total)).filter(
        Order.created_at >= month_ago, Order.status == 'delivered'
    ).scalar() or 0
    
    # Top products
    top_products = Product.query.order_by(Product.sales_count.desc()).limit(10).all()
    
    # Top customers
    top_customers = db.session.query(
        User, db.func.count(Order.id).label('order_count'), db.func.sum(Order.grand_total).label('total_spent')
    ).join(Order, Order.user_id == User.id).filter(Order.status == 'delivered').group_by(User.id).order_by(db.desc('total_spent')).limit(10).all()
    
    return render_template('admin/reports.html',
                         today_sales=today_sales,
                         week_sales=week_sales,
                         month_sales=month_sales,
                         top_products=top_products,
                         top_customers=top_customers)

# ============ ACTIVITY LOGS ============
@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template('admin/activity_logs.html', logs=logs)

# ============ INVENTORY ============
@admin_bp.route('/inventory')
@login_required
@admin_required
def inventory():
    products = Product.query.filter(
        Product.stock <= Product.min_stock
    ).order_by(Product.stock.asc()).all()
    return render_template('admin/inventory.html', products=products)

# ============ SETTINGS / THEME ============
@admin_bp.route('/theme-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def theme_settings():
    if request.method == 'POST':
        theme_keys = ['primary_color', 'secondary_color', 'accent_color', 'header_style', 'footer_style', 'custom_css']
        for key in theme_keys:
            value = request.form.get(key, '')
            setting = WebsiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = WebsiteSetting(key=key, value=value)
                db.session.add(setting)
        db.session.commit()
        flash('Theme settings updated!', 'success')
        return redirect(url_for('admin.theme_settings'))
    
    settings = {}
    for setting in WebsiteSetting.query.all():
        settings[setting.key] = setting.value
    
    return render_template('admin/theme_settings.html', settings=settings)
