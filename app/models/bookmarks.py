from flask import current_app
from .. import db, login_manager

class Bookmarks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, unique=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id')) #also needs to be added to Hunter's Vendors model

    def __init__(self, listing_id, merchant_id):
        self.listing_id = listing_id
        self.merchant_id = merchant_id

    def __repr__(self):
        return "<User: {} Bookmarked Listing: {}".format(self.merchant_id, self.listing_id)
