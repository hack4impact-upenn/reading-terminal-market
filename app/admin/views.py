from ..decorators import admin_required

from flask import render_template, abort, redirect, flash, url_for
from flask.ext.login import login_required, current_user

from forms import (
    ChangeUserEmailForm,
    NewUserForm,
    InviteUserForm,
    NewCategoryForm
)
from . import admin
from ..models import User, Role, Vendor, Merchant, Category
from .. import db
from ..email import send_email


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


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
    print("ADD CATEGORY LINKED");
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


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/registered_users.html', users=users,
                           roles=roles)


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
