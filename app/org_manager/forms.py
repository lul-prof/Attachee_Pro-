from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, Length, Email, ValidationError, Optional
from app.models import User

class AttacheeForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    department = StringField('Department', validators=[Optional(), Length(max=64)])
    supervisor_name = StringField('Supervisor Name', validators=[Optional(), Length(max=64)])
    supervisor_email = StringField('Supervisor Email', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('Submit')
    
    def __init__(self, original_email=None, *args, **kwargs):
        super(AttacheeForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email is already registered.')

class LogbookReviewForm(FlaskForm):
    feedback = TextAreaField('Feedback', validators=[DataRequired(), Length(max=500)])
    status = RadioField('Status', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Review')