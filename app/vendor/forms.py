import imghdr
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms.fields import StringField, DecimalField, BooleanField, SubmitField, TextAreaField, FileField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, URL
from wtforms import ValidationError
from ..models import Category, Listing
from .. import db


PRICE_MESSAGE = "This value needs to be filled and needs to be a number"


class ImageFileRequired(object):
    """
    Validates that an uploaded file from a flask_wtf FileField is, in fact an
    image.  Better than checking the file extension, examines the header of
    the image using Python's built in imghdr module.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if field.data is None or imghdr.what('unused', field.data.read()) is None:
            message = self.message or 'An image file is required'
            raise ValidationError(message)

        field.data.seek(0)


class ChangeListingInformation(Form):
    category_id = QuerySelectField('Category',
                                   validators=[DataRequired()],
                                   get_label='name',
                                   query_factory=lambda: db.session.query(Category).order_by('id'))
    listing_name = StringField('Item Name', validators=[DataRequired(), Length(1, 1000)])
    listing_description = TextAreaField('Item Description',
                                        validators=[DataRequired(), Length(1, 2500)])
    listing_price = DecimalField('Item Price', places=2,
                                 validators=[DataRequired(message=PRICE_MESSAGE)])
    listing_available = BooleanField('Available?')
    submit = SubmitField('Update Item Information')

    def validate_listing_name(self, field):
        is_same_name = Listing.name == field.data
        is_diff_id = Listing.id != self.listing_id
        if current_user.listings.filter(is_same_name, is_diff_id).first():
            raise ValidationError('You already have an item with name {}.'.format(field.data))


class NewItemForm(Form):
    category_id = QuerySelectField('Category',
                                   validators=[DataRequired()],
                                   get_label='name',
                                   query_factory=lambda: db.session.query(Category).order_by('id'))
    listing_name = StringField('Item Name',
                               validators=[DataRequired(), Length(1, 1000)])
    listing_description = TextAreaField('Item Description',
                                        validators=[DataRequired(), Length(1, 2500)])
    listing_price = DecimalField('Item Price', places=2,
                                 validators=[DataRequired(message=PRICE_MESSAGE)])
    submit = SubmitField('Create New Item')

    def validate_listing_name(self, field):
        if current_user.listings.filter_by(name=field.data).first():
            raise ValidationError('You already have an item with this name.')


class EditProfileForm(Form):
    image = FileField(u'Image File', validators=[ImageFileRequired()])
    bio = TextAreaField('Bio')
    address = StringField('Address')
    phone_number = StringField('Phone Number')
    website = StringField('Website (http://www.example.com)',
                          validators=[URL('This URL is invalid. Please enter a valid website name')])
    email = StringField('Email', validators=[Email('Please enter a valid email address')])
    submit = SubmitField('Save')
