from .. import db


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # listing properties
    listing_name = db.Column(db.String(64))
    listing_description = db.Column(db.Text)
    listing_price = db.Column(db.Float)
    listing_available = db.Column(db.Boolean, default=True)

    def __init__(self, vendor_id, listing_name, type_id, listing_price,
                 listing_description=""):
        self.vendor_id = vendor_id
        self.listing_name = listing_name
        self.listing_description = listing_description
        self.type_id = type_id
        self.listing_price = listing_price

    def __repr__(self):
        return "<Vendor: {} Listing: {} Type: {}".format(self.vendor,
                                                         self.listing_name,
                                                         self.type_id)
