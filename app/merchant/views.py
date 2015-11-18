from flask import render_template, flash, abort, request, redirect, url_for
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


@merchant.route('/view/all')
@login_required
@merchant_required
def listing_view_all():
    """Search for listings"""
    listings = Listing.search()
    return render_template('merchant/view_listings.html',
                           listings=listings,
                           header="All listings")


@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    return render_template('merchant/manage_cart.html', cart=current_user.cart_items)


@merchant.route('/items/<int:listing_id>')
@merchant.route('/items/<int:listing_id>/info')
@login_required
@merchant_required
def listing_info(listing_id):
    """View a listing's info."""
    """TODO: Create listing's info view for merchants"""
    abort(404)


@merchant.route('/view/search/<string:search>')
@login_required
@merchant_required
def listing_search(search):
    """Search for listings"""
    listings = Listing.search(term=search)
    return render_template('merchant/view_listings.html',
                           listings=listings,
                           header="Search results for \"{}\"".format(search))


@merchant.route('/add_to_cart')
@login_required
@merchant_required
def add_to_cart():
    current_listing_id = request.args.get('current_listing_id')
    quantity_needed = request.args.get('quantity_needed')
    if not current_listing_id or not quantity_needed:
        return redirect(url_for('.index'))
    listing = Listing.query.filter_by(id=current_listing_id).first()
    cart_item = CartItem.query.filter_by(merchant_id=current_user.id).filter_by(listing_id=current_listing_id).first()

    if cart_item is None:
        db.session.add(CartItem(
            merchant_id=current_user.id,
            listing_id=current_listing_id,
            quantity=quantity_needed
        ))
    else:
        cart_item.quantity = quantity_needed

    db.session.commit()
    flash('Successfully added item {}'.format(listing.name))
    return redirect(url_for('.index'))


@merchant.route('/add_to_favorites', methods=['POST'])
@login_required
@merchant_required
def favorite(listing_id):
    if request.method == 'POST':
        bookmarks_list = db.session.query(bookmarks_table).filter_by(merchant_id=current_user.id)
        listing = Listing.query.filter_by(id=listing_id).first()
        if listing is None:
            abort(404)
        in_list = False
        for listing in bookmarks_list:
            if listing.id == listing_id:
                in_list = True
        if not in_list:
            db.session.add(bookmarks_table(merchant_id=current_user.id, listing_id=listing_id))

        db.session.commit()
        flash('Successfully added item {}'.format(listing.name))
        return render_template('/')
