from flask import render_template, redirect, request, url_for, flash
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user


@merchant.route('/')
@login_required
@merchant_required
def index():
    return render_template('merchant/index.html')

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

