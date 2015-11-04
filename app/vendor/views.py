from flask import render_template
from . import vendor
from ..decorators import vendor_required
from flask.ext.login import login_required


@vendor.route('/')
@login_required
@vendor_required
def index():
    return render_template('main/index.html')
