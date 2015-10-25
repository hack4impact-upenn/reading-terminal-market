from flask import Blueprint

merchant = Blueprint('merchant', __name__)

from . import views  # noqa
