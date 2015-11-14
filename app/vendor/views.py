from ..decorators import vendor_required

from flask import render_template, abort, redirect, flash, url_for
from flask.ext.login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from forms import (
    ChangeListingInformation,
    NewItemForm
)  
from . import vendor
from ..models import Listing, Category
from .. import db


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


@vendor.route('/items')
@login_required
@vendor_required
def current_listings():
    """View all current listings."""
    listings = current_user.listings.all()
    categories = Category.query.all()
    return render_template('vendor/current_listings.html',
                           listings=listings,
                           categories=categories)


@vendor.route('/items/<int:listing_id>')
@vendor.route('/items/<int:listing_id>/info')
@login_required
@vendor_required
def listing_info(listing_id):
    """View a listing's info."""
    listing = Listing.query.filter_by(id=listing_id, vendor_id=current_user.id).first()
    if listing is None:
        abort(404)
    return render_template('vendor/manage_listing.html', listing=listing)


@vendor.route('/items/<int:listing_id>/edit-item', methods=['GET', 'POST'])
@login_required
@vendor_required
def change_listing_info(listing_id):
    """Change a listings's info."""
    listing = Listing.query.filter_by(id=listing_id, vendor_id=current_user.id).first()
    if listing is None:
        abort(404)
    form = ChangeListingInformation()
    form.listing_id = listing_id
    if form.validate_on_submit():
        listing.category_id = form.category_id.data.id
        listing.name = form.listing_name.data
        listing.description = form.listing_description.data
        listing.available = form.listing_available.data
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
    return render_template('vendor/manage_listing.html', listing=listing, form=form)


@vendor.route('/item/<int:listing_id>/delete')
@login_required
@vendor_required
def delete_listing_request(listing_id):
    """Request deletion of an item"""
    listing = Listing.query.filter_by(id=listing_id, vendor_id=current_user.id).first()
    if listing is None:
        abort(404)
    return render_template('vendor/manage_listing.html', listing=listing)


@vendor.route('/item/<int:listing_id>/_delete')
@login_required
@vendor_required
def delete_listing(listing_id):
    """Delete an item."""
    listing = Listing.query.filter_by(id=listing_id, vendor_id=current_user.id).first()
    db.session.delete(listing)
    db.session.commit()
    flash('Successfully deleted item %s.' % listing.name, 'success')
    return redirect(url_for('vendor.current_listings'))
