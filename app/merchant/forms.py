from flask.ext.wtf import Form
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired


class CartQuantityForm(Form):
    quantity = IntegerField('Quantity', validators=[
        InputRequired(),
    ])
