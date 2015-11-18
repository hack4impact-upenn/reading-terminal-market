from flask import render_template, abort
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user
from ..models import Listing


@merchant.route('/')
@login_required
@merchant_required
def index():
    return listing_view_all()


@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    # todo : include price, total price, price for quantity
    return render_template('merchant/manage_cart.html', cart=current_user.get_cart())


@merchant.route('/items/<int:listing_id>')
@merchant.route('/items/<int:listing_id>/info')
@login_required
@merchant_required
def listing_info(listing_id):
    """View a listing's info."""
    """TODO: Create listing's info view for merchants"""
    abort(404)


@merchant.route('/view/all')
@login_required
@merchant_required
def listing_view_all():
    """Search for listings"""
    listings = Listing.search()
    return render_template('merchant/view_listings.html',
                           listings=listings,
                           header="All listings")


@merchant.route('/view/search/<string:search>')
@login_required
@merchant_required
def listing_search(search):
    """Search for listings"""
    listings = Listing.search(term=search)
    return render_template('merchant/view_listings.html',
                           listings=listings,
                           header="Search results for \"{}\"".format(search))
