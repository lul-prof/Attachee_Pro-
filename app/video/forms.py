from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional

class JoinSessionForm(FlaskForm):
    session_id = StringField('Session ID', validators=[DataRequired()])
    submit = SubmitField('Join Session')