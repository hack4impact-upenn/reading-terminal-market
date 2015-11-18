from .. import db
from datetime import datetime
import pytz


class CartItem(db.Model):
    ''' Functions as association table between listings and merchants '''
    __tablename__ = "cartItems"
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'),
                           primary_key=True)
    quantity = db.Column(db.Integer)

    listing = db.relationship("Listing")


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
            vendor_id = item.listing.vendor
            listing_id = item.listing.id
            qty = item.quantity
            item = item.listing.name
            cost = item.listing.cost * qty
            db.session.add(Purchase(vendor_id, listing_id, self, qty, item,
                                    cost))

        db.session.commit()

    def __repr__(self):
        return "<Order: {}>".format(self.id)


class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    order = db.relationship("Order", backref="purchases")
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'))

    # purchase properties
    quantity = db.Column(db.Integer)
    approved = db.Column(db.Boolean, default=False)
    item = db.Column(db.String(64))
    total_cost = db.Column(db.Float)

    def __init__(self, vendor_id, listing_id, order, purchase_quantity,
                 purchase_item, purchase_total_cost):
        self.vendor_id = vendor_id
        self.listing_id = listing_id
        self.order = order
        self.quantity = purchase_quantity
        self.item = purchase_item
        self.total_cost = purchase_total_cost

    # TODO: set constraints for purchases to accord with cart behavior

    def __repr__(self):
        return "<Purchase: {} Listing: {}>".format(self.id, self.listing_id)
