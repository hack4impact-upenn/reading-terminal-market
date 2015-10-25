from flask import current_app
from .. import db, login_manager

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, unique=True)
    merchant_id = db.Column(db.Integer)

    def __init__(self, listing_id, merchant_id):
        self.listing_id = listing_id
        self.merchant_id = merchant_id

    def __repr__(self):
        return '<Bookmarked Object: %d from Vendor: %d>' % self.listing_id, self.merchant_id