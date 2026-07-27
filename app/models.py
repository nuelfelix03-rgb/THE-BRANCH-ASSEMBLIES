from datetime import datetime, date
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(255))
    position = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    address = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    whatsapp = db.Column(db.String(20))
    linkedin = db.Column(db.String(255))
    api_token = db.Column(db.String(128), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    announcements = db.relationship('Announcement', backref='author', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='recorded_by_user', lazy='dynamic')
    notifications_sent = db.relationship('Notification', foreign_keys='Notification.sender_id', backref='sender', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role in roles

    def __repr__(self):
        return f'<User {self.username}>'


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    marital_status = db.Column(db.String(20), default='Single')
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    residential_address = db.Column(db.Text)
    date_joined = db.Column(db.Date, default=date.today)
    baptism_status = db.Column(db.String(50), default='Not Baptized')
    ministry_id = db.Column(db.Integer, db.ForeignKey('ministries.id'))
    membership_status = db.Column(db.String(20), default='Active')
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_relationship = db.Column(db.String(50))
    emergency_contact_phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def __repr__(self):
        return f'<Member {self.member_id}: {self.full_name()}>'


ministry_members = db.Table('ministry_members',
    db.Column('ministry_id', db.Integer, db.ForeignKey('ministries.id'), primary_key=True),
    db.Column('member_id', db.Integer, db.ForeignKey('members.id'), primary_key=True)
)


class Ministry(db.Model):
    __tablename__ = 'ministries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    leader = db.Column(db.String(100))
    leader_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    leader_user = db.relationship('User', foreign_keys=[leader_user_id])
    members = db.relationship('Member', backref='ministry', lazy='dynamic')
    events = db.relationship('Event', backref='ministry', lazy='dynamic')
    additional_members = db.relationship('Member', secondary=ministry_members,
        backref=db.backref('additional_ministries', lazy='dynamic'),
        lazy='dynamic')

    def __repr__(self):
        return f'<Ministry {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default='Present')
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='attendances', foreign_keys=[member_id])

    __table_args__ = (
        db.Index('idx_attendance_date_service', 'date', 'service_type'),
        db.UniqueConstraint('member_id', 'date', 'service_type', name='uq_member_date_service'),
    )

    def __repr__(self):
        return f'<Attendance {self.member_id} - {self.service_type} on {self.date}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    venue = db.Column(db.String(200))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    organizer = db.Column(db.String(100))
    ministry_id = db.Column(db.Integer, db.ForeignKey('ministries.id'))
    status = db.Column(db.String(20), default='Upcoming')
    registration_required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Event {self.name}>'


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='Draft')
    scheduled_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Announcement {self.title}>'


class AnnouncementRead(db.Model):
    __tablename__ = 'announcement_reads'

    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)

    announcement = db.relationship('Announcement', backref='reads')
    user = db.relationship('User', backref='announcement_reads')

    __table_args__ = (
        db.UniqueConstraint('announcement_id', 'user_id', name='uq_user_announcement_read'),
    )

    def __repr__(self):
        return f'<AnnouncementRead {self.announcement_id} by user {self.user_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='In-App')
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='notifications_received')

    def __repr__(self):
        return f'<Notification {self.title}>'


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reset_tokens')

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<PasswordResetToken for user {self.user_id}>'


CHURCH_INFO_CATEGORIES = [
    'Church Vision', 'Church Mission', 'Church History',
    'Weekly Theme', "Pastor's Message", 'Service Times',
    'Upcoming Programs', 'Church Contact Information',
    'Church Leadership', 'General Information', 'Custom'
]


class ChurchInformation(db.Model):
    __tablename__ = 'church_information'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General Information')
    content = db.Column(db.Text, nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship('User', backref='church_infos')

    def __repr__(self):
        return f'<ChurchInformation {self.title}>'


class ChurchSettings(db.Model):
    __tablename__ = 'church_settings'

    id = db.Column(db.Integer, primary_key=True)
    church_name = db.Column(db.String(200), default='My Church')
    church_address = db.Column(db.Text)
    church_phone = db.Column(db.String(20))
    church_email = db.Column(db.String(120))
    service_times = db.Column(db.Text)
    welcome_message = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_settings(cls):
        setting = cls.query.first()
        if not setting:
            setting = cls()
            db.session.add(setting)
            db.session.commit()
        return setting

    def __repr__(self):
        return f'<ChurchSettings: {self.church_name}>'
