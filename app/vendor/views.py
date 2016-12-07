from threading import Thread
from ..decorators import vendor_required
from app import os, create_app
import app
import boto
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
import json
from flask.ext.login import login_required, current_user
from forms import (ChangeListingInformation, NewItemForm, NewCSVForm, EditProfileForm)
from . import vendor
from ..models import Listing, Order, Status, User
from ..models.listing import Updated
from ..models.user import Vendor
import csv
import re
import copy
from .. import db
from ..email import send_email
from flask.ext.rq import get_queue
from werkzeug.utils import secure_filename
from uuid import uuid4
from pint import UnitRegistry, UndefinedUnitError

@vendor.route('/')
@login_required
@vendor_required
def index():
    tut_completed = User.query.filter_by(id=current_user.id).first().tutorial_completed
    return render_template('vendor/index.html', tut_completed=tut_completed)


@vendor.route('/tutorial_completed', methods=['POST'])
@login_required
@vendor_required
def tutorial_completed():
    current_tutorial_status = User.query.filter_by(id=current_user.id).first().tutorial_completed;
    User.query.filter_by(id=current_user.id).first().tutorial_completed = \
        not User.query.filter_by(id=current_user.id).first().tutorial_completed;
    db.session.commit();
    return '', 204


@vendor.route('/new-item', methods=['GET', 'POST'])
@login_required
@vendor_required
def new_listing():
    tut_completed = User.query.filter_by(id=current_user.id).first().tutorial_completed
    """Create a new item."""
    form = NewItemForm()
    if form.validate_on_submit():
        listing = Listing(
            name=form.listing_name.data,
            description=form.listing_description.data,
            available=True,
            unit= form.listing_unit.data,
            quantity= form.listing_quantity.data,
            price=form.listing_price.data,
            vendor_id=current_user.id,
            product_id=form.listing_productID.data
        )
        db.session.add(listing)
        db.session.commit()
        flash('Item {} successfully created'.format(listing.name),
              'form-success')
        return redirect(url_for('.new_listing', tut_completed=tut_completed))
    return render_template('vendor/new_listing.html', form=form, tut_completed=tut_completed)

def isclose(a, b, rel_tol=1e-09, abs_tol=0.000001):
    b = float(b)
    print "ABS", abs(a-b)
    print "MAX", max(rel_tol * max(abs(a), abs(b)), abs_tol)
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

@vendor.route('/csv-row-upload', methods=['POST'])
@login_required
@vendor_required
def row_upload():
    data = json.loads(request.form['json'])
    print data
    if data['action'] == 'replace':
        listings_delete = db.session.query(Listing).filter_by(vendor_id = current_user.id)
        if listings_delete.first():
            listings_delete.first().delete_listing()
        return jsonify({"status": "Prep", "message": "Prepared current items for replacement. {} left".format(listings_delete.count())})
    if data['action'] == 'add':
        row = data['row']
        name = row['name']
        description = row['description']
        unit = row['unit']
        quantity = row['quantity']
        price = row['price']
        print name, description, unit, quantity, price

        print re.findall("\d+\.\d+", price)

        formatted_raw_price = re.findall("\d+\.*\d*", price)
        product_id = row['productId']

        if not (is_number(formatted_raw_price)):
            message_string = ("Skipping {} (Product Id: {}), due to fact that price was unable to be interpreted as a number. Found {}".
                format(name, product_id, price))
            return jsonify({"status": "Failure", "message": message_string})

        formatted_price = re.findall("\d+\.*\d*", price)[0]

        queried_listing = Listing.query.filter_by(product_id=product_id, vendor_id = current_user.id).first()
        if queried_listing:
            changed = False
            if queried_listing.name != name:
                print "name"
                changed = True
                queried_listing.name = name
            if queried_listing.description != description:
                print "desc"
                changed = True
                queried_listing.description = description
            if queried_listing.unit != unit:
                print "unit"
                changed = True
                queried_listing.unit = unit
            if queried_listing.quantity != quantity:
                print "quantity"
                changed = True
                queried_listing.quantity = quantity
            if (isclose(queried_listing.price,formatted_price)) == False:
                changed = True
                queried_listing.price = formatted_price
            if changed is True:
                queried_listing.available = True
                db.session.commit()
                return jsonify({"status": "Success", "message": "Successfully merged {} (Product Id: {}) with price ${}".format(name, product_id, formatted_price)})
            else:
                return jsonify({"status": "Prep", "message": "No change {} (Product Id: {})".format(name, product_id)})
        else:
            Listing.add_listing(Listing(product_id, current_user.id, unit, name, True, formatted_price, description, Updated.NEW_ITEM, quantity))
            return jsonify({"status": "Success", "message": "Successfully added {} (Product Id: {}) with price ${}".format(name, product_id, formatted_price)})

