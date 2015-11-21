from flask import render_template, abort, request, redirect, url_for
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user
from ..models import Listing, CartItem
from .. import db
# from forms import SearchForm

from forms import (
    CartQuantityForm
)


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
    # page = request.args.get('page', 1, type=int)
    main_search_term = request.args.get('main-search', "", type=str)
    favorite = True if request.args.get('favorite') == "on" else False
    name_search_term = request.args.get('name-search', "", type=str)
    listings = Listing.search(available=True,
                              favorite=favorite,
                              name_search_term=name_search_term,
                              main_search_term=main_search_term)
    # pagination = Listing.query.paginate(
    #         page, per_page=20,
    #         error_out=False)
    # listings = pagination.items
    return render_template('merchant/view_listings.html',
                           listings=listings,
                           main_search_term=main_search_term,
                           name_search_term=name_search_term,
                           favorite=favorite,
                           cart_listings=current_user.get_cart_listings(),
                           header="All listings")


@merchant.route('/cart-action', methods=['POST'])
@login_required
@merchant_required
def cart_action():
    if request.form['submit'] == "Save Cart":
        for item in current_user.cart_items:
            item.quantity = request.form[str(item.listing_id)]
        db.session.commit()

        return redirect(url_for('.manage_cart'))

    elif request.form['submit'] == "Order Items":
        pass  # order items (dubin)


@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    form = CartQuantityForm()
    print "HELLOOOOOOO?"
    return render_template('merchant/manage_cart.html',
                           cart=current_user.cart_items,
                           form=form)


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
    cart_item = CartItem.query.filter_by(
        merchant_id=current_user.id).filter_by(
        listing_id=current_listing_id).first()

    if listing is None:
        abort(404)

    if cart_item is None:
        db.session.add(CartItem(
            merchant_id=current_user.id,
            listing_id=current_listing_id,
            quantity=quantity_needed
        ))
    else:
        db.session.delete(cart_item)

    db.session.commit()
    return redirect(url_for('.listing_view_all'))


@merchant.route('/add_to_favorites')
@login_required
@merchant_required
def favorite():
    listing_id = request.args.get('listing_id')
    if not listing_id:
        abort(404)
    listing = Listing.query.filter_by(id=listing_id).first_or_404()
    if listing in current_user.bookmarks:
        current_user.bookmarks.remove(listing)
    else:
        current_user.bookmarks.append(listing)
    db.session.commit()
    return redirect(url_for('.listing_view_all'))
