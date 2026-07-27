from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, TextAreaField, DateField,
                     SelectField, SubmitField, BooleanField, IntegerField,
                     DateTimeField, HiddenField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo,
                                ValidationError, Optional)
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')


class MemberForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=100)])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female')])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    marital_status = SelectField('Marital Status', choices=[
        ('Single', 'Single'), ('Married', ' Married'), ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed')
    ])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    residential_address = TextAreaField('Residential Address', validators=[Optional()])
    date_joined = DateField('Date Joined', format='%Y-%m-%d', validators=[Optional()])
    baptism_status = SelectField('Baptism Status', choices=[
        ('Not Baptized', 'Not Baptized'), ('Baptized', 'Baptized'),
        ('Pending', 'Pending')
    ])
    ministry_id = SelectField('Ministry/Department', coerce=int, validators=[Optional()])
    membership_status = SelectField('Membership Status', choices=[
        ('Active', 'Active'), ('Inactive', 'Inactive'), ('Transferred', 'Transferred'),
        ('Removed', 'Removed')
    ])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=100)])
    emergency_contact_relationship = StringField('Relationship', validators=[Optional(), Length(max=50)])
    emergency_contact_phone = StringField('Emergency Phone', validators=[Optional(), Length(max=20)])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Member')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Ministry
        self.ministry_id.choices = [(0, 'No Ministry')] + [
            (m.id, m.name) for m in Ministry.query.all()
        ]


class AttendanceForm(FlaskForm):
    member_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    service_type = SelectField('Service Type', choices=[
        ('Sunday Service', 'Sunday Service'),
        ('Midweek Service', 'Midweek Service'),
        ('Prayer Meeting', 'Prayer Meeting'),
        ('Special Program', 'Special Program'),
        ('Ministry Meeting', 'Ministry Meeting')
    ], validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Present', 'Present'), ('Absent', 'Absent')])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Attendance')


class MinistryForm(FlaskForm):
    name = StringField('Ministry Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    leader = StringField('Leader Name', validators=[Optional(), Length(max=100)])
    leader_user_id = SelectField('Leader User', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Ministry')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import User
        users = User.query.filter(User.role.in_(['ministry_leader', 'church_admin', 'super_admin'])).all()
        self.leader_user_id.choices = [(0, 'No User Assigned')] + [
            (u.id, f'{u.username} ({u.role})') for u in users
        ]


class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('General', 'General'), ('Events', 'Events'),
        ('Meetings', 'Meetings'), ('Prayer', 'Prayer'),
        ('Emergency', 'Emergency')
    ])
    status = SelectField('Status', choices=[
        ('Draft', 'Draft'), ('Published', 'Published')
    ])
    scheduled_date = DateTimeField('Schedule Date (optional)', format='%Y-%m-%d %H:%M', validators=[Optional()])
    submit = SubmitField('Save Announcement')


class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    venue = StringField('Venue', validators=[Optional(), Length(max=200)])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    organizer = StringField('Organizer', validators=[Optional(), Length(max=100)])
    ministry_id = SelectField('Ministry', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Upcoming', 'Upcoming'), ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'), ('Cancelled', 'Cancelled')
    ])
    registration_required = BooleanField('Registration Required')
    submit = SubmitField('Save Event')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Ministry
        self.ministry_id.choices = [(0, 'No Ministry')] + [
            (m.id, m.name) for m in Ministry.query.all()
        ]


class NotificationForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])
    notification_type = SelectField('Type', choices=[
        ('In-App', 'In-App'), ('Email', 'Email')
    ])
    submit = SubmitField('Send Notification')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No account found with that email.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    role = SelectField('Role', choices=[
        ('member', 'Member'),
        ('ministry_leader', 'Ministry Leader'),
        ('church_admin', 'Church Admin'),
        ('super_admin', 'Super Admin')
    ])
    is_active = BooleanField('Active')
    submit = SubmitField('Save User')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password.validators = [Optional()]


class ChurchSettingsForm(FlaskForm):
    church_name = StringField('Church Name', validators=[Optional(), Length(max=200)])
    church_address = TextAreaField('Address', validators=[Optional()])
    church_phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    church_email = StringField('Email', validators=[Optional(), Email()])
    service_times = TextAreaField('Service Times', validators=[Optional()])
    welcome_message = TextAreaField('Welcome Message', validators=[Optional()])
    submit = SubmitField('Save Settings')


CATEGORY_CHOICES = [
    ('', 'Select Category'),
    ('Church Vision', 'Church Vision'),
    ('Church Mission', 'Church Mission'),
    ('Church History', 'Church History'),
    ('Weekly Theme', 'Weekly Theme'),
    ("Pastor's Message", "Pastor's Message"),
    ('Service Times', 'Service Times'),
    ('Upcoming Programs', 'Upcoming Programs'),
    ('Church Contact Information', 'Church Contact Information'),
    ('Church Leadership', 'Church Leadership'),
    ('General Information', 'General Information'),
    ('Custom', 'Custom'),
]


class ChurchInformationForm(FlaskForm):
    title = StringField('Information Title', validators=[DataRequired(), Length(max=200)])
    category = SelectField('Category', choices=CATEGORY_CHOICES, validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    display_order = IntegerField('Display Order', default=0)
    is_published = BooleanField('Published')
    submit = SubmitField('Save')


class MemberSelfRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=100)])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female')])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    marital_status = SelectField('Marital Status', choices=[
        ('Single', 'Single'), ('Married', 'Married'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')
    ])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    residential_address = TextAreaField('Residential Address', validators=[Optional()])
    baptism_status = SelectField('Baptism Status', choices=[
        ('Not Baptized', 'Not Baptized'), ('Baptized', 'Baptized'), ('Pending', 'Pending')
    ])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=100)])
    emergency_contact_relationship = StringField('Relationship', validators=[Optional(), Length(max=50)])
    emergency_contact_phone = StringField('Emergency Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Submit Profile')
