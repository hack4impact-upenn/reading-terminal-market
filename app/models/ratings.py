from .. import db


class Ratings(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    star_rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    date_reviewed = db.Column(db.DateTime)
