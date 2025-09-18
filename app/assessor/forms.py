from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import LogbookStatus

class FeedbackForm(FlaskForm):
    feedback = TextAreaField('Feedback', validators=[DataRequired(), Length(min=10, max=1000)])
    status = SelectField('Status', choices=[
        ('ASSESSOR_APPROVED', 'Approve'),
        ('ASSESSOR_REJECTED', 'Reject')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class VideoSessionForm(FlaskForm):
    title = StringField('Session Title', validators=[DataRequired(), Length(max=100)])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = StringField('Time (HH:MM)', validators=[DataRequired()])
    duration = SelectField('Duration', choices=[
        ('30', '30 minutes'),
        ('45', '45 minutes'),
        ('60', '1 hour'),
        ('90', '1.5 hours'),
        ('120', '2 hours')
    ], validators=[DataRequired()])
    notes = TextAreaField('Session Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Schedule Session')

class AttacheeSearchForm(FlaskForm):
    search = StringField('Search by name or organization', validators=[Optional()])
    submit = SubmitField('Search')