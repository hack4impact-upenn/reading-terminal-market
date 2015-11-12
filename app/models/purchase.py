from .. import db
from datetime import datetime
import pytz

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'))

    # the listing the in the purchase
    listing = db.relationship("Listing")

    # purchase properties
    quantity = db.Column(db.Integer)
    order_number = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    approved = db.Column(db.Boolean, default=False)
    in_cart = db.Column(db.Boolean, default=True)

    def __init__(self, merchant_id, listing_id, purchase_quantity, purchase_order_number, purchase_approved):
        self.merchant_id = merchant_id
        self.listing_id = listing_id
        self.quantity = purchase_quantity
        self.order_number = purchase_order_number
        self.date = datetime.now(pytz.timezone('US/Eastern'))
        self.approved = purchase_approved

    def __repr__(self):
        return "<Purchase: {} Merchant: {} Listing: {}".format(self.id,
                                                               self.merchant_id,
                                                               self.listing_id)
