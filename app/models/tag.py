from .. import db
from purchase import CartItem
from sqlalchemy import or_, desc, func
from ..models import Category, Vendor, User
from sqlalchemy import UniqueConstraint


class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(64))
    vendors = db.relationship("TagAssociation", back_populates="tag")


class TagAssociation(db.Model):
    __tablename__ = "tagassociation"
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    tag = db.relationship("Tag", back_populates="vendors")
    vendor = db.relationship("Vendor", back_populates="tags")
