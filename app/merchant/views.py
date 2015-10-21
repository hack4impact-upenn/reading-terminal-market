from flask import render_template
from . import merchant
from flask.ext.login import login_required


@merchant.route('/')
@login_required
def index():
    return render_template('main/index.html')
