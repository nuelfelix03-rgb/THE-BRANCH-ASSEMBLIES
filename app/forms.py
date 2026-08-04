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
    # === Section 1: Personal Information ===
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    residential_address = TextAreaField('Home Address', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    marital_status = SelectField('Marital Status', choices=[
        ('', 'Select Marital Status'), ('Single', 'Single'), ('Married', 'Married'),
        ('Engaged', 'Engaged'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')
    ], validators=[DataRequired()])
    profession = StringField('Profession / Occupation', validators=[DataRequired(), Length(max=100)])

    # === Section 2: Student Information ===
    is_student = SelectField('Are you a Student?', choices=[('', 'Select Option'), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    school = StringField('School', validators=[Optional(), Length(max=200)])
    faculty = StringField('Faculty', validators=[Optional(), Length(max=200)])
    department = StringField('Department', validators=[Optional(), Length(max=200)])
    level = SelectField('Level', choices=[
        ('', 'Select Level'), ('100', '100'), ('200', '200'), ('300', '300'),
        ('400', '400'), ('500', '500'), ('Postgraduate', 'Postgraduate'), ('Other', 'Other')
    ], validators=[Optional()])
    accommodation = SelectField('Accommodation', choices=[
        ('', 'Select Accommodation'), ('Hostel', 'Hostel'), ('Off Campus', 'Off Campus')
    ], validators=[Optional()])
    hostel_name = StringField('Hostel Name', validators=[Optional(), Length(max=200)])
    room_number = StringField('Room Number', validators=[Optional(), Length(max=50)])

    # === Section 3: Membership Details ===
    previous_church = StringField('Previous Church', validators=[Optional(), Length(max=200)])
    how_heard = SelectField('How did you hear about us?', choices=[
        ('', 'Select Option'), ('Friend', 'Friend'), ('Family', 'Family'),
        ('Facebook', 'Facebook'), ('Instagram', 'Instagram'), ('WhatsApp', 'WhatsApp'),
        ('TikTok', 'TikTok'), ('X (Twitter)', 'X (Twitter)'), ('YouTube', 'YouTube'),
        ('Church Outreach', 'Church Outreach'), ('Google Search', 'Google Search'),
        ('Website', 'Website'), ('Flyer', 'Flyer'), ('Campus Evangelism', 'Campus Evangelism'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    friend_name = StringField("Friend's Name", validators=[Optional(), Length(max=100)])
    other_source = StringField('Please Specify', validators=[Optional(), Length(max=200)])

    # === Social Media ===
    preferred_social_platform = SelectField('Preferred Social Media Platform', choices=[
        ('', 'Select Platform'), ('WhatsApp', 'WhatsApp'), ('Facebook', 'Facebook'),
        ('Instagram', 'Instagram'), ('TikTok', 'TikTok'), ('X (Twitter)', 'X (Twitter)'),
        ('Telegram', 'Telegram'), ('Snapchat', 'Snapchat'), ('LinkedIn', 'LinkedIn'),
        ('Other', 'Other')
    ], validators=[Optional()])
    social_handle = StringField('Social Media Username / Handle', validators=[Optional(), Length(max=100)])

    # === Hidden legacy fields for compatibility ===
    first_name = HiddenField()
    last_name = HiddenField()
    middle_name = HiddenField()
    baptism_status = HiddenField()
    ministry_id = HiddenField()
    membership_status = HiddenField()
    emergency_contact_name = HiddenField()
    emergency_contact_relationship = HiddenField()
    emergency_contact_phone = HiddenField()
    profile_picture = HiddenField()
    notes = HiddenField()
    date_joined = HiddenField()

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
    image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])])
    author_name = StringField('Author (optional)', validators=[Optional(), Length(max=100)])
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
    profession = StringField('Profession / Occupation', validators=[Optional(), Length(max=200)])
    is_student = SelectField('Are you a student?', choices=[('', 'Select...'), ('yes', 'Yes'), ('no', 'No')])
    school = StringField('School / Institution', validators=[Optional(), Length(max=200)])
    faculty = StringField('Faculty', validators=[Optional(), Length(max=200)])
    department = StringField('Department', validators=[Optional(), Length(max=200)])
    level = StringField('Level / Year', validators=[Optional(), Length(max=50)])
    accommodation = SelectField('Accommodation Type', choices=[('', 'Select...'), ('Hostel', 'Hostel'), ('Off-Campus', 'Off-Campus'), ('Home', 'Home')], validators=[Optional()])
    hostel_name = StringField('Hostel Name', validators=[Optional(), Length(max=200)])
    room_number = StringField('Room Number', validators=[Optional(), Length(max=50)])
    previous_church = StringField('Previous Church', validators=[Optional(), Length(max=200)])
    how_heard = SelectField('How did you hear about us?', choices=[
        ('', 'Select...'), ('Friend', 'Friend'), ('Social Media', 'Social Media'),
        ('Church Website', 'Church Website'), ('Campus Outreach', 'Campus Outreach'),
        ('Family Member', 'Family Member'), ('Other', 'Other')
    ], validators=[Optional()])
    friend_name = StringField('Friend\'s Name (if referred)', validators=[Optional(), Length(max=100)])
    other_source = StringField('Please specify (if Other)', validators=[Optional(), Length(max=200)])
    preferred_social_platform = StringField('Preferred Social Platform', validators=[Optional(), Length(max=100)])
    social_handle = StringField('Social Media Handle', validators=[Optional(), Length(max=100)])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])])
    submit = SubmitField('Submit Profile')