@vendor.route('/csv-upload', methods=['GET', 'POST'])
@login_required
@vendor_required
def csv_upload():
    tut_completed = User.query.filter_by(id=current_user.id).first().tutorial_completed
    """Create a new item."""
    form = NewCSVForm()
    listings = []
    count = db.session.query(Listing).filter_by(vendor_id = current_user.id).count()
    current_row = 0
    if form.validate_on_submit():
        if test_csv(form):
            csv_field = form.file_upload
            buff = csv_field.data.stream
            buff.seek(0)
            csv_data = csv.DictReader(buff, delimiter=',')
            #for each row in csv, create a listing
            current_vendor = Vendor.get_vendor_by_user_id(user_id=current_user.id)
            if form.replace_or_merge.data == 'replace':
                listings_delete = db.session.query(Listing).filter_by(vendor_id=current_user.id).all()
                for listing in listings_delete:
                    listing.available = False
            for row in csv_data:
                #cheap way to skip weird 'categorical' lines
                if (row[current_vendor.product_id_col]).strip().isdigit() and form.replace_or_merge.data == 'merge':
                    safe_price = row[current_vendor.price_col]
                    description = row[current_vendor.listing_description_col]
                    name = row[current_vendor.name_col]
                    unit = row[current_vendor.unit_col]
                    quantity = row[current_vendor.quantity_col]
                    proposed_listing = Listing.add_csv_row_as_listing(csv_row=row, price=safe_price)
                    queried_listing = Listing.get_listing_by_product_id(product_id=row[current_vendor.product_id_col])
                    if queried_listing:
                        # case: listing exists and price has not changed
                        queried_listing.available = True
                        if (
                            queried_listing.price == float(safe_price)
                            and queried_listing.description == description
                            and queried_listing.name == name
                            and queried_listing.unit == unit
                            and queried_listing.quantity == quantity):
                            proposed_listing.updated = Updated.NO_CHANGE
                            listings.append(proposed_listing)
                        # case: listing exists and price has changed
                        else:
                            queried_listing.price = float(safe_price)
                            proposed_listing.price = float(safe_price)
                            proposed_listing.description = description
                            proposed_listing.name = name
                            proposed_listing.unit = unit
                            proposed_listing.quantity = quantity
                            proposed_listing.updated = Updated.PRICE_CHANGE
                            listings.append(proposed_listing)
                            db.session.commit()
                        #case: listing does not yet exist
                    else:
                        proposed_listing.updated = Updated.NEW_ITEM
                        listings.append(proposed_listing)
                        Listing.add_listing(new_listing=proposed_listing)
                elif (row[current_vendor.product_id_col]).strip().isdigit() and form.replace_or_merge.data == 'replace':
                    safe_price = row[current_vendor.price_col]
                    proposed_listing = Listing.add_csv_row_as_listing(csv_row=row, price=safe_price)
                    proposed_listing.updated = Updated.NEW_ITEM
                    listings.append(proposed_listing)
                    Listing.add_listing(new_listing=proposed_listing)
    return render_template('vendor/new_csv.html', tut_completed=tut_completed, form=form, listings=listings, count=count)

#get rid of those pesky dollar signs that mess up parsing
def stripPriceHelper(price):
    r = re.compile("\$(\d+.\d+)")
    return r.search(price.replace(',','')).group(1)

def is_number(s):
    if len(s) == 0:
        return False
    try:
        complex(s[0]) # for int, long, float and complex
    except ValueError:
        return False

    return True
def is_numeric_col(current_vendor, row, col, row_count):
    if not is_number(row[col]) and row[col]:
        flash("Error parsing {}'s CSV file. Bad entry in {} column, at row {}. Must be number (no letters/characters). Found <b>{}</b>"
              .format(current_vendor.full_name(),col, row_count, row[col]),
              'form-error')
        return False
    return True


def is_proper_unit(vendor_name, unit, row, row_count):
    return True

@vendor_required
def test_csv(form):
    current_vendor = Vendor.get_vendor_by_user_id(user_id=current_user.id)
    if current_vendor is None:
        abort(404)
    columns = [current_vendor.product_id_col,current_vendor.listing_description_col, current_vendor.unit_col,
               current_vendor.price_col, current_vendor.name_col, current_vendor.quantity_col]
    csv_file = form.file_upload
    print csv_file.data.filename
    if '.csv' not in csv_file.data.filename: 
        flash("Must be a .csv file", 'form-error')
        return False
    buff = csv_file.data.stream
    csv_data = csv.DictReader(buff, delimiter=',')
    c = current_vendor.product_id_col
    row_count = 0
    for row in csv_data:
        if len(row.keys()) > 1:
            row_count += 1
            for c in columns:
                    if c not in row:
                        flash("Error parsing {}'s CSV file. Couldn't find {} column at row {}"
                              .format(current_vendor.full_name(),c, row_count),
                              'form-error')
                        return False
                    if row[current_vendor.product_id_col]=="" and row[current_vendor.listing_description_col]=="":
                        flash("Successfully parsed {}'s CSV file!"
                        .format(current_vendor.full_name()), 'form-success')
                        return True
            if not(
                is_numeric_col(current_vendor=current_vendor, row=row,
                              col=current_vendor.price_col, row_count=row_count) and
                is_numeric_col(current_vendor=current_vendor, row=row,
                               col=current_vendor.quantity_col,row_count=row_count) and
                is_numeric_col(current_vendor=current_vendor, row=row,
                               col=current_vendor.product_id_col,row_count=row_count)):
                return False
            if not is_proper_unit(current_vendor.full_name(), current_vendor.unit_col,row, row_count):
                return False
    return True


