from .. import db


class Listing(db.Model):
    __tablename__ = "listings"
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # listing properties
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    available = db.Column(db.Boolean, default=True)

    def __init__(self, vendor_id, listing_name, category_id, listing_price,
                 listing_description=""):
        self.vendor_id = vendor_id
        self.category_id = category_id
        self.name = listing_name
        self.description = listing_description
        self.price = listing_price

    def __repr__(self):
        return "<Listing: {} Vendor: {} Category: {}>".format(self.name,
                                                             self.vendor_id,
                                                             self.category_id)
