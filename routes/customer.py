from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models import db, User, Order, OrderItem, Address, Notification, Review
from forms import ProfileForm, ChangePasswordForm, AddressForm, ReviewForm

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/profile')
@login_required
def profile():
    return render_template('customer/profile.html')

@customer_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        if form.avatar.data:
            # Save avatar
            from utils import save_image
            avatar_path = save_image(form.avatar.data, 'avatars', (200, 200))
            if avatar_path:
                current_user.avatar = avatar_path
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customer.profile'))
    return render_template('customer/edit_profile.html', form=form)

@customer_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('customer.profile'))
        else:
            flash('Current password is incorrect!', 'danger')
    return render_template('customer/change_password.html', form=form)

@customer_bp.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('customer/orders.html', orders=orders)

@customer_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    return render_template('customer/order_detail.html', order=order)

@customer_bp.route('/orders/invoice/<int:order_id>')
@login_required
def invoice(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    return render_template('customer/invoice.html', order=order)

@customer_bp.route('/track-order/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    return render_template('customer/track_order.html', order=order)

@customer_bp.route('/addresses')
@login_required
def addresses():
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('customer/addresses.html', addresses=addresses)

@customer_bp.route('/addresses/add', methods=['GET', 'POST'])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        address = Address(
            user_id=current_user.id,
            label=form.label.data,
            full_name=form.full_name.data or current_user.full_name,
            phone=form.phone.data or current_user.phone,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            country=form.country.data,
            is_default=form.is_default.data
        )
        
        if form.is_default.data:
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!', 'success')
        return redirect(url_for('customer.addresses'))
    
    return render_template('customer/address_form.html', form=form, title='Add Address')

@customer_bp.route('/addresses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_address(id):
    address = Address.query.get_or_404(id)
    if address.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('customer.addresses'))
    
    form = AddressForm(obj=address)
    if form.validate_on_submit():
        form.populate_obj(address)
        if form.is_default.data:
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
            address.is_default = True
        db.session.commit()
        flash('Address updated successfully!', 'success')
        return redirect(url_for('customer.addresses'))
    
    return render_template('customer/address_form.html', form=form, title='Edit Address', address=address)

@customer_bp.route('/addresses/delete/<int:id>')
@login_required
def delete_address(id):
    address = Address.query.get_or_404(id)
    if address.user_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('customer.addresses'))
    db.session.delete(address)
    db.session.commit()
    flash('Address deleted!', 'success')
    return redirect(url_for('customer.addresses'))

@customer_bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('customer/notifications.html', notifications=notifications)

@customer_bp.route('/notifications/count')
@login_required
def notification_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
