import os
import random
import string
import hashlib
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_image(file, subfolder='products', size=None):
    """Save uploaded image and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generate unique filename
        ext = filename.rsplit('.', 1)[1].lower()
        unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.{ext}"
        
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, unique_name)
        file.save(filepath)
        
        # Resize image if size specified
        if size:
            try:
                img = Image.open(filepath)
                img.thumbnail(size)
                img.save(filepath, optimize=True, quality=85)
            except:
                pass
        
        return f"uploads/{subfolder}/{unique_name}"
    return None

def delete_image(image_path):
    """Delete image file from uploads"""
    if image_path:
        full_path = os.path.join(current_app.root_path, 'static', image_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except:
                pass

def format_price(price):
    """Format price with commas"""
    if price is None:
        return "0"
    return f"{price:,.2f}"

def generate_sku(category_name, product_id):
    """Generate SKU for product"""
    prefix = ''.join(word[0].upper() for word in category_name.split()[:2])
    return f"{prefix}-{product_id:05d}"

def generate_order_number():
    """Generate unique order number"""
    date_str = datetime.utcnow().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"AAM-{date_str}-{random_str}"

def calculate_cart_total(cart_items):
    """Calculate total price of cart items"""
    subtotal = 0
    for item in cart_items:
        price = item.product.discount_price or item.product.price
        subtotal += price * item.quantity
    return subtotal

def apply_coupon(coupon, subtotal):
    """Apply coupon discount and return discount amount"""
    if not coupon or not coupon.is_active:
        return 0
    
    now = datetime.utcnow()
    if coupon.starts_at and now < coupon.starts_at:
        return 0
    if coupon.expires_at and now > coupon.expires_at:
        return 0
    
    if coupon.used_count >= coupon.usage_limit:
        return 0
    
    if subtotal < coupon.min_purchase:
        return 0
    
    if coupon.discount_type == 'percentage':
        discount = subtotal * (coupon.discount_value / 100)
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    else:
        discount = min(coupon.discount_value, subtotal)
    
    return round(discount, 2)

def time_ago(dt):
    """Convert datetime to human-readable time ago"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years}y ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        mins = diff.seconds // 60
        return f"{mins}m ago"
    else:
        return "Just now"

def get_rating_stars(rating):
    """Return CSS classes for rating stars"""
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    return full, half, empty

def generate_barcode():
    """Generate random barcode number"""
    return ''.join(random.choices(string.digits, k=12))

def truncate_text(text, length=100):
    """Truncate text to specified length"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + "..."
