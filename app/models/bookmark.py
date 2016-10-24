from .. import db
from sqlalchemy import or_, desc, func
from sqlalchemy import UniqueConstraint

class Bookmark(db.Model):
  __tablename__= "bookmark"
  id = db.Column(db.Integer, primary_key=True)
  merchant_id = db.Column(db.Integer)
  listing_id = db.Column(db.Integer)

class BookmarkVendor(db.Model):
  __tablename__ = "bookmarkvendor"
  id = db.Column(db.Integer, primary_key=True)
  merchant_id = db.Column(db.Integer)
  vendor_id = db.Column(db.Integer)
