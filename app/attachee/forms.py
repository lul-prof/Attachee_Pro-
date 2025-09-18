from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField,IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.validators import DataRequired, Length, Optional
from app.models import LogbookStatus

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    organization = SelectField('Organization', coerce=int)
    department = StringField('Department', validators=[Length(max=64)])
    supervisor_name = StringField('Supervisor Name', validators=[Length(max=64)])
    supervisor_email = StringField('Supervisor Email', validators=[Length(max=120)])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Update Profile')

class LogbookEntryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_date = DateField('Start Date', 
                          validators=[DataRequired()],
                          format='%Y-%m-%d')
    end_date = DateField('End Date',
                        validators=[DataRequired()],
                        format='%Y-%m-%d')
    week_number = IntegerField('Week Number', 
                              validators=[DataRequired(), NumberRange(min=1, max=52)])
    activities = TextAreaField('Activities Performed', validators=[DataRequired()])
    skills_learned = TextAreaField('Skills Learned', validators=[DataRequired()])
    challenges = TextAreaField('Challenges Faced', validators=[Optional()])
    solutions = TextAreaField('Solutions Applied', validators=[Optional()])
    submit = SubmitField('Submit Entry')

class FileUploadForm(FlaskForm):
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Allowed file types: PDF, Word, Images')
    ])
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    file_type = SelectField('Category', choices=[
        ('report', 'Report'),
        ('certificate', 'Certificate'),
        ('evidence', 'Work Evidence'),
        ('other', 'Other')
    ])
    submit = SubmitField('Upload File')