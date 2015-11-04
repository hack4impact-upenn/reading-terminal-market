from flask import current_app
from .. import db, login_manager

class Bookmarks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, unique=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    merchant = db.relationship('User', backref=db.backref('bookmarks', lazy='dynamic'))

    def __init__(self, listing_id, merchant):
        self.listing_id = listing_id
        self.merchant = merchant

    def __repr__(self):
        return "<User: {} Bookmarked Listing: {}".format(self.merchant_id, self.listing_id)
