from flask import render_template, abort, request, redirect, url_for, jsonify
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user
from ..models import Listing, CartItem, Order
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
    main_search_term = request.args.get('main-search', "", type=str)
    favorite = True if request.args.get('favorite') == "on" else False
    name_search_term = request.args.get('name-search', "", type=str)
    min_price = request.args.get('min-price', "", type=float)
    max_price = request.args.get('max-price', "", type=float)
    listings = Listing.search(available=True,
                              favorite=favorite,
                              min_price=min_price,
                              max_price=max_price,
                              name_search_term=name_search_term,
                              main_search_term=main_search_term)

    return render_template('merchant/view_listings.html',
                           listings=listings,
                           main_search_term=main_search_term,
                           min_price=min_price,
                           max_price=max_price,
                           name_search_term=name_search_term,
                           favorite=favorite,
                           cart_listings=current_user.get_cart_listings(),
                           header="All listings")


@merchant.route('/order-items', methods=['POST'])
@login_required
@merchant_required
def order_items():
    order = Order(current_user.cart_items)
    db.session.add(order)
    CartItem.delete_cart_items()
    db.session.commit()
    return redirect(url_for('.manage_cart'))


@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    return render_template('merchant/manage_cart.html',
                           cart=current_user.cart_items)


@merchant.route('/items/<int:listing_id>')
@merchant.route('/items/<int:listing_id>/info')
@login_required
@merchant_required
def listing_info(listing_id):
    """View a listing's info."""
    listing = Listing.query.filter_by(id=listing_id).first()
    if listing is None:
        abort(404)
    item = current_user.get_cart_item(listing_id)
    if item is None:
        quantity = 0
    else:
        quantity = item.quantity

    return render_template('merchant/listing_info.html', listing=listing,
                           quantity=quantity)


@merchant.route('/add_to_cart/<int:listing_id>', methods=["PUT"])
@login_required
@merchant_required
def add_to_cart(listing_id):
    """Adds listing to cart with specified quantity"""
    listing = Listing.query.filter_by(id=listing_id, available=True).first()
    if not listing:
        abort(404)
    if not request.json:
        abort(400)
    if ('quantity' not in request.json or
                type(request.json['quantity']) is not int):
        abort(400)
    cart_item = CartItem.query.filter_by(merchant_id=current_user.id,
                                         listing_id=listing_id).first()
    new_quantity = request.json['quantity']
    is_currently_incart = cart_item is not None

    if new_quantity == 0 and is_currently_incart:
        db.session.delete(cart_item)
    elif new_quantity != 0 and is_currently_incart:
        cart_item.quantity = new_quantity
    elif new_quantity != 0 and not is_currently_incart:
        db.session.add(CartItem(merchant_id=current_user.id,
                                listing_id=listing_id,
                                quantity=new_quantity))
    db.session.commit()
    return jsonify({'quantity': new_quantity})


<<<<<<< HEAD
@merchant.route('/add_quantity_to_cart')
@login_required
@merchant_required
def add_quantity_to_cart():
    listing_id = request.args.get('listing_id')
    quantity = int(request.args.get('quantity'))
    return_to = request.args.get('return_to')
    if not quantity:
        quantity = 0

    if not listing_id:
        return redirect(url_for('.index'))
    listing = Listing.query.filter_by(id=listing_id).first()
    cart_item = CartItem.query.filter_by(
        merchant_id=current_user.id).filter_by(
        listing_id=listing_id).first()

    if listing is None:
        abort(404)

    if cart_item is not None:
        db.session.delete(cart_item)
        db.session.commit()

    if quantity >= 1:
        db.session.add(CartItem(
            merchant_id=current_user.id,
            listing_id=listing_id,
            quantity=quantity
        ))
        db.session.commit()

    if return_to == 'listing_view_all':
        return redirect(url_for('.listing_view_all'))
    elif return_to == 'listing_info':
        return redirect(url_for('.listing_info', listing_id=listing_id))
    else:
        return redirect(url_for('.listing_view_all'))


@merchant.route('/change_favorite/<int:listing_id>', methods=['PUT'])
@login_required
@merchant_required
def change_favorite(listing_id):
    listing = Listing.query.filter_by(id=listing_id).first()
    if not listing:
        abort(404)
    if not request.json:
        abort(400)
    if ('isFavorite' not in request.json or
                type(request.json['isFavorite']) is not bool):
        abort(400)
    old_status = listing in current_user.bookmarks
    new_status = request.json.get('isFavorite', old_status)
    if new_status and listing not in current_user.bookmarks:
        current_user.bookmarks.append(listing)
    elif not new_status and listing in current_user.bookmarks:
        current_user.bookmarks.remove(listing)
    db.session.commit()
    return jsonify({'isFavorite': listing in current_user.bookmarks})
