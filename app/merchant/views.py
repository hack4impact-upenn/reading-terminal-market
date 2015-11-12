from flask import render_template
from . import merchant
from ..decorators import merchant_required
from flask.ext.login import login_required, current_user


@merchant.route('/')
@login_required
@merchant_required
def index():
    return render_template('main/index.html')

@merchant.route('/manage-cart')
@login_required
@merchant_required
def manage_cart():
    # todo : include price, total price, price for quantity
    return render_template('merchant/manage_cart.html', cart=current_user.get_cart())
