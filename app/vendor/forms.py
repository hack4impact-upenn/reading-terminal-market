from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms.fields import StringField, DecimalField, BooleanField, SubmitField, TextAreaField, FileField, IntegerField, RadioField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Regexp
from wtforms import ValidationError, widgets, SelectMultipleField
from ..models import Listing, User
from .. import db


PRICE_MESSAGE = "This value needs to be filled and needs to be a number"


class ChangeListingInformation(Form):
    listing_name = StringField('Item Name', validators=[DataRequired(), Length(1, 1000)])
    listing_description = TextAreaField('Item Description',
                                        validators=[DataRequired(), Length(1, 2500)])
    listing_price = DecimalField('Item Price', places=2,
                                 validators=[DataRequired(message=PRICE_MESSAGE)])
    listing_unit = StringField('Item Unit', validators=[DataRequired(), Length(1, 1000)])
    listing_quantity = IntegerField('Item Quantity (per unit)',
                                 validators=[DataRequired(message=PRICE_MESSAGE)])
    listing_available = BooleanField('Available?')
    submit = SubmitField('Update Item Information')



class NewItemForm(Form):
    listing_name = StringField('Item Name',
                               validators=[DataRequired(), Length(1, 1000)])
    listing_description = TextAreaField('Item Description',
                                        validators=[DataRequired(), Length(1, 2500)])
    listing_price = DecimalField('Item Price', places=2,
                                 validators=[DataRequired(message=PRICE_MESSAGE)])
    listing_unit = StringField('Item Unit', validators=[DataRequired(), Length(1, 1000)])
    listing_quantity = IntegerField('Item Quantity (per unit)',
                                 validators=[DataRequired(message=PRICE_MESSAGE)])
    listing_productID = IntegerField('Item Product ID',
                                 validators=[DataRequired(message='Provide a valid numerical Product Identification')])
    submit = SubmitField('Create New Item')

    def validate_listing_name(self, field):
        if current_user.listings.filter_by(name=field.data).first():
            raise ValidationError('You already have an item with this name.')


class NewCSVForm(Form):
    file_upload = FileField(validators=[DataRequired()])
    replace_or_merge = SelectField('Would you like to replace all of your current items on the system with this upload or merge this upload with the items on the system?', choices=[('replace', 'Replace'), ('merge', 'Merge')], validators=[DataRequired()])
    submit = SubmitField('Submit Upload')
