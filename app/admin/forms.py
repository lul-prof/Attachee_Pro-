from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User, Organization, UserRole

class OrganizationForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    address = StringField('Address', validators=[Optional(), Length(max=200)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=120)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    website = StringField('Website', validators=[Optional(), Length(max=100)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')
    
    def validate_name(self, name):
        org = Organization.query.filter_by(name=name.data).first()
        if org:
            raise ValidationError('An organization with this name already exists.')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[(role.name, role.value) for role in UserRole])
    submit = SubmitField('Create User')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered.')

class UserSearchForm(FlaskForm):
    search = StringField('Search by username or email', validators=[Optional()])
    submit = SubmitField('Search')