@vendor.route('/itemslist/')
@vendor.route('/itemslist/<int:page>')
@login_required
@vendor_required
def current_listings(page=1):
    """View all current listings."""
    tut_completed = User.query.filter_by(id=current_user.id).first().tutorial_completed
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

    listings_paginated = listings_raw.paginate(page, 21, False)
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
        header=header,
        tut_completed=tut_completed
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
        listing.name = form.listing_name.data
        listing.description = form.listing_description.data
        listing.unit = form.listing_unit.data
        listing.quantity = form.listing_quantity.data
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
    form.listing_unit.default = listing.unit
    form.listing_quantity.default = listing.quantity
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


@vendor.route('/approve/<int:order_id>', methods=['POST'])
@login_required
@vendor_required
def approve_order(order_id):
    order = Order.query.filter_by(id = order_id).first()
    if not order or order.vendor_id != current_user.id:
        abort(404)
    if order.status != Status.PENDING:
        abort(400)
    order.status = Status.APPROVED
    order.comment = request.json['comment']
    db.session.commit()

    merchant_id = order.merchant_id
    merchant = User.query.filter_by(id=merchant_id).first()

    vendor_name = order.company_name
    purchases = order.purchases
    comment = order.comment
    send_email(merchant.email,
               'Vendor order request approved',
               'vendor/email/approved_order',
               vendor_name=vendor_name,
               order=order,
               purchases=purchases,
               comment=comment)

    return jsonify({'order_id': order_id, 'status': 'approved', 'comment': comment})
    

@vendor.route('/decline/<int:order_id>', methods=['POST'])
@login_required
@vendor_required
def decline_order(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order or order.vendor_id != current_user.id:
        abort(404)
    if order.status != Status.PENDING:
        abort(400)
    order.status = Status.DECLINED
    order.comment = request.json['comment']
    db.session.commit()

    merchant_id = order.merchant_id
    merchant = User.query.filter_by(id=merchant_id).first()
    vendor_name = order.company_name
    vendor_email = current_user.email
    purchases = order.purchases
    comment = order.comment
    send_email(merchant.email,
               'Vendor order request declined',
               'vendor/email/declined_order',
               vendor_name=vendor_name,
               vendor_email=vendor_email,
               order=order,
               purchases=purchases,
               comment=comment)
    return jsonify({'order_id': order_id, 'status': 'declined', 'comment': comment})

@vendor.route('/profile', methods=['GET'])
@login_required
@vendor_required
def view_profile():
    return render_template('vendor/profile.html', vendor=current_user)

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
        if form.image.data:
            filename = form.image.data.filename
            get_queue().enqueue(process_image, 
                                type='image',
                                filename=filename,
                                data =form.image.data.read(),
                                user_id=current_user.id)
        if form.pdf.data:
            filename = form.pdf.data.filename
            get_queue().enqueue(process_image, 
                                type='pdf',
                                filename=filename,
                                data =form.pdf.data.read(),
                                user_id=current_user.id)
        db.session.commit()
        return redirect(url_for('vendor.view_profile'))
    form.bio.data = current_user.bio
    form.address.data = current_user.address
    form.phone_number.data = current_user.phone_number
    form.website.data = current_user.website
    form.email.data = current_user.public_email
    form.featured1.data = current_user.f1
    return render_template('vendor/edit_profile.html', form=form)

def process_image(filename, type, data, user_id):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        source_filename = secure_filename(filename)
        source_extension = os.path.splitext(source_filename)[1]

        destination_filename = uuid4().hex + source_extension
        conn = boto.connect_s3(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"])
        b = conn.get_bucket(os.environ["S3_BUCKET"])
        sml = b.new_key("/".join([destination_filename]))
        sml.set_contents_from_string(data)
        sml.set_acl('public-read')
        
        user = User.query.filter_by(id=user_id).first()
        if type == 'image': 
            user.image = 'https://s3-us-west-2.amazonaws.com/{}/{}'.format(os.environ["S3_BUCKET"], destination_filename)
        if type == 'pdf':
            user.pdf = 'https://s3-us-west-2.amazonaws.com/{}/{}'.format(os.environ["S3_BUCKET"], destination_filename)
        db.session.commit()
