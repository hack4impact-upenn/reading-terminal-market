from .. import db


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # listing properties
    listing_name = db.Column(db.String(64))
    listing_description = db.Column(db.Text)
    listing_price = db.Column(db.Float)
    listing_available = db.Column(db.Boolean, default=True)

    def __init__(self, vendor_id, listing_name, category_id, listing_price,
                 listing_description=""):
        self.vendor_id = vendor_id
        self.listing_name = listing_name
        self.listing_description = listing_description
        self.category_id = category_id
        self.listing_price = listing_price

    def __repr__(self):
        return "<Vendor: {} Listing: {} Category: {}".format(self.vendor,
                                                             self.listing_name,
                                                             self.category_id)
