from .. import db


class Ratings(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    star_rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    date_reviewed = db.Column(db.DateTime)

    def get_date(self):
        """Get date formatted as mm-dd-yyyy"""
        date = self.date_reviewed.date()
        return '{}-{}-{}'.format(date.month, date.day, date.year)

    def __repr__(self):
        return "<Rating: id {}, vendor_id {}, merchant_id {}, star_rating {}, \
        comment {}, date_reviewed {} \n>".format(self.id,
                                                 self.vendor_id,
                                                 self.merchant_id,
                                                 self.star_rating,
                                                 self.comment,
                                                 self.date_reviewed)
