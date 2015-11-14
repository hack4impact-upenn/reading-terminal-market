from flask.ext.wtf import Form
from wtforms.fields import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField
)
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(Form):
    email = EmailField('Email', validators=[
        InputRequired(),
        Length(1, 64),
        Email()
    ])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')


class RequestResetPasswordForm(Form):
    email = EmailField('Email', validators=[
        InputRequired(),
        Length(1, 64),
        Email()])
    submit = SubmitField('Reset password')

    # We don't validate the email address so we don't confirm to attackers
    # that an account with the given email exists.


class ResetPasswordForm(Form):
    email = EmailField('Email', validators=[
        InputRequired(),
        Length(1, 64),
        Email()])
    new_password = PasswordField('New password', validators=[
        InputRequired(),
        EqualTo('new_password2', 'Passwords must match.')
    ])
    new_password2 = PasswordField('Confirm new password',
                                  validators=[InputRequired()])
    submit = SubmitField('Reset password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class CreateUserFromInviteForm(Form):
    first_name = StringField('First name', validators=[InputRequired(),
                                                       Length(1, 64)])
    last_name = StringField('Last name', validators=[InputRequired(),
                                                     Length(1, 64)])
    password = PasswordField('Password', validators=[
        InputRequired(),
        EqualTo('password2', 'Passwords must match.')
    ])
    password2 = PasswordField('Confirm new password',
                                validators=[InputRequired()])
    submit = SubmitField('Create account', validators=[InputRequired()])
    submit = SubmitField('Set password')


class CreateMerchantVendorFromInviteForm(CreateUserFromInviteForm):
    company_name = StringField('Company name', validators=[InputRequired(),
                                                     Length(1, 64)])


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[InputRequired()])
    new_password = PasswordField('New password', validators=[
        InputRequired(),
        EqualTo('new_password2', 'Passwords must match.')
    ])
    new_password2 = PasswordField('Confirm new password',
                                  validators=[InputRequired()])
    submit = SubmitField('Update password')


class ChangeEmailForm(Form):
    email = EmailField('New email', validators=[
        InputRequired(),
        Length(1, 64),
        Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangeCompanyNameForm(Form):
    company_name = StringField('Company name', validators=[
        InputRequired(),
        Length(1, 64)])
    submit = SubmitField('Update company name')


class ChangeNameForm(Form):
    first_name = StringField('First name', validators=[
        InputRequired(),
        Length(1, 64)])
    last_name = StringField('Last name', validators=[
        InputRequired(),
        Length(1, 64)])
    submit = SubmitField('Update name')
