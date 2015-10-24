from .. import db


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    parent = db.relationship("Categories", remote_side=[id])
