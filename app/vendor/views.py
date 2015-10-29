from flask import render_template
from . import vendor
from flask.ext.login import login_required


@vendor.route('/')
@login_required
def index():
    return render_template('main/index.html')
