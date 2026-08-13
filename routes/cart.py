from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import current_user, login_required
from datetime import datetime

from models import db, Cart, Product, Coupon, Order, OrderItem, Address, Payment, Inventory, Notification
from utils import calculate_cart_total, apply_coupon, generate_order_number

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/')
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).order_by(Cart.created_at.desc()).all()
    subtotal = calculate_cart_total(cart_items)
    
    # Apply coupon if in session
    discount = 0
    coupon_code = session.get('coupon_code')
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
        if coupon:
            discount = apply_coupon(coupon, subtotal)
    
    shipping = 0 if subtotal >= 500 else 99
    tax = round(subtotal * 0.05, 2)
    grand_total = subtotal - discount + shipping + tax
    
    return render_template('cart.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         discount=discount,
                         shipping=shipping,
                         tax=tax,
                         grand_total=grand_total)

@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    variant_id = request.form.get('variant_id', type=int)
    
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        flash('Product is not available!', 'danger')
        return redirect(url_for('products.product_detail', slug=product.slug))
    
    # Check stock
    if product.stock < quantity:
        flash('Not enough stock!', 'danger')
        return redirect(url_for('products.product_detail', slug=product.slug))
    
    # Check if product already in cart
    existing = Cart.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id,
        variant_id=variant_id
    ).first()
    
    if existing:
        existing.quantity += quantity
        if existing.quantity > product.stock:
            existing.quantity = product.stock
            flash('Quantity adjusted to available stock!', 'warning')
        flash('Cart updated!', 'info')
    else:
        cart_item = Cart(
            user_id=current_user.id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=min(quantity, product.stock)
        )
        db.session.add(cart_item)
        flash('Product added to cart!', 'success')
    
    db.session.commit()
    
    # Check if it's an AJAX request (buy now button)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        return jsonify({'success': True, 'cart_count': cart_count})
    
    return redirect(request.referrer or url_for('cart.view_cart'))

@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = Cart.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    quantity = request.form.get('quantity', 1, type=int)
    if quantity < 1:
        quantity = 1
    if quantity > cart_item.product.stock:
        quantity = cart_item.product.stock
    
    cart_item.quantity = quantity
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        subtotal = calculate_cart_total(Cart.query.filter_by(user_id=current_user.id).all())
        return jsonify({
            'success': True,
            'item_total': cart_item.get_total(),
            'subtotal': subtotal,
            'cart_count': Cart.query.filter_by(user_id=current_user.id).count()
        })
    
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = Cart.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Product removed from cart!', 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    code = request.form.get('coupon_code', '')
    coupon = Coupon.query.filter_by(code=code, is_active=True).first()
    
    if not coupon:
        flash('Invalid coupon code!', 'danger')
    elif coupon.expires_at and coupon.expires_at < datetime.utcnow():
        flash('Coupon has expired!', 'danger')
    elif coupon.used_count >= coupon.usage_limit:
        flash('Coupon usage limit reached!', 'danger')
    else:
        session['coupon_code'] = code
        flash('Coupon applied successfully!', 'success')
    
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remove-coupon')
@login_required
def remove_coupon():
    session.pop('coupon_code', None)
    flash('Coupon removed!', 'info')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    subtotal = calculate_cart_total(cart_items)
    
    # Apply coupon
    discount = 0
    coupon_code = session.get('coupon_code')
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
        if coupon:
            discount = apply_coupon(coupon, subtotal)
    
    shipping = 0 if subtotal >= 500 else 99
    tax = round(subtotal * 0.05, 2)
    grand_total = subtotal - discount + shipping + tax
    
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            customer_name=current_user.full_name,
            customer_email=current_user.email,
            customer_phone=current_user.phone,
            subtotal=subtotal,
            discount=discount,
            coupon_code=coupon_code,
            coupon_discount=discount,
            shipping_cost=shipping,
            tax=tax,
            grand_total=grand_total,
            payment_method=request.form.get('payment_method', 'cod'),
            status='pending',
            payment_status='unpaid'
        )
        
        shipping_address_id = request.form.get('shipping_address', type=int)
        if shipping_address_id:
            order.shipping_address_id = shipping_address_id
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            price = cart_item.product.discount_price or cart_item.product.price
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                variant_id=cart_item.variant_id,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                product_image=cart_item.product.get_primary_image(),
                price=price,
                quantity=cart_item.quantity,
                total=price * cart_item.quantity
            )
            db.session.add(order_item)
            
            # Update stock
            cart_item.product.stock -= cart_item.quantity
            if cart_item.product.stock < 0:
                cart_item.product.stock = 0
        
        # Clear cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        
        # Update coupon usage
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                coupon.used_count += 1
        
        # Create payment record
        payment = Payment(
            order_id=order.id,
            payment_method=request.form.get('payment_method', 'cod'),
            amount=grand_total,
            status='pending' if request.form.get('payment_method') == 'cod' else 'paid'
        )
        db.session.add(payment)
        
        # Create notification
        notif = Notification(
            user_id=current_user.id,
            title='Order Placed',
            message=f'Your order #{order.order_number} has been placed successfully!',
            type='success',
            link=url_for('customer.order_detail', order_id=order.id)
        )
        db.session.add(notif)
        
        db.session.commit()
        session.pop('coupon_code', None)
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('cart.order_confirmation', order_id=order.id))
    
    return render_template('checkout.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         discount=discount,
                         shipping=shipping,
                         tax=tax,
                         grand_total=grand_total,
                         addresses=addresses)

@cart_bp.route('/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    return render_template('order_confirmation.html', order=order)
