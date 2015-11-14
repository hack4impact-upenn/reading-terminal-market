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
    __table_args__ = (db.UniqueConstraint('vendor_id', 'name', name='_vendor_name_uc'),)

    def __init__(self, vendor_id, name, available, category_id, price,
                 description=""):
        self.vendor_id = vendor_id
        self.category_id = category_id
        self.name = name
        self.description = description
        self.price = price
        self.available = available

    def __repr__(self):
        return "<Listing: {} Listing id: {} " \
               "Vendor: {} Category: {}>".format(self.name,
                                                 self.id,
                                                 self.vendor_id,
                                                 self.category_id)
