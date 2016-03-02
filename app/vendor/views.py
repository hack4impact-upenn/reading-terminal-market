from ..decorators import vendor_required
from app import os
from config import Config
from flask import (
    render_template,
    abort,
    redirect,
    flash,
    url_for,
    send_from_directory,
    jsonify,
    request
)
from flask.ext.login import login_required, current_user
from forms import (ChangeListingInformation, NewItemForm, EditProfileForm)
from . import vendor
from ..models import Listing, Order, Status, User
from .. import db
from ..email import send_email

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

    merchant_id = order.merchant_id
    merchant = User.query.get(merchant_id)

    vendor_name = order.company_name
    purchases = order.purchases

    send_email(merchant.email,
               'Vendor order request approved',
               'vendor/email/approved_order',
               vendor_name=vendor_name,
               order=order,
               purchases=purchases)

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

    merchant_id = order.merchant_id
    merchant = User.query.get(merchant_id)

    vendor_name = order.company_name
    vendor_email = current_user.email
    purchases = order.purchases

    send_email(merchant.email,
               'Vendor order request declined',
               'vendor/email/declined_order',
               vendor_name=vendor_name,
               vendor_email=vendor_email,
               order=order,
               purchases=purchases)

    return jsonify({'order_id': order_id, 'status': 'declined'})


@vendor.route('/profile', methods=['GET'])
@login_required
@vendor_required
def view_profile():
    f1 = Listing.query.filter_by(name=current_user.f1).first()
    f1_ID = f1
    f2 = Listing.query.filter_by(name=current_user.f2).first()
    if f2:
        f2_ID = f2
    else:
        f2_ID = None
    f3 = Listing.query.filter_by(name=current_user.f3).first()
    if f3:
        f3_ID = f3
    else:
        f3_ID = None
    f4 = Listing.query.filter_by(name=current_user.f4).first()
    if f4:
        f4_ID = f4
    else:
        f4_ID = None
    return render_template('vendor/profile.html', vendor=current_user,
                           f1=f1_ID, f2=f2_ID, f3=f3_ID, f4=f4_ID)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


@vendor.route('/picture/<filename>', methods=['GET'])
@login_required
def get_picture(filename):
    c = Config()
    return send_from_directory(c.UPLOAD_FOLDER, filename)


@vendor.route('/suggestions/<search>', methods=['GET'])
@login_required
def get_suggestions(search):
    listings_raw = Listing.search(
        available=True,
        strict_name_search=search,
        sort_by='alphaAZ'
    ).filter_by(vendor_id=current_user.id).limit(10)
    final_arr = []
    for a in listings_raw:
        final_arr.append(a.name)
    return jsonify({'json_list': final_arr});



@vendor.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@vendor_required
def edit_profile():
    form = EditProfileForm()
    c = Config()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        current_user.address = form.address.data
        current_user.phone_number = form.phone_number.data
        current_user.website = form.website.data
        current_user.public_email = form.email.data
        current_user.f1 = form.featured1.data
        current_user.f2 = form.featured2.data
        current_user.f3 = form.featured3.data
        current_user.f4 = form.featured4.data
        current_user.d1 = form.description1.data
        current_user.d2 = form.description2.data
        current_user.d3 = form.description3.data
        current_user.d4 = form.description4.data
        if form.image.data:
            filename = form.image.data.filename
            form.image.data.save(os.path.join(c.UPLOAD_FOLDER, filename))
            current_user.image = filename
        db.session.commit()
        return redirect(url_for('vendor.view_profile'))
    form.bio.data = current_user.bio
    form.address.data = current_user.address
    form.phone_number.data = current_user.phone_number
    form.website.data = current_user.website
    form.email.data = current_user.public_email

    return render_template('vendor/edit_profile.html', form=form)
