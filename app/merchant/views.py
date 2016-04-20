from flask import render_template, abort, request, redirect, url_for, jsonify, flash
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user
from ..models import Listing, CartItem, Order, Vendor, Status, Ratings
from .. import db
from datetime import datetime
import pytz


@merchant.route('/')
@login_required
@merchant_required
def index():
    return listing_view_all()


@merchant.route('/view/all')
@merchant.route('/view/all/<int:page>')
@login_required
@merchant_required
def listing_view_all(page=1):
    """Search for listings"""
    main_search_term = request.args.get('main-search', "", type=str)
    favorite = True if request.args.get('favorite') == "on" else False
    fav_vendor = True if request.args.get('fav_vendor') == "on" else False
    sort_by = request.args.get('sortby', "", type=str)
    name_search_term = request.args.get('name-search', "", type=str)
    min_price = request.args.get('min-price', "", type=float)
    max_price = request.args.get('max-price', "", type=float)
    category_search = request.args.get('category-search', "", type=str)
    search = request.args.get('search', "", type=str)
    listings_raw = Listing.search(
        available=True,
        favorite=favorite,
        fav_vendor=fav_vendor,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price,
        name_search_term=name_search_term,
        main_search_term=main_search_term,
        category_search=category_search
    )
    # used to reset page count to pg.1 when new search is performed from a page
    # that isn't the first one

    if search != "False":
        page = 1

    listings_paginated = listings_raw.paginate(page, 20, False)
    result_count = listings_raw.count()

    if result_count > 0:
        header = "Search Results: {} results in total".format(result_count)
    else:
        header = "No Search Results"

    return render_template(
        'merchant/view_listings.html',
        listings=listings_paginated,
        main_search_term=main_search_term,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        name_search_term=name_search_term,
        fav_vendor=fav_vendor,
        favorite=favorite,
        category_search=category_search,
        cart_listings=current_user.get_cart_listings(),
        header=header,
        count=result_count
    )


@merchant.route('/order-items/', methods=['POST'])
@merchant.route('/order-items/<int:vendor_id>', methods=['POST'])
@login_required
@merchant_required
def order_items(vendor_id=None):
    if vendor_id:
        Order.order_cart_items_from_vendor(vendor_id)
    else:
        Order.order_cart_items()
    return redirect(url_for('.manage_cart'))


@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    # used to show/hide the order modal
    confirm_order = request.args.get('confirm_order', default=False, type=bool)
    # vendor_id to order from. if None, order from all
    vendor_id = request.args.get('vendor_id', type=int)
    if vendor_id not in CartItem.get_vendor_ids():
        vendor = None
    else:
        vendor = Vendor.query.get(vendor_id)

    vendor_items_dict = CartItem.get_vendor_cart_items_dict()
    return render_template(
        'merchant/manage_cart.html',
        vendor_items_dict=vendor_items_dict,
        confirm_order=confirm_order,
        vendor=vendor,
        get_total_price=CartItem.get_total_price
    )


@merchant.route('/items/<int:listing_id>')
@merchant.route('/items/<int:listing_id>/info')
@login_required
@merchant_required
def listing_info(listing_id):
    """View a listing's info."""
    listing = Listing.query.filter_by(id=listing_id, available=True).first()
    if listing is None:
        abort(404)
    item = current_user.get_cart_item(listing_id)
    if item is None:
        quantity = 0
    else:
        quantity = item.quantity

    if 'backto' in request.args:
        backto = request.args.get('backto')
    else:
        backto = url_for('merchant.listing_view_all')

    if 'cart' in backto:
        backto_text = 'cart'
    else:
        backto_text = 'listings'

    return render_template(
        'shared/listing_info.html',
        listing=listing,
        quantity=quantity,
        backto=backto,
        backto_text=backto_text
    )


