from .. import db
from purchase import CartItem
from sqlalchemy import or_
from user import Vendor
from flask.ext.login import current_user


class Listing(db.Model):
    __tablename__ = "listings"
    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # listing properties
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    available = db.Column(db.Boolean, default=True)

    def __init__(self, vendor_id, name, available, category_id, price,
                 description=""):
        self.vendor_id = vendor_id
        self.category_id = category_id
        self.name = name
        self.description = description
        self.price = price
        self.available = available

    def remove_from_carts(self):
        cart_items = CartItem.query.filter_by(listing_id=self.id).all()
        for cart_item in cart_items:
            db.session.delete(cart_item)
        db.session.commit()

    def get_quantity_in_cart(self):
        cart_item = CartItem.query.filter_by(merchant_id=current_user.id,
                                              listing_id=self.id).first()
        if cart_item:
            return cart_item.quantity
        else:
            return 0

    def disable_listing(self):
        """Disable the listing and remove from all carts"""
        self.available = False
        self.remove_from_carts()
        db.session.commit()

    def delete_listing(self):
        """Delete the listing and remove from all carts"""
        self.remove_from_carts()
        db.session.delete(self)
        db.session.commit()

    @property
    def category_name(self):
        return self.category_id.name

    @staticmethod
    def search(**kwargs):
        """ Returns all listings matching the criteria """
        filter_list = []
        name = "%"
        vendor = "%"
        if 'main_search_term' in kwargs:
            term = kwargs['main_search_term']
            name = '%{}%'.format(term)
            filter_list.append(or_(
                Listing.name.like('%{}%'.format(term)),
                Listing.description.like('%{}%'.format(term)))
            )
        if 'name_search_term' in kwargs:
            term = kwargs['name_search_term']
            vendor = '%{}%'.format(term)
            filter_list.append(or_(
                # Vendor.first_name.like('%{}%'.format(term)),
                # Vendor.last_name.like('%{}%'.format(term)),
                Vendor.company_name.like('%{}%'.format(term)))
            )
        if 'available' in kwargs:
            filter_list.append(Listing.available == kwargs['available'])
        pricemin = 0
        # pricemax some arbitrarily large number to ensure all price are shown unless a user specifies a price
        pricemax = 1000000
        bookmark_ids = [listing.id for listing in Listing.query.all()]
        sort_criteria = None
        if 'favorite' in kwargs and kwargs['favorite']:
            bookmark_ids = [listing.id for listing in current_user.bookmarks]
            # filter_list.append(Listing.id.in_(bookmark_ids))
        if 'min_price' in kwargs and kwargs['min_price']:
            pricemin = kwargs['min_price']
            # filter_list.append(Listing.price >= float(format(price)))
        if 'max_price' in kwargs and kwargs['max_price']:
            pricemax = kwargs['max_price']
            # filter_list.append(Listing.price <= float(format(price)))
        if 'sortby' in kwargs and kwargs['sortby']:
            sort = kwargs['sortby']
            format(sort)
            if sort == "low_high":
                sort_criteria = 'price'
            elif sort == "high_low":
                sort_criteria = 'price desc'
            elif sort == "alphaAZ":
                sort_criteria = 'name'
            else:
                sort_criteria = 'name desc'
        print name
        initFilter = Listing.query.filter((Listing.price >= pricemin)
                                    & (Listing.price <= pricemax)
                                    & (Listing.id.in_(bookmark_ids))
                                    & (Listing.available == True) &
                                    or_((Listing.name.like(name)),
                                    (Listing.description.like(name))),
                                    or_(
                                        # Need to find way to get access to vendor names
                                        # Vendor.first_name.like(vendor),
                                        # Vendor.last_name.like(vendor),
                                        Vendor.company_name.like(vendor))
                                    )

        finalFilter = initFilter.order_by(sort_criteria)
        return finalFilter

    def __repr__(self):
        return "<Listing: {} Vendor: {} Category: {}>".format(self.name,
                                                              self.vendor_id,
                                                              self.category_id)