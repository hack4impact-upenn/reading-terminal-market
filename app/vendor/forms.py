from flask.ext.wtf import Form
from wtforms.fields import StringField, DecimalField, RadioField, BooleanField, SubmitField, TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from ..models import Category
from .. import db


PRICE_MESSAGE = "This value needs to be filled and needs to be a number"


class ChangeListingInformation(Form):
    categoryId = QuerySelectField('Category',
                                  validators=[DataRequired()],
                                  get_label='name',
                                  query_factory=lambda: db.session.query(Category).order_by('id'))
    listingName = StringField('Item Name',
                              validators=[DataRequired(), Length(1, 1000)])
    listingDescription = TextAreaField('Item Description',
                                       validators=[DataRequired(), Length(1, 2500)])
    listingPrice = DecimalField('Item Price',
                                places=2,
                                validators=[DataRequired(message=PRICE_MESSAGE)])
    listingAvailable = BooleanField('Available?')
    submit = SubmitField('Update Item Information')


class NewItemForm(Form):	
    categoryId = QuerySelectField('Category',
                                  validators=[DataRequired()],
                                  get_label='name',
                                  query_factory=lambda: db.session.query(Category).order_by('id'))
    listingName = StringField('Item Name',
                              validators=[DataRequired(), Length(1, 1000)])
    listingDescription = TextAreaField('Item Description',
                                       validators=[DataRequired(), Length(1, 2500)])
    listingPrice = DecimalField('Item Price',
                                places=2,
                                validators=[DataRequired(message=PRICE_MESSAGE)])
    submit = SubmitField('Create New Item')