@merchant.route('/items/<int:listing_id>/reviews')
@merchant.route('/items/<int:listing_id>/info/reviews')
@login_required
@merchant_required
def review_info(listing_id, page=1):
    """View all ratings for Vendor selling the listing"""
    listing = Listing.query.filter_by(id=listing_id, available=True).first()
    if listing is None:
        abort(404)

    page = request.args.get('page', 1, type=int)
    ratings_raw = listing.vendor.get_ratings_query()
    ratings_paginated = ratings_raw.paginate(page, 3, False)

    ratings_breakdown = listing.vendor.get_ratings_breakdown()
    total_num_ratings = sum(ratings_breakdown.values())

    backto = url_for('merchant.listing_info', listing_id=listing_id)

    return render_template(
        'merchant/view_reviews.html',
        listing=listing,
        backto=backto,
        ratings=ratings_paginated,
        ratings_breakdown=ratings_breakdown,
        total_num_ratings=total_num_ratings
    )


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
    if 'quantity' not in request.json or type(request.json[
                                                  'quantity']) is not int:
        abort(400)

    cart_item = CartItem.query.filter_by(
        merchant_id=current_user.id,
        listing_id=listing_id
    ).first()

    new_quantity = request.json['quantity']
    is_currently_incart = cart_item is not None

    if new_quantity == 0 and is_currently_incart:
        db.session.delete(cart_item)
    elif new_quantity != 0 and is_currently_incart:
        cart_item.quantity = new_quantity
    elif new_quantity != 0 and not is_currently_incart:
        db.session.add(
            CartItem(
                merchant_id=current_user.id,
                listing_id=listing_id,
                quantity=new_quantity
            )
        )
    db.session.commit()
    name = Listing.query.filter_by(id=listing_id).first().name
    return jsonify({'quantity': new_quantity, 'name': name})


@merchant.route('/change_favorite/<int:listing_id>', methods=['PUT'])
@login_required
@merchant_required
def change_favorite(listing_id):
    listing = Listing.query.filter_by(id=listing_id).first()
    if not listing:
        abort(404)
    if not request.json:
        abort(400)
    if 'isFavorite' not in request.json or type(request.json['isFavorite']) is not bool:
        abort(400)

    old_status = listing in current_user.bookmarks
    new_status = request.json.get('isFavorite', old_status)
    if new_status and listing not in current_user.bookmarks:
        current_user.bookmarks.append(listing)
    elif not new_status and listing in current_user.bookmarks:
        current_user.bookmarks.remove(listing)
    db.session.commit()
    return jsonify(
        {'isFavorite': listing in current_user.bookmarks, 'name': listing.name}
    )


@merchant.route('/change-fav-vendor/<int:vendor_id>', methods=['PUT'])
@login_required
@merchant_required
def change_fav_vendor(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id).first()
    if not vendor:
        abort(404)
    if not request.json:
        abort(400)
    if 'isFavVendor' not in request.json or type(request.json['isFavVendor']) is not bool:
        abort(400)

    old_status = vendor in current_user.bookmarked_vendors
    new_status = request.json.get('isFavVendor', old_status)
    if new_status and vendor not in current_user.bookmarked_vendors:
        print current_user.bookmarked_vendors
        current_user.bookmarked_vendors.append(vendor)
    elif not new_status and vendor in current_user.bookmarked_vendors:
        current_user.bookmarked_vendors.remove(vendor)
    db.session.commit()
    return jsonify(
        {'isFavVendor': vendor in current_user.bookmarked_vendors,
         'vendor_id': vendor.id,
         'name': vendor.company_name }
    )


@merchant.route('/orders')
@login_required
@merchant_required
def view_orders():
    orders = (Order.query.filter_by(merchant_id=current_user.id)
              .order_by(Order.id.desc()))

    status_filter = request.args.get('status')

    if status_filter == 'approved':
        orders = orders.filter_by(status=Status.APPROVED)
    elif status_filter == 'declined':
        orders = orders.filter_by(status=Status.DECLINED)
    elif status_filter == 'pending':
        orders = orders.filter_by(status=Status.PENDING)
    else:
        status_filter = None

    ratings = Ratings.query.filter_by(merchant_id=current_user.id).all()
    rating_dict = {rating.vendor_id: rating for rating in ratings}

    return render_template(
        'merchant/orders.html',
        orders=orders.all(),
        status_filter=status_filter,
        ratings=rating_dict
    )


@merchant.route('/orders/<int:order_id>', methods=['POST'])
@login_required
@merchant_required
def review_orders(order_id):
    order = Order.query.get(order_id)
    star_rating = request.json['rating']
    comment = request.json['review']

    # TODO: flash on orders page
    if not comment or star_rating == 0:
        flash('Minimum 1 star rating and review mandatory', 'error')
        return redirect(url_for('.view_orders'))

    rating = Ratings.query.filter_by(vendor_id=order.vendor_id, merchant_id=order.merchant_id).first()
    if not rating:
        rating = Ratings(
            vendor_id=order.vendor_id,
            merchant_id=order.merchant_id,
            star_rating=star_rating,
            comment=comment,
            date_reviewed=datetime.now()
            )
        db.session.add(rating)
        db.session.commit()
    else:
        rating.star_rating = star_rating
        rating.comment = comment
        rating.date_reviewed = datetime.now()
        db.session.commit()

    return jsonify({'order_id': order_id, 'rating': star_rating,
                    'comment': comment, 'vendor id': order.vendor_id,
                    'date_reviewed': rating.get_date()})
