from flask import render_template, abort
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required


@merchant.route('/')
@login_required
@merchant_required
def index():
    return render_template('main/index.html')


@merchant.route('/items/<int:listing_id>')
@merchant.route('/items/<int:listing_id>/info')
@login_required
@merchant_required
def listing_info(listing_id):
    """View a listing's info."""
    """TODO: Create listing's info view for merchants"""
    abort(404)
