from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, IntegerField, FloatField, FileField, HiddenField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    avatar = FileField('Avatar')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])

class AddressForm(FlaskForm):
    label = StringField('Label', validators=[DataRequired(), Length(max=50)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    zip_code = StringField('ZIP Code', validators=[Optional(), Length(max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(max=100)])
    is_default = BooleanField('Set as Default')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    sku = StringField('SKU', validators=[DataRequired(), Length(max=50)])
    barcode = StringField('Barcode', validators=[Optional(), Length(max=100)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    brand_id = SelectField('Brand', coerce=int, validators=[Optional()])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    discount_price = FloatField('Discount Price', validators=[Optional(), NumberRange(min=0)])
    cost_price = FloatField('Cost Price', validators=[Optional(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    min_stock = IntegerField('Min Stock', validators=[Optional(), NumberRange(min=0)])
    max_stock = IntegerField('Max Stock', validators=[Optional(), NumberRange(min=0)])
    weight = FloatField('Weight', validators=[Optional(), NumberRange(min=0)])
    unit = StringField('Unit', validators=[Optional(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    short_description = StringField('Short Description', validators=[Optional(), Length(max=500)])
    tags = StringField('Tags', validators=[Optional(), Length(max=500)])
    is_featured = BooleanField('Featured')
    is_new = BooleanField('New Arrival')
    is_best_seller = BooleanField('Best Seller')
    is_active = BooleanField('Active')
    meta_title = StringField('Meta Title', validators=[Optional(), Length(max=200)])
    meta_description = StringField('Meta Description', validators=[Optional(), Length(max=500)])

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])
    icon = StringField('Icon Class', validators=[Optional(), Length(max=50)])
    image = FileField('Image')
    sort_order = IntegerField('Sort Order', validators=[Optional()])
    is_active = BooleanField('Active')

class BrandForm(FlaskForm):
    name = StringField('Brand Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    logo = FileField('Logo')
    is_active = BooleanField('Active')

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    discount_type = SelectField('Discount Type', choices=[('percentage', 'Percentage'), ('flat', 'Flat Amount')])
    discount_value = FloatField('Discount Value', validators=[DataRequired(), NumberRange(min=0)])
    min_purchase = FloatField('Minimum Purchase', validators=[Optional(), NumberRange(min=0)])
    max_discount = FloatField('Max Discount', validators=[Optional(), NumberRange(min=0)])
    usage_limit = IntegerField('Usage Limit', validators=[Optional(), NumberRange(min=1)])
    is_active = BooleanField('Active')
    starts_at = DateTimeField('Start Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    expires_at = DateTimeField('Expiry Date', format='%Y-%m-%d %H:%M', validators=[Optional()])

class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(max=200)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    is_active = BooleanField('Active')

class WebsiteSettingForm(FlaskForm):
    key = StringField('Key', validators=[DataRequired(), Length(max=100)])
    value = TextAreaField('Value', validators=[DataRequired()])

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', coerce=int, choices=[(5, '5'), (4, '4'), (3, '3'), (2, '2'), (1, '1')], validators=[DataRequired()])
    title = StringField('Title', validators=[Optional(), Length(max=200)])
    content = TextAreaField('Review', validators=[Optional()])
