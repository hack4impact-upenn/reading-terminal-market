from flask.ext.wtf import Form
from wtforms.fields import StringField, PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from wtforms import ValidationError
from ..models import User, Role, Category
from .. import db


class ChangeUserEmailForm(Form):
    email = EmailField('New email', validators=[
        InputRequired(),
        Length(1, 64),
        Email()
    ])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class InviteUserForm(Form):
    role = QuerySelectField('Account type',
                            validators=[InputRequired()],
                            get_label='name',
                            query_factory=lambda: db.session.query(Role).
                            order_by('permissions'))
    email = EmailField('Email', validators=[InputRequired(), Length(1, 64),
                                            Email()])
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    first_name = StringField('First name', validators=[InputRequired(),
                                                       Length(1, 64)])
    last_name = StringField('Last name', validators=[InputRequired(),
                                                     Length(1, 64)])

    password = PasswordField('Password', validators=[
        InputRequired(), EqualTo('password2',
                                 'Passwords must match.')
    ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')


class NewCategoryForm(Form):
    category_name = StringField('Category', validators=[InputRequired(),
                                                        Length(1, 64)])
    unit = StringField('Unit', validators=[InputRequired(),
                                           Length(1, 32)])
    submit = SubmitField('Add category')
