from flask import render_template, redirect, request, url_for, flash
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

@merchant.route('/add_to_cart', methods=['POST'])
def add_to_cart(listing_id, quantity_needed):
	listing_name = Listing.query.filter_by(id = listing_id).first();
	cart = Cart.query.filter_by(name=current_user.id).first();
	in_list = False
	for listing in cart:
		if listing.id == listing_id:
			listing.quantity += quantity_needed;
			in_list = True
	if !in_list:
		cart.append({merchant_id=current_user.id, listing_id=listing_id, quantity=quantity_needed});

	db.session.commit();
	flash('Successfully added item {}'.format(listing_name)); #will add in listing name
	return render_template('/');

@merchant.route('/add_to_favorites', methods=['POST'])
def favorite(listing_id):
	bookmarks_list = session.query(bookmarks_table).filter_by(id=current_user.id);
	listing_name = Listing.query.filter_by(id = listing_id).first();
	in_list = False
	for listing in bookmarks_list:
		if listing.id == listing_id:
			in_list = True
	if !in_list:
		bookmarks_table.append({merchant_id = current_user.id, listing_id=listing_id}) #association?

	db.session.commit();
	flash('Successfully added item {}'.format(listing_name)); #will add in listing name
	return render_template('/');
