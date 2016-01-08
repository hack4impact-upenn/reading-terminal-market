from flask.ext.login import login_required, current_user
from . import order
from .. import db
from ..models import Order, Status
from flask import abort, jsonify
from ..decorators import merchant_required, vendor_required

# @order.route('/cancel/<int:order_id>', methods=['DELETE'])
# @login_required
# @merchant_required
# def cancel_order(order_id):
#     order = Order.query.get(order_id)
#     if not order or order.merchant_id != current_user.id:
#         abort(404)
#     if order.status != Status.PENDING:
#         abort(400)
#     order.status = Status.CANCELED
#     db.session.commit()
#     # TODO send emails
#     return jsonify({'status': 'canceled'})


@order.route('/approve/<int:order_id>', methods=['PUT'])
@login_required
@vendor_required
def approve_order(order_id):
    order = Order.query.get(order_id)
    if not order or order.vendor_id != current_user.id:
        abort(404)
    if order.status != Status.PENDING:
        abort(400)
    order.status = Status.APPROVED
    db.session.commit()
    # TODO send emails
    return jsonify({'status': 'approved'})

@order.route('/decline/<int:order_id>', methods=['PUT'])
@login_required
@vendor_required
def decline_order(order_id):
    order = Order.query.get(order_id)
    if not order or order.vendor_id != current_user.id:
        abort(404)
    if order.status != Status.PENDING:
        abort(400)
    order.status = Status.DECLINED
    db.session.commit()
    # TODO send emails
    return jsonify({'status': 'declined'})

