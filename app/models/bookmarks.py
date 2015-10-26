from flask import current_app
from .. import db, login_manager

class Bookmarks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, unique=True)
    merchant_id = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer, db.ForeignKey('person.id')) #also needs to be added to Hunter's Vendors model

    def __init__(self, listing_id, merchant_id, vendor_id):
        self.listing_id = listing_id
        self.merchant_id = merchant_id
        self.vendor_id = vendor_id

    def __repr__(self):
        return '<User: %d Bookmarked Object: %d from Vendor: %d>' % self.vendor_id, self.listing_id, self.merchant_id