from flask import current_app
from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, \
    BadSignature, SignatureExpired
from .. import db, login_manager
from sqlalchemy import or_, desc, func
from ..models import Ratings
import operator

class Permission:
    GENERAL = 0x01
    VENDOR = 0x02
    MERCHANT = 0x04
    ADMINISTER = 0x08


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    index = db.Column(db.String(64))
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    @staticmethod
    def insert_roles():
        roles = {
            'Merchant': (
                Permission.GENERAL | Permission.MERCHANT, 'merchant', False
            ),
            'Vendor': (
                Permission.GENERAL | Permission.VENDOR, 'vendor', False
            ),
            'Administrator': (
                Permission.ADMINISTER, 'admin', False
            )
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.index = roles[r][1]
            role.default = roles[r][2]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role \'%s\'>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    tutorial_completed = db.Column(db.Boolean, default=False)
    # polymorphism
    user_type = db.Column(db.String(32), nullable=False, default='user')
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    # application-specific profile fields
    description = db.Column(db.String(128), default='')
    handles_credit = db.Column(db.Boolean, default=True)
    handles_cash = db.Column(db.Boolean, default=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_admin(self):
        return self.can(Permission.ADMINISTER)

    def is_vendor(self):
        return self.can(Permission.VENDOR)

    def is_merchant(self):
        return self.can(Permission.MERCHANT)

    def is_merchant_or_vendor(self):
        return self.can(Permission.MERCHANT) or self.can(Permission.VENDOR)

    @property
    def password(self):
        raise AttributeError('`password` is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=604800):
        """Generate a confirmation token to email a new user."""

        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def generate_email_change_token(self, new_email, expiration=3600):
        """Generate an email change token to email an existing user."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def generate_password_reset_token(self, expiration=3600):
        """
        Generate a password reset change token to email to an existing user.
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def confirm_account(self, token):
        """Verify that the provided token is for this user's id."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def change_email(self, token):
        """Verify the new email for this user."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def reset_password(self, token, new_password):
        """Verify the new password for this user."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    @staticmethod
    def generate_fake(count=100, **kwargs):
        """Generate a number of fake users for testing."""
        from sqlalchemy.exc import IntegrityError
        from random import seed, choice
        from faker import Faker

        fake = Faker()
        roles = Role.query.all()

        seed()
        for i in range(count):
            role = choice(roles)
            if role.index == 'merchant':
                u = Merchant(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    password=fake.password(),
                    confirmed=True,
                    role=choice(roles),
                    **kwargs
                )
            elif role.index == 'vendor':
                u = Vendor(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    password=fake.password(),
                    confirmed=True,
                    role=choice(roles),
                    **kwargs
                )
            else:
                u = User(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    password=fake.password(),
                    confirmed=True,
                    role=choice(roles),
                    **kwargs
                )
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
    @staticmethod
    def user_search(**kwargs):
        """ Returns all users matching criteria"""
        filter_list = []
        if 'main_search_term' in kwargs:
            term = kwargs['main_search_term']
            if " " in (term.strip()):
                array_term = term.split(' ', 1) # split into first and last name
                filter_list.append(or_(User.first_name.like('%{}%'.format(array_term[0])),
                                   User.last_name.like('%{}%'.format(array_term[1]))))
            else:
                filter_list.append(or_(User.first_name.like('%{}%'.format(term)),
                                   User.last_name.like('%{}%'.format(term))))
        if 'company_search_term' in kwargs and kwargs['company_search_term']:
            term = kwargs['company_search_term']
            vendors = Vendor.query.filter(Vendor.company_name.like('%{}%'.format(term))).all()
            vendor_ids = [vendor.id for vendor in vendors]
            if len(vendor_ids) > 0:
                filter_list.append(User.id.in_(vendor_ids))
        if 'company_search_term' in kwargs and kwargs['company_search_term']:
            term = kwargs['company_search_term']
            merchants = Merchant.query.filter(Merchant.company_name.like('%{}%'.format(term))).all()
            merchant_ids = [merchant.id for merchant in merchants]
            if len(merchant_ids) > 0:
                filter_list.append(User.id.in_(merchant_ids))
        if 'user_type' in kwargs:
            user_criteria = kwargs['user_type']
            format(user_criteria)
            if user_criteria == "merchant":
                filter_list.append(User.user_type == "merchant")
            elif user_criteria == "vendor":
                filter_list.append(User.user_type == "vendor")
            elif user_criteria == "merchant_vendor":
                filter_list.append(or_(User.user_type == "merchant",
                                       User.user_type == "vendor"))
            elif user_criteria == "admin":
                filter_list.append(User.role_id == 2)
            else:
                ()
        filtered_query = User.query.filter(*filter_list)

        if 'sort_by' in kwargs and kwargs['sort_by']:
            sort = kwargs['sort_by']
            format(sort)
        else:
            sort = None

        if sort == "alphaAZ":
            sorted_query = filtered_query.order_by(func.lower(User.last_name))
        elif sort == "alphaZA":
            sorted_query = filtered_query.order_by(desc(func.lower(User.last_name)))
        else:  # default sort
            sorted_query = filtered_query.order_by(func.lower(User.last_name))
        return sorted_query

    def __repr__(self):
        return '<User \'%s\'>' % self.full_name()


class AnonymousUser(AnonymousUserMixin):
    def can(self, _):
        return False

    def is_admin(self):
        return False

    def is_vendor(self):
        return False

    def is_merchant(self):
        return False

    def is_merchant_or_vendor(self):
        return False


class Vendor(User):
    __mapper_args__ = {'polymorphic_identity': 'vendor'}
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    # are the vendor's prices visible to other vendors?
    visible = db.Column(db.Boolean, default=False)
    listings = db.relationship("Listing", backref="vendor", lazy="dynamic")
    company_name = db.Column(db.String(64), default="")
    tags = db.relationship("TagAssociation", back_populates="vendor")
    product_id_col = db.Column(db.String(64), default="ProductID")
    category_id_col = db.Column(db.String(64), default="CategoryID")
    listing_description_col = db.Column(db.String(64), default="Description")
    price_col = db.Column(db.String(64), default="Price")
    name_col = db.Column(db.String(64), default="Vendor")

    def get_tags(self):
        return [str(tag.tag.tag_name) for tag in self.tags]

    def __init__(self, **kwargs):
        super(Vendor, self).__init__(**kwargs)
        self.visible = kwargs.get('visible', False)
        self.role = Role.query.filter_by(index='vendor').first()

    def __repr__(self):
        return '<Vendor %s>' % self.full_name()

    def get_rating_value(self):
        ratings = Ratings.query.filter_by(vendor_id=self.id).all()
        if not ratings:
            return -1.0
        total_rating = 0.0
        for rating in ratings:
            total_rating += rating.star_rating
        return '%.1f' % (total_rating / len(ratings))

    def get_all_ratings(self):
        ratings = Ratings.query.filter_by(vendor_id=self.id).all()
        ratings.sort(key=lambda r: r.date_reviewed, reverse=True)
        return ratings

    def get_ratings_query(self):
        ratings = Ratings.query.filter_by(vendor_id=self.id)
        sorted_ratings = ratings.order_by(desc(Ratings.date_reviewed))
        return sorted_ratings

    def get_ratings_breakdown(self):
        ratings = Ratings.query.filter_by(vendor_id=self.id)
        ratings_breakdown = {"1.0": 0, "2.0": 0, "3.0": 0, "4.0": 0, "5.0": 0}
        for rating in ratings:
            ratings_breakdown[rating.star_rating] = ratings_breakdown.get(rating.star_rating, 0) + 1
        return ratings_breakdown

    @staticmethod
    def get_vendor_by_user_id(user_id):
            return Vendor.query.filter_by(id=user_id).first()

bookmarks_table = db.Table('bookmarks', db.Model.metadata,
                           db.Column('merchant_id', db.Integer,
                                     db.ForeignKey('users.id')),
                           db.Column('listing_id', db.Integer,
                                     db.ForeignKey('listings.id'))
                           )

bookmarked_vendor_table = db.Table('bookmarked_vendors', db.Model.metadata,
                              db.Column('merchant_id', db.Integer,
                                     db.ForeignKey('users.id')),
                              db.Column('vendor_id', db.Integer,
                                     db.ForeignKey('vendor.id')))

class Merchant(User):
    __mapper_args__ = {'polymorphic_identity': 'merchant'}
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    bookmarked_vendors = db.relationship("Vendor",
                                        secondary=bookmarked_vendor_table,
                                        backref="bookmarked_vendor_by")
    bookmarks = db.relationship("Listing",
                                secondary=bookmarks_table,
                                backref="bookmarked_by")
    cart_items = db.relationship("CartItem")
    company_name = db.Column(db.String(64), default="")

    def get_cart_listings(self):
        return [cart_item.listing for cart_item in self.cart_items]

    def get_cart_item(self, listing_id):
        """ Returns a cart_item based on its listing_id """
        for cart_item in self.cart_items:
            if cart_item.listing.id == listing_id:
                return cart_item
        return None

    def __init__(self, **kwargs):
        super(Merchant, self).__init__(**kwargs)
        self.role = Role.query.filter_by(index='merchant').first()

    def __repr__(self):
        return '<Merchant %s>' % self.full_name()




login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
