# from .. import db
#
#
# class Cart(db.Model):
#
#     merchant_id
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), unique=True)
#     unit = db.Column(db.String(32))
#     listings = db.relationship("Listing", backref="category")
