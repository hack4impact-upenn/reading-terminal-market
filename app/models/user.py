from flask import current_app
from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, \
    BadSignature, SignatureExpired
from .. import db, login_manager


class Permission:
    GENERAL = 0x01
    VENDOR = 0x02
    MERCHANT = 0x04
    ADMINISTER = 0xff


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
                Permission.ADMINISTER, 'admin', False  # grants all permissions
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
        import forgery_py

        roles = Role.query.all()

        seed()
        for i in range(count):
            role = choice(roles)
            if role.index == 'merchant':
                u = Merchant(
                    first_name=forgery_py.name.first_name(),
                    last_name=forgery_py.name.last_name(),
                    email=forgery_py.internet.email_address(),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    role=choice(roles),
                    **kwargs
                )
            elif role.index == 'vendor':
                u = Vendor(
                    first_name=forgery_py.name.first_name(),
                    last_name=forgery_py.name.last_name(),
                    email=forgery_py.internet.email_address(),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    role=choice(roles),
                    **kwargs
                )
            else:
                u = User(
                    first_name=forgery_py.name.first_name(),
                    last_name=forgery_py.name.last_name(),
                    email=forgery_py.internet.email_address(),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    role=choice(roles),
                    **kwargs
                )
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User \'%s\'>' % self.full_name()


class AnonymousUser(AnonymousUserMixin):
    def can(self, _):
        return False

    def is_admin(self):
        return False


class Vendor(User):
    __mapper_args__ = {'polymorphic_identity': 'vendor'}
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    # are the vendor's prices visible to other vendors?
    visible = db.Column(db.Boolean, default=False)
    listings = db.relationship("Listing", backref="vendor")

    def __init__(self, **kwargs):
        super(Vendor, self).__init__(**kwargs)
        self.visible = kwargs.get('visible', False)
        self.role = Role.query.filter_by(index='vendor').first()

    def __repr__(self):
        return '<Vendor %s>' % self.full_name()


bookmarks_table = db.Table('association', db.Model.metadata,
    db.Column('merchant_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listings.id'))
)


class Merchant(User):
    __mapper_args__ = {'polymorphic_identity': 'merchant'}
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    purchases = db.relationship("Purchase")
    bookmarks = db.relationship("Listing", secondary=bookmarks_table)

    def __init__(self, **kwargs):
        super(Merchant, self).__init__(**kwargs)
        self.role = Role.query.filter_by(index='merchant').first()

    def __repr__(self):
        return '<Merchant %s>' % self.full_name()


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
