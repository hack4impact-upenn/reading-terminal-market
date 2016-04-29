from .. import db
from purchase import CartItem
from sqlalchemy import or_, desc, func
from ..models import Vendor
from flask.ext.login import current_user
from sqlalchemy import UniqueConstraint


class Updated:
    PRICE_CHANGE, NEW_ITEM, NO_CHANGE = range(3)


class Listing(db.Model):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint('id', 'name'),
    )

    id = db.Column(db.Integer, primary_key=True)

    # model relationships
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    unit = db.Column(db.String(32))
    quantity = db.Column(db.String(32))
    # listing properties
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    available = db.Column(db.Boolean, default=True)
    product_id=db.Column(db.Integer, default=1)
    updated=db.Column(db.Integer, default=0)

    def __init__(self, product_id, vendor_id, unit, name, available, price,
                 description="", updated=Updated.NO_CHANGE, quantity=0):
        self.product_id = product_id
        self.vendor_id = vendor_id
        self.unit = unit
        self.quantity = quantity
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

    # used in csv parsing
    @staticmethod
    def get_listing_by_product_id(product_id):
        return Listing.query.filter_by(product_id=product_id).first()

    # used in csv parsing.
    # adds to DB a new listing iven params in csv row
    @staticmethod
    def add_csv_row_as_listing(csv_row, price=0):
        return Listing(
                    name=csv_row[current_user.name_col],
                    description=csv_row[current_user.listing_description_col],
                    available=True,
                    price=price,
                    unit=csv_row[current_user.unit_col],
                    quantity= csv_row[current_user.quantity_col],
                    vendor_id=current_user.id,
                    product_id=csv_row[current_user.product_id_col],
                    updated=Updated.PRICE_CHANGE)

    @staticmethod
    def add_listing(new_listing):
        db.session.add(new_listing)
        db.session.commit()

    def update_listing(self, new_product_id):
        self.product_id = new_product_id

    @property
    def category_name(self):
        return self.category_id.name

    @staticmethod
    def search(**kwargs):
        """ Returns all listings matching the criteria """
        filter_list = []
        if 'main_search_term' in kwargs:
            term = kwargs['main_search_term']
            filter_list.append(or_(
                Listing.name.like('%{}%'.format(term)),
                Listing.description.like('%{}%'.format(term)))
            )

        if 'name_search_term' in kwargs and kwargs['name_search_term']:
            term = kwargs['name_search_term']
            vendors = Vendor.query.filter(Vendor.company_name.like('%{}%'.format(term))).all()
            vendor_ids = [vendor.id for vendor in vendors]
            filter_list.append(Listing.vendor_id.in_(vendor_ids))

        # if 'category_search' in kwargs and kwargs['category_search']:
        #     term = kwargs['category_search']
        #     categories = Category.query.filter(Category.name.like('%{}%'.format(term))).all()
        #     category_ids = [category.id for category in categories]
        #     filter_list.append(Listing.category_id.in_(category_ids))

        # used by vendors to filter by availability
        if 'avail' in kwargs:
            avail_criteria = kwargs['avail']
            format(avail_criteria)
            if avail_criteria == "non_avail":
                filter_list.append(Listing.available == False)
            if avail_criteria == "avail":
                filter_list.append(Listing.available == True)
            if avail_criteria == "both":
                filter_list.append(or_(Listing.available == True,
                                       Listing.available == False))

        # used by merchants to filter by availability
        if 'available' in kwargs:
            filter_list.append(Listing.available == True)

        if 'fav_vendor' in kwargs and kwargs['fav_vendor']:
            bookmarked_vendor_ids = [vendor.id for vendor in current_user.bookmarked_vendors]
            filter_list.append(Listing.vendor_id.in_(bookmarked_vendor_ids))

        if 'favorite' in kwargs and kwargs['favorite']:
            bookmark_ids = [listing.id for listing in current_user.bookmarks]
            filter_list.append(Listing.id.in_(bookmark_ids))

        if 'min_price' in kwargs and kwargs['min_price']:
            filter_list.append(Listing.price >= kwargs['min_price'])

        if 'max_price' in kwargs and kwargs['max_price']:
            filter_list.append(Listing.price <= kwargs['max_price'])

        filtered_query = Listing.query.filter(*filter_list)
        print Listing.query.filter(*filter_list)
        if 'sort_by' in kwargs and kwargs['sort_by']:
            sort = kwargs['sort_by']
            format(sort)
        else:
            sort = None

        if sort == "low_high":
            sorted_query = filtered_query.order_by(Listing.price)
        elif sort == "high_low":
            sorted_query = filtered_query.order_by(desc(Listing.price))
        elif sort == "alphaAZ":
            sorted_query = filtered_query.order_by(func.lower(Listing.name))
        elif sort == "alphaZA":
            sorted_query = filtered_query.order_by(desc(func.lower(Listing.name)))
        else:  # default sort
            sorted_query = filtered_query.order_by(Listing.price)
        return sorted_query

    def __repr__(self):
        return "<Listing: {} Vendor: {} Unit: {}>".format(self.name,
                                                              self.vendor_id,
                                                              self.unt)
