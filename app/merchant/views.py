from flask import render_template, abort, request, redirect, url_for, jsonify
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user
from ..models import Listing, CartItem, Order
from .. import db

from forms import CartQuantityForm


@merchant.route('/')
@login_required
@merchant_required
def index():
    return listing_view_all(1,"")


@merchant.route('/view/all')
@merchant.route('/view/all/<int:page>')
@merchant.route('/view/all/<int:page>/<string:requestlink>')
@login_required
@merchant_required
def listing_view_all(page=1, requestlink=""):
    """Search for listings"""
    main_search_term = request.args.get('main-search', "", type=str)
    favorite = True if request.args.get('favorite') == "on" else False
    sortby = request.args.get('sortby', "", type=str)
    name_search_term = request.args.get('name-search', "", type=str)
    min_price = request.args.get('min-price', "", type=float)
    max_price = request.args.get('max-price', "", type=float)
    listings_raw = Listing.search(available=True,
                                  favorite=favorite,
                                  sortby=sortby,
                                  min_price=min_price,
                                  max_price=max_price,
                                  name_search_term=name_search_term,
                                  main_search_term=main_search_term)
    listings_paginated = listings_raw.paginate(page, 20, False)
    return render_template('merchant/view_listings.html',
                           listings=listings_paginated,
                           main_search_term=main_search_term,
                           min_price=min_price,
                           max_price=max_price,
                           sortby=sortby,
                           name_search_term=name_search_term,
                           favorite=favorite,
                           cart_listings=current_user.get_cart_listings(),
                           header="All listings")


@merchant.route('/cart-action', methods=['POST'])
@login_required
@merchant_required
def cart_action():

    def save_cart():
        for item in current_user.cart_items:
            qty = int(request.form[str(item.listing_id)])
            if qty == 0:
                db.session.delete(item)
            else:
                item.quantity = qty
        db.session.commit()

    if request.form['submit'] == "Save Cart":
        save_cart()
        return redirect(url_for('.manage_cart'))

    elif "Remove" in request.form['submit']:

        remove_id = request.form['submit'].split()[1]

        remove_item = CartItem.query.filter_by(
            merchant_id=current_user.id).filter_by(
                listing_id=remove_id).first()

        db.session.delete(remove_item)
        db.session.commit()
        return redirect(url_for('.manage_cart'))

    elif request.form['submit'] == "Order Items":
        save_cart()
        order = Order(current_user.cart_items)
        db.session.add(order)
        CartItem.delete_cart_items()
        db.session.commit()
        return redirect(url_for('.manage_cart'))


@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    form = CartQuantityForm()
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


@merchant.route('/change_in_cart/<int:listing_id>', methods=["PUT"])
@login_required
@merchant_required
def change_in_cart(listing_id):
    listing = Listing.query.filter_by(id=listing_id).first()
    if not listing:
        abort(404)
    if not request.json:
        abort(400)
    if 'inCart' in request.json and type(request.json['inCart']) is not bool:
        abort(400)
    if ('quantity' in request.json and
            type(request.json['quantity']) is not int):
        abort(400)
    cart_item = CartItem.query.filter_by(merchant_id=current_user.id,
                                         listing_id=listing_id).first()
    quantity = request.json['quantity']
    already_exists = cart_item is not None
    should_be_in_cart = request.json.get('inCart', already_exists)
    if should_be_in_cart and not already_exists:
        db.session.add(CartItem(merchant_id=current_user.id,
                                listing_id=listing_id,
                                quantity=quantity))
    elif should_be_in_cart and already_exists:
        cart_item.quantity = quantity
    elif not should_be_in_cart and already_exists:
        db.session.delete(cart_item)
    db.session.commit()
    name = Listing.query.filter_by(id=listing_id).first().name
    return jsonify({'inCart': should_be_in_cart, 'quantity': quantity, 'name': name})


@merchant.route('/change_favorite/<int:listing_id>', methods=['PUT'])
@login_required
@merchant_required
def change_favorite(listing_id):
    listing = Listing.query.filter_by(id=listing_id).first()
    if not listing:
        abort(404)
    if not request.json:
        abort(400)
    if ('isFavorite' in request.json and
            type(request.json['isFavorite']) is not bool):
        abort(400)
    old_status = listing in current_user.bookmarks
    new_status = request.json.get('isFavorite', old_status)
    if new_status and listing not in current_user.bookmarks:
        current_user.bookmarks.append(listing)
    elif not new_status and listing in current_user.bookmarks:
        current_user.bookmarks.remove(listing)
    db.session.commit()
    return jsonify({'isFavorite': listing in current_user.bookmarks, 'name': listing.name})