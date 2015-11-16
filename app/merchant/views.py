from flask import render_template, redirect, request, url_for, flash
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user
from ..models import Listing, CartItem, bookmarks_table
from .. import db

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

@merchant.route('/add_to_cart', methods=['POST'])
def add_to_cart(current_listing_id, quantity_needed):
    listing = Listing.query.filter_by(id = current_listing_id)[0]
    cart_item_list = CartItem.query.filter_by(merchant_id=current_user.id).filter_by(listing_id=current_listing_id)

    if len(cart_item_list) == 0:
        db.session.add(CartItem(current_user.id, current_listing_id, quantity_needed, listing))
    else:
        cart_item_list[0].quantity += quantity_needed

    db.session.commit()
    flash('Successfully added item {}'.format(listing.name)) #will add in listing name
    return render_template('/')

@merchant.route('/add_to_favorites', methods=['POST'])
def favorite(listing_id):
    bookmarks_list = db.session.query(bookmarks_table).filter_by(merchant_id=current_user.id)
    listing = Listing.query.filter_by(id = listing_id)[0]
    in_list = False
    for listing in bookmarks_list:
        if listing.id == listing_id:
            in_list = True
    if not in_list:
        db.session.add(bookmarks_table(merchant_id=current_user.id, listing_id=listing_id))

    db.session.commit()
    flash('Successfully added item {}'.format(listing.name))
    return render_template('/');
