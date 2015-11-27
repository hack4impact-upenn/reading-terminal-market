from .. import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    unit = db.Column(db.String(32))
    listings = db.relationship("Listing", backref="category")

    def plural(self):
        """ TODO: Return unit in plural form """
        return self.unit

    def singular(self):
        """ TODO: Return unit in singular form """
        return self.unit

    def properPluralization(self, count):
        """ TODO: Return singular/plural form depending on count """
        return self.unit
