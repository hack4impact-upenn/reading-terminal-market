from ..decorators import vendor_required
from flask import (
    render_template,
    abort,
    redirect,
    flash,
    url_for,
    request,
    jsonify,
    json
)
from flask.ext.login import login_required, current_user
from forms import (ChangeListingInformation, NewItemForm, NewCSVForm)
from . import vendor
from ..models import Listing, Order, Status, User
from .. import db
from sqlalchemy import update
import csv


@vendor.route('/')
@login_required
@vendor_required
def index():
    return render_template('vendor/index.html')


@vendor.route('/new-item', methods=['GET', 'POST'])
@login_required
@vendor_required
def new_listing():
    """Create a new item."""
    form = NewItemForm()
    if form.validate_on_submit():
        category_id = form.category_id.data.id
        listing = Listing(
            name=form.listing_name.data,
            description=form.listing_description.data,
            available=True,
            price=form.listing_price.data,
            category_id=category_id,
            vendor_id=current_user.id
        )
        db.session.add(listing)
        db.session.commit()
        flash('Item {} successfully created'.format(listing.name),
              'form-success')
        return redirect(url_for('.new_listing'))
    return render_template('vendor/new_listing.html', form=form)


@vendor.route('/csv-upload', methods=['GET', 'POST'])
@login_required
@vendor_required
def csv_upload():
    """Create a new item."""
    form = NewCSVForm()
    listings = []
    if form.validate_on_submit():
        csv_field = form.file_upload
        buff = csv_field.data.stream
        csv_data = csv.DictReader(buff, delimiter=',')
        #for each row in csv, create a listing
        current_vendor = User.query.filter_by(id=current_user.id).first()
        for row in csv_data:
            print row[current_vendor.product_id_col].strip()
            #cheap way to skip weird 'categorical' lines
            if (row[current_vendor.product_id_col]).strip().isdigit():
                safe_price = stripPriceHelper(row[current_vendor.price_col])
                proposed_listing = Listing(
                            name=row[current_vendor.name_col],
                            description=row[current_vendor.listing_description_col],
                            available=True,
                            price=safe_price,
                            category_id=str(-1),
                            vendor_id=current_user.id,
                            product_id=row[current_vendor.product_id_col],
                            updated=2)
                queried_listing = Listing.query.filter_by(product_id=row[current_vendor.product_id_col]).first()
                if queried_listing:
                    if queried_listing.price == float(safe_price):
                        listings.append(proposed_listing)
                    else:
                        queried_listing.price = float(safe_price)
                        db.session.commit()
                        proposed_listing.updated = 0
                        listings.append(proposed_listing)
                else:
                        proposed_listing.updated = 1
                        listings.append(proposed_listing)
                        db.session.add(proposed_listing)
                        db.session.commit()
    return render_template('vendor/new_csv.html', form=form, listings=listings)

#get rid of those pesky dollar signs that mess up parsing
def stripPriceHelper(price):
    if not price[0].isdigit():
        return price[1:]
    return price




@vendor.route('/itemslist/')
@vendor.route('/itemslist/<int:page>')
@login_required
@vendor_required
def current_listings(page=1):
    """View all current listings."""
    main_search_term = request.args.get('main-search', "", type=str)
    sort_by = request.args.get('sort-by', "", type=str)
    avail = request.args.get('avail', "", type=str)
    search = request.args.get('search', "", type=str)
    listings_raw = Listing.search(
        sort_by=sort_by,
        main_search_term=main_search_term,
        avail=avail
    )
    listings_raw = listings_raw.filter(Listing.vendor_id == current_user.id)

    if search != "False":
        page = 1

    listings_paginated = listings_raw.paginate(page, 20, False)
    result_count = listings_raw.count()

    if result_count > 0:
        header = "Search Results: {} in total".format(result_count)
    else:
        header = "No Search Results"

    return render_template(
        'vendor/current_listings.html',
        listings=listings_paginated,
        main_search_term=main_search_term,
        sort_by=sort_by,
        count=result_count,
        header=header
    )


@vendor.route('/items/<int:listing_id>')
@vendor.route('/items/<int:listing_id>/info')
@login_required
@vendor_required
def listing_info(listing_id):
    """View a listing's info."""
    listing = Listing.query.filter_by(id=listing_id).first()

    if listing is None:
        abort(404)
    elif listing.vendor_id != current_user.id:
        abort(403)

    return render_template('vendor/manage_listing.html', listing=listing)


@vendor.route('/items/<int:listing_id>/edit-item', methods=['GET', 'POST'])
@login_required
@vendor_required
def change_listing_info(listing_id):
    """Change a listings's info."""
    listing = Listing.query.filter_by(
        id=listing_id,
        vendor_id=current_user.id
    ).first()

    if listing is None:
        abort(404)

    form = ChangeListingInformation()
    form.listing_id = listing_id

    if form.validate_on_submit():
        listing.category_id = form.category_id.data.id
        listing.name = form.listing_name.data
        listing.description = form.listing_description.data
        if form.listing_available.data:
            listing.available = True
        else:
            listing.disable_listing()
        listing.price = form.listing_price.data
        listing.vendor_id = current_user.id
        flash('Information for item {} successfully changed.'
              .format(listing.name), 'form-success')

    form.listing_name.default = listing.name
    form.listing_description.default = listing.description
    form.listing_price.default = listing.price
    form.category_id.default = listing.category
    form.listing_available.default = listing.available

    form.process()

    return render_template(
        'vendor/manage_listing.html',
        listing=listing,
        form=form
    )


@vendor.route('/item/<int:listing_id>/delete')
@login_required
@vendor_required
def delete_listing_request(listing_id):
    """Request deletion of an item"""
    listing = Listing.query.filter_by(
        id=listing_id,
        vendor_id=current_user.id
    ).first()
    if listing is None:
        abort(404)
    return render_template('vendor/manage_listing.html', listing=listing)


@vendor.route('/item/<int:listing_id>/_delete')
@login_required
@vendor_required
def delete_listing(listing_id):
    """Delete an item."""
    listing = Listing.query.filter_by(
        id=listing_id,
        vendor_id=current_user.id
    ).first()
    listing.delete_listing()
    flash('Successfully deleted item %s.' % listing.name, 'success')
    return redirect(url_for('vendor.current_listings'))


@vendor.route('/orders')
@login_required
@vendor_required
def view_orders():
    orders = (Order.query.filter_by(vendor_id=current_user.id)
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

    return render_template(
        'vendor/orders.html',
        orders=orders.all(),
        status_filter=status_filter
    )


@vendor.route('/approve/<int:order_id>', methods=['PUT'])
@login_required
@vendor_required
def approve_order(order_id):
    order = Order.query.get(order_id)
    if not order or order.vendor_id != current_user.id:
        abort(404)
    if order.status != Status.PENDING:
        abort(400)
    order.status = Status.APPROVED
    db.session.commit()
    # TODO send emails
    return jsonify({'order_id': order_id, 'status': 'approved'})


@vendor.route('/decline/<int:order_id>', methods=['PUT'])
@login_required
@vendor_required
def decline_order(order_id):
    order = Order.query.get(order_id)
    if not order or order.vendor_id != current_user.id:
        abort(404)
    if order.status != Status.PENDING:
        abort(400)
    order.status = Status.DECLINED
    db.session.commit()
    # TODO send emails
    return jsonify({'order_id': order_id, 'status': 'declined'})
