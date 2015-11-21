from .. import db
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
    def delete_cart_items():
        for cart_item in current_user.cart_items:
            db.session.delete(cart_item)
        db.session.commit()


class Status:
    PENDING = 0
    APPROVED = 1
    DECLINED = 2


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.DateTime)
    status = db.Column(db.Integer)

    def __init__(self, cart_items):
        self.date = datetime.now(pytz.timezone('US/Eastern'))
        self.status = Status.PENDING

        for item in cart_items:
            vendor_id = item.listing.vendor_id
            listing_id = item.listing.id
            quantity = item.quantity
            item_name = item.listing.name
            item_price = item.listing.price
            p = Purchase(vendor_id, listing_id, self, quantity, item_name, item_price)
            db.session.add(p)

        db.session.commit()

    def __repr__(self):
        return "<Order: {}>".format(self.id)



class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    order = db.relationship("Order", backref="purchases")
    listing_id = db.Column(db.Integer)

    # purchase properties
    quantity = db.Column(db.Integer)
    item_name = db.Column(db.String(64))
    item_price = db.Column(db.Float)

    def __init__(self, vendor_id, listing_id, order, quantity, item_name, item_price):
        self.vendor_id = vendor_id
        self.listing_id = listing_id
        self.order = order
        self.quantity = quantity
        self.item_name = item_name
        self.item_price = item_price


    def __repr__(self):
        return "<Purchase: {} Listing: {}>".format(self.id, self.listing_id)
