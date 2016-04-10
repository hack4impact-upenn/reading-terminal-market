from ..decorators import admin_required

from flask import render_template, abort, redirect, request, flash, url_for
from flask.ext.login import login_required, current_user
import pint

from forms import (
    ChangeUserEmailForm,
    NewUserForm,
    InviteUserForm,

)
from . import admin
from ..models import User, Role, Vendor, Merchant, Listing
from .. import db
from .. vendor.forms import NewCSVForm
from ..email import send_email
import csv
from pint import UnitRegistry, UndefinedUnitError


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


@admin.route('/view-all/')
@admin.route('/view-all/<int:page>')
@login_required
@admin_required
def listing_view_all(page=1):
    """Search for listings"""
    main_search_term = request.args.get('main-search', "", type=str)
    sort_by = request.args.get('sort-by', "", type=str)
    name_search_term = request.args.get('name-search', "", type=str)
    min_price = request.args.get('min-price', "", type=float)
    max_price = request.args.get('max-price', "", type=float)
    avail = request.args.get('avail', "", type=str)
    search = request.args.get('search', "", type=str)
    listings_raw = Listing.search(
        sort_by=sort_by,
        main_search_term=main_search_term,
        avail=avail,
        name_search_term=name_search_term,
        min_price=min_price,
        max_price=max_price,
    )
    print sort_by
    print main_search_term
    # used to reset page count to pg.1 when new search is performed from a page that isn't the first one
    if search != "False":
        page = 1
    listings_paginated_new = listings_raw.paginate(page, 20, False)
    result_count = listings_raw.count()

    if result_count > 0:
        header = "Search Results: {} results in total".format(result_count)
    else:
        header = "No Search Results"

    return render_template(
        'admin/view_listings.html',
        sort_by=sort_by,
        listings=listings_paginated_new,
        main_search_term=main_search_term,
        avail=avail,
        name_search_term=name_search_term,
        min_price=min_price,
        max_price=max_price,
        header=header,
        count=result_count
    )







@admin.route('/category/<int:category_id>/delete')
@login_required
@admin_required
def delete_category(category_id):
    return redirect(url_for('admin.view_categories'))


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        role_choice = form.role.data.name
        if role_choice == 'Vendor':
            user = Vendor(email=form.email.data,
                          first_name=form.first_name.data,
                          company_name=form.company_name.data,
                          last_name=form.last_name.data,
                          password=form.password.data)
        elif role_choice == 'Merchant':
            user = Merchant(email=form.email.data,
                            first_name=form.first_name.data,
                            company_name=form.company_name.data,
                            last_name=form.last_name.data,
                            password=form.password.data)
        elif role_choice == 'Administrator':
            user = User(role=form.role.data,
                        email=form.email.data,
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        password=form.password.data)
        else:
            # invalid selection for user role
            flash('Invalid role selection', 'form-error')
            return render_template('admin/new_user.html', form=form)
        db.session.add(user)
        db.session.commit()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
        return redirect(url_for('admin.new_user'))
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        role_choice = form.role.data.name
        if role_choice == 'Vendor':
            user = Vendor(email=form.email.data)
        elif role_choice == 'Merchant':
            user = Merchant(email=form.email.data)
        elif role_choice == 'Administrator':
            user = User(role=form.role.data,
                        email=form.email.data)
        else:
            # invalid selection for user role
            flash('Invalid role selection', 'form-error')
            return render_template('admin/new_user.html', form=form)

        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,
                   'You Are Invited To Join',
                   'account/email/invite',
                   user=user,
                   user_id=user.id,
                   token=token)

        flash('User successfully invited', 'form-success')
        return redirect(url_for('admin.invite_user'))
    return render_template('admin/new_user.html', form=form)


