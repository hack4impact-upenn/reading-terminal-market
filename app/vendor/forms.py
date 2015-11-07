from flask.ext.wtf import Form
from wtforms.fields import StringField, IntegerField, RadioField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms import ValidationError
from ..models import Listing, Category
from .. import db


class ChangeListingInformation(Form):
	categoryId = QuerySelectField('Category', validators=[DataRequired()], get_label='name', query_factory=lambda: db.session.query(Category).order_by('id'))
	listingName = StringField('Item Name', validators=[DataRequired(), Length(1, 1000)])
	listingDescription = StringField('Item Description', validators=[DataRequired(), Length(1, 2500)])
	listingPrice = IntegerField('Item Price', validators=[DataRequired()])
	listingAvailable = BooleanField('Available?')
	submit = SubmitField('Update Item Information')

class NewItemForm(Form):	
	categoryId = QuerySelectField('Category', validators=[DataRequired()], get_label='name', query_factory=lambda: db.session.query(Category).order_by('id'))
	listingName = StringField('Item Name', validators=[DataRequired(), Length(1, 1000)])
	listingDescription = StringField('Item Description', validators=[DataRequired(), Length(1, 2500)])
	listingPrice = IntegerField('Item Price', validators=[DataRequired()])
	listingAvailable = BooleanField('Available?')
	submit = SubmitField('Create New Item')
