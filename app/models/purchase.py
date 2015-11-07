from .. import db


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))

    # purchase properties
    purchase_quantity = db.Column(db.Integer)
    purchase_order_number = db.Column(db.Integer)
    purchase_date = db.Column(db.DateTime)
    purchase_approved = db.Column(db.Boolean, default=False)

    def __init__(self, merchant_id, listing_id, purchase_quantity, purchase_order_number,
                 purchase_date, purchase_approved):
        self.merchant_id = merchant_id
        self.listing_id = listing_id
        self.purchase_quantity = purchase_quantity
        self.purchase_order_number = purchase_order_number
        self.purchase_date = purchase_date
        self.purchase_approved = purchase_approved

    def __repr__(self):
        return "<Purchase: {} Merchant: {} Listing: {}".format(self.id,
                                                               self.merchant_id,
                                                               self.listing_id)