@admin.route('/users-all/')
@admin.route('/users-all/<int:page>')
@login_required
@admin_required
def registered_users(page=1):
    """View all registered users."""
    main_search_term = request.args.get('main-search', "", type=str)
    sort_by = request.args.get('sort-by', "", type=str)
    company_search_term = request.args.get('company-search', "", type=str)
    user_type = request.args.get('user-type', "", type=str)
    search = request.args.get('search', "", type=str)
    users_raw = User.user_search(
        sort_by=sort_by,
        main_search_term=main_search_term,
        company_search_term=company_search_term,
        user_type=user_type,
    )
    # used to reset page count to pg.1 when new search is performed from a page that isn't the first one
    if search != "False":
        page = 1
    users_paginated = users_raw.paginate(page, 2, False)
    result_count = users_raw.count()
    print result_count

    if result_count > 0:
        header = "Search Results: {} results in total".format(result_count)
    else:
        header = "No Search Results"

    return render_template(
        'admin/registered_users.html',
        sort_by=sort_by,
        main_search_term=main_search_term,
        company_search_term=company_search_term,
        user_type=user_type,
        header=header,
        users=users_paginated,
        count=result_count
    )


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'
              .format(user.full_name(), user.email),
              'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/test-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def test_csv(user_id):
    current_vendor = Vendor.query.filter_by(id=user_id).first()
    if current_vendor is None:
        abort(404)
    form = NewCSVForm()
    if form.validate_on_submit():
        columns = [current_vendor.product_id_col,current_vendor.listing_description_col, current_vendor.unit_col,
                   current_vendor.price_col, current_vendor.name_col, current_vendor.quantity_col]
        csv_file = form.file_upload
        buff = csv_file.data.stream
        csv_data = csv.DictReader(buff, delimiter=',')
        c = current_vendor.product_id_col
        row_count = 0
        for row in csv_data:
            row_count += 1
            for c in columns:
                if c not in row:
                    flash("Error parsing {}'s CSV file. Couldn't find {} column at row {}"
                          .format(current_vendor.full_name(),c, row_count),
                          'form-error')
                    return render_template('admin/manage_user.html', user=current_vendor, form=form)
                if row[current_vendor.product_id_col]=="" and row[current_vendor.listing_description_col]=="":
                    flash("Successfully parsed {}'s CSV file!"
                    .format(current_vendor.full_name()), 'form-success')
                    return render_template('admin/manage_user.html', user=current_vendor, form=form)
            if not(
                is_numeric_col(current_vendor=current_vendor, row=row,
                              col=current_vendor.price_col, row_count=row_count) and
                is_numeric_col(current_vendor=current_vendor, row=row,
                               col=current_vendor.quantity_col,row_count=row_count) and
                is_numeric_col(current_vendor=current_vendor, row=row,
                               col=current_vendor.product_id_col,row_count=row_count)):
                return render_template('admin/manage_user.html', user=current_vendor, form=form)
            if not is_proper_unit(current_vendor.full_name(), current_vendor.unit_col,row, row_count):
                return render_template('admin/manage_user.html', user=current_vendor, form=form)
        flash("Successfully parsed {}'s CSV file!"
          .format(current_vendor.full_name()),
          'form-success')
    return render_template('admin/manage_user.html', user=current_vendor, form=form)


def is_numeric_col(current_vendor, row, col, row_count):
    if not row[col].isdigit() and row[col]:
        flash("Error parsing {}'s CSV file. Bad entry in {} column, at row {} "
              .format(current_vendor.full_name(),col, row_count),
              'form-error')
        return False
    return True


def is_proper_unit(vendor_name, unit, row, row_count):
    ureg = UnitRegistry()
    try:
        ureg.parse_expression(row[unit])
    except UndefinedUnitError:
        flash("Error parsing {}'s CSV file. Bad entry in the {} column, at row {} "
              .format(vendor_name, unit, row_count),'form-error')
        return False
    return True



@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))


@admin.route('/items/<int:listing_id>')
@admin.route('/items/<int:listing_id>/info')
@login_required
@admin_required
def listing_info(listing_id):
    """View a listing's info."""
    listing = Listing.query.filter_by(id=listing_id, available=True).first()
    if listing is None:
        abort(404)

    if 'backto' in request.args:
        backto = request.args.get('backto')
    else:
        backto = url_for('admin.listing_view_all')

    return render_template(
        'shared/listing_info.html',
        listing=listing,
        backto=backto
    )

