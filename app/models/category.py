from .. import db


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    parent = db.relationship("Category", remote_side=[id])

