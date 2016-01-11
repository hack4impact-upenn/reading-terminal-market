from ..decorators import admin_required

from flask import render_template, abort, redirect, request, flash, url_for
from flask.ext.login import login_required, current_user

from forms import (
    ChangeUserEmailForm,
    NewUserForm,
    InviteUserForm,
    NewCategoryForm
)
from . import admin
from ..models import User, Role, Vendor, Merchant, Category, Listing
from .. import db
from ..email import send_email


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
    category_search = request.args.get('category-search', "", type=str)
    avail = request.args.get('avail', "", type=str)
    search = request.args.get('search', "", type=str)
    listings_raw = Listing.search(
        sort_by=sort_by,
        main_search_term=main_search_term,
        avail=avail,
        name_search_term=name_search_term,
        min_price=min_price,
        max_price=max_price,
        category_search=category_search
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
        category_search=category_search,
        header=header,
        count=result_count
    )


@admin.route('/view-categories')
@login_required
@admin_required
def view_categories():
    """Manage categories availabe to vendors"""
    categories = Category.query.all()
    return render_template('admin/view_categories.html', categories=categories)


@admin.route('/add-category', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = NewCategoryForm()
    if form.validate_on_submit():
        category_name = form.category_name.data
        if Category.query.filter_by(name=category_name).first():
            flash('Category {} already exists'.format(category_name),
                  'form-error')
        else:
            category = Category(name=category_name, unit=form.unit.data)
            db.session.add(category)
            db.session.commit()
            flash('Category {} successfully created'.format(category.name),
                  'form-success')
        return redirect(url_for('admin.add_category'))
    return render_template('admin/add_category.html', form=form)


@admin.route('/category/<int:category_id>/delete')
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    if not category:
        flash('The category you are trying to delete does not exist.', 'error')
    elif len(category.listings) > 0:
        flash('You cannot delete a category with that has listings.', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Successfully deleted category {}.'.format(category.name), 'success')
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
