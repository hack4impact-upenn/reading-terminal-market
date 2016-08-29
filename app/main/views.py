from flask import redirect, url_for
from . import main
from flask.ext.login import current_user


@main.route('/')
def index():
    if current_user.is_merchant():
        return redirect(url_for('merchant.index'))
    elif current_user.is_admin():
        return redirect(url_for('admin.index'))
    elif current_user.is_vendor():
        return redirect(url_for('vendor.index'))
    else:
        return redirect(url_for('account.login'))
