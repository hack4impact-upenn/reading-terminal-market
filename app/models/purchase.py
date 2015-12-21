from .. import db
from ..models import User, Listing
from datetime import datetime
import pytz
from sqlalchemy import CheckConstraint
from flask.ext.login import current_user


class CartItem(db.Model):
    ''' Functions as association table between listings and merchants '''
    __tablename__ = "cartItems"
    __table_args__ = (
        CheckConstraint('quantity > 0'),
    )
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'),
                           primary_key=True)
    quantity = db.Column(db.Integer)

    listing = db.relationship("Listing")

    @staticmethod
    def delete_cart_items(cart_items):
        for cart_item in cart_items:
            db.session.delete(cart_item)

    def __repr__(self):
        return "<CartItem: merchant_id {}, " \
               "listing_id {}, quantity {}>".format(self.merchant_id,
                                                    self.listing_id,
                                                    self.quantity)


class Status:
    PENDING = 0
    APPROVED = 1
    DECLINED = 2


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.DateTime)
    status = db.Column(db.Integer)

    vendor_id = db.Column(db.Integer)
    company_name = db.Column(db.String(64))

    def __init__(self, date, vendor_id):
        self.status = Status.PENDING
        self.date = date
        self.vendor_id = vendor_id
        vendor = User.query.get(vendor_id)
        self.company_name = vendor.company_name

    def __repr__(self):
        return "<Order: {}>".format(self.id)

    @staticmethod
    def order_cart_items_from_vendor(vendor_id, date=None):
        """Orders all the items in the cart from a given vendor"""

        if date is None:
            date = datetime.now(pytz.timezone('US/Eastern'))

        cart_items = CartItem.query.\
            join(Listing).\
            join(User).\
            filter_by(User.id == vendor_id).\
            filter_by(CartItem.merchant_id == current_user.id)

        order = Order(date, vendor_id)

        for item in cart_items:
            p = Purchase(
                order=order,
                listing_id=item.listing.id,
                quantity=item.quantity,
                item_name=item.listing.name,
                item_price=item.listing.price
            )
            db.session.add(p)
        db.session.add(order)
        CartItem.delete_cart_items(cart_items)
        db.session.commit()

    @staticmethod
    def order_cart_items():
        """Takes the cart items and makes an order
        for each vendor represented in the cart"""

        date = datetime.now(pytz.timezone('US/Eastern'))
        vendor_ids = set([item.listing.vendor_id for item in current_user.cart_items])

        for vendor_id in vendor_ids:
            Order.order_cart_items_from_vendor(vendor_id, date)


class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    order = db.relationship("Order", backref="purchases")
    listing_id = db.Column(db.Integer)

    # purchase properties
    quantity = db.Column(db.Integer)
    item_name = db.Column(db.String(64))
    item_price = db.Column(db.Float)

    def __init__(self, order, listing_id, quantity, item_name, item_price):
        self.order = order
        self.listing_id = listing_id
        self.quantity = quantity
        self.item_name = item_name
        self.item_price = item_price

    def __repr__(self):
        return "<Purchase: {} Listing: {}>".format(self.id, self.listing_id)
