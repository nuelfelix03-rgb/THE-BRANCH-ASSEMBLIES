from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Member, Attendance, Ministry, Event, Announcement, User, ChurchInformation
from app.utils.decorators import admin_required
from app.utils.helpers import generate_member_id, save_profile_picture, delete_file
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'member':
        return member_dashboard()
    return admin_dashboard()


def admin_dashboard():
    today = date.today()
    first_of_month = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())

    total_members = Member.query.filter_by(membership_status='Active').count()
    total_ministries = Ministry.query.count()
    attendance_this_week = Attendance.query.filter(
        Attendance.date >= week_start,
        Attendance.date <= today,
        Attendance.status == 'Present'
    ).count()
    attendance_this_month = Attendance.query.filter(
        Attendance.date >= first_of_month,
        Attendance.date <= today,
        Attendance.status == 'Present'
    ).count()

    upcoming_events = Event.query.filter(
        Event.start_date >= datetime.now(),
        Event.status == 'Upcoming'
    ).order_by(Event.start_date).limit(5).all()

    recent_announcements = Announcement.query.filter_by(
        status='Published'
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    monthly_growth = db_monthly_growth()

    return render_template('dashboard.html',
        total_members=total_members,
        total_ministries=total_ministries,
        attendance_this_week=attendance_this_week,
        attendance_this_month=attendance_this_month,
        upcoming_events=upcoming_events,
        recent_announcements=recent_announcements,
        monthly_growth=monthly_growth
    )


def member_dashboard():
    member = Member.query.filter_by(email=current_user.email).first()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    my_attendance = Attendance.query.filter_by(
        member_id=member.id
    ).order_by(Attendance.date.desc()).limit(5).all() if member else []

    attendance_rate = 0
    if member:
        total = Attendance.query.filter_by(member_id=member.id).count()
        present = Attendance.query.filter_by(member_id=member.id, status='Present').count()
        attendance_rate = round((present / total * 100) if total > 0 else 0)

    upcoming_events = Event.query.filter(
        Event.start_date >= datetime.now(),
        Event.status == 'Upcoming'
    ).order_by(Event.start_date).limit(5).all()

    recent_announcements = Announcement.query.filter_by(
        status='Published'
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    leadership = User.query.filter(User.role.in_(['super_admin', 'church_admin', 'ministry_leader']), User.is_active == True).all()

    church_info = ChurchInformation.query.filter_by(
        is_published=True
    ).order_by(ChurchInformation.display_order, ChurchInformation.updated_at.desc()).all()

    return render_template('member_dashboard.html',
        member=member,
        my_attendance=my_attendance,
        attendance_rate=attendance_rate,
        upcoming_events=upcoming_events,
        recent_announcements=recent_announcements,
        leadership=leadership,
        church_info=church_info
    )


@main_bp.route('/profile')
@login_required
def my_profile():
    member = Member.query.filter_by(email=current_user.email).first()
    return render_template('profile.html', member=member)


@main_bp.route('/register-profile', methods=['GET', 'POST'])
@login_required
def register_profile():
    if current_user.role != 'member':
        flash('Only members can register a profile.', 'warning')
        return redirect(url_for('main.dashboard'))

    existing = Member.query.filter_by(email=current_user.email).first()
    if existing:
        flash('You already have a member profile.', 'info')
        return redirect(url_for('main.my_profile'))

    from app.forms import MemberSelfRegistrationForm
    form = MemberSelfRegistrationForm()
    if form.validate_on_submit():
        member = Member(
            member_id=generate_member_id(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            middle_name=form.middle_name.data,
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            marital_status=form.marital_status.data,
            phone_number=form.phone_number.data,
            email=current_user.email,
            residential_address=form.residential_address.data,
            date_joined=date.today(),
            baptism_status=form.baptism_status.data,
            membership_status='Active',
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_relationship=form.emergency_contact_relationship.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
            profession=form.profession.data,
            is_student=form.is_student.data,
            school=form.school.data,
            faculty=form.faculty.data,
            department=form.department.data,
            level=form.level.data,
            accommodation=form.accommodation.data,
            hostel_name=form.hostel_name.data,
            room_number=form.room_number.data,
            previous_church=form.previous_church.data,
            how_heard=form.how_heard.data,
            friend_name=form.friend_name.data,
            other_source=form.other_source.data,
            preferred_social_platform=form.preferred_social_platform.data,
            social_handle=form.social_handle.data
        )
        picture = request.files.get('profile_picture')
        if picture and picture.filename:
            from app.utils.helpers import save_profile_picture
            member.profile_picture = save_profile_picture(picture)
        db.session.add(member)
        db.session.commit()
        flash('Your profile has been created! Welcome to the church.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('member_register.html', form=form)


@main_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_my_member_profile():
    if current_user.role != 'member':
        flash('Only members can edit their profile.', 'warning')
        return redirect(url_for('main.dashboard'))

    member = Member.query.filter_by(email=current_user.email).first()
    if not member:
        flash('Please register your profile first.', 'warning')
        return redirect(url_for('main.register_profile'))

    from app.forms import MemberSelfRegistrationForm
    form = MemberSelfRegistrationForm(obj=member)
    if form.validate_on_submit():
        member.first_name = form.first_name.data
        member.last_name = form.last_name.data
        member.middle_name = form.middle_name.data
        member.gender = form.gender.data
        member.date_of_birth = form.date_of_birth.data
        member.marital_status = form.marital_status.data
        member.phone_number = form.phone_number.data
        member.residential_address = form.residential_address.data
        member.baptism_status = form.baptism_status.data
        member.emergency_contact_name = form.emergency_contact_name.data
        member.emergency_contact_relationship = form.emergency_contact_relationship.data
        member.emergency_contact_phone = form.emergency_contact_phone.data
        member.profession = form.profession.data
        member.is_student = form.is_student.data
        member.school = form.school.data
        member.faculty = form.faculty.data
        member.department = form.department.data
        member.level = form.level.data
        member.accommodation = form.accommodation.data
        member.hostel_name = form.hostel_name.data
        member.room_number = form.room_number.data
        member.previous_church = form.previous_church.data
        member.how_heard = form.how_heard.data
        member.friend_name = form.friend_name.data
        member.other_source = form.other_source.data
        member.preferred_social_platform = form.preferred_social_platform.data
        member.social_handle = form.social_handle.data

        picture = request.files.get('profile_picture')
        if picture and picture.filename:
            member.profile_picture = save_profile_picture(picture)

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.my_profile'))
    return render_template('member_register.html', form=form, edit_mode=True, member=member)


@main_bp.route('/remove-photo')
@login_required
def remove_my_photo():
    if current_user.role == 'member':
        member = Member.query.filter_by(email=current_user.email).first()
        if member and member.profile_picture:
            delete_file(member.profile_picture)
            member.profile_picture = None
            db.session.commit()
            flash('Photo removed.', 'info')
    else:
        if current_user.profile_picture:
            delete_file(current_user.profile_picture)
            current_user.profile_picture = None
            db.session.commit()
            flash('Photo removed.', 'info')
    return redirect(url_for('main.my_profile'))


@main_bp.route('/user/<int:id>/profile')
@login_required
def view_user_profile(id):
    user = User.query.get_or_404(id)
    member = None
    if user.role == 'member':
        member = Member.query.filter_by(email=user.email).first()
    return render_template('user_profile.html', profile_user=user, member=member)


@main_bp.route('/edit-photo', methods=['GET', 'POST'])
@login_required
def edit_my_photo():
    from flask_wtf import FlaskForm
    from flask_wtf.file import FileField, FileAllowed
    from wtforms import SubmitField

    class PhotoForm(FlaskForm):
        profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
        submit = SubmitField('Upload Photo')

    form = PhotoForm()
    if form.validate_on_submit() and form.profile_picture.data:
        picture_file = save_profile_picture(form.profile_picture.data)
        if current_user.role == 'member':
            member = Member.query.filter_by(email=current_user.email).first()
            if member:
                if member.profile_picture:
                    delete_file(member.profile_picture)
                member.profile_picture = picture_file
        else:
            if current_user.profile_picture:
                delete_file(current_user.profile_picture)
            current_user.profile_picture = picture_file
        db.session.commit()
        flash('Profile picture updated!', 'success')
        return redirect(url_for('main.my_profile'))

    member = Member.query.filter_by(email=current_user.email).first()
    return render_template('edit_photo.html', form=form, member=member)


@main_bp.route('/edit-admin-profile', methods=['GET', 'POST'])
@login_required
def edit_admin_profile():
    if current_user.role == 'member':
        flash('Not available for members.', 'warning')
        return redirect(url_for('main.dashboard'))

    from flask_wtf import FlaskForm
    from flask_wtf.file import FileField, FileAllowed
    from wtforms import StringField, TextAreaField, SubmitField
    from wtforms.validators import Optional, Length

    class AdminProfileForm(FlaskForm):
        position = StringField('Position / Title', validators=[Optional(), Length(max=100)])
        phone = StringField('Phone', validators=[Optional(), Length(max=20)])
        address = StringField('Address / Location', validators=[Optional(), Length(max=255)])
        facebook = StringField('Facebook URL', validators=[Optional(), Length(max=255)])
        twitter = StringField('Twitter / X URL', validators=[Optional(), Length(max=255)])
        instagram = StringField('Instagram URL', validators=[Optional(), Length(max=255)])
        whatsapp = StringField('WhatsApp Number', validators=[Optional(), Length(max=20)])
        linkedin = StringField('LinkedIn URL', validators=[Optional(), Length(max=255)])
        bio = TextAreaField('Bio', validators=[Optional()])
        profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])])
        submit = SubmitField('Update Profile')

    form = AdminProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.position = form.position.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.facebook = form.facebook.data
        current_user.twitter = form.twitter.data
        current_user.instagram = form.instagram.data
        current_user.whatsapp = form.whatsapp.data
        current_user.linkedin = form.linkedin.data
        current_user.bio = form.bio.data

        picture = request.files.get('profile_picture')
        if picture and picture.filename:
            if current_user.profile_picture:
                delete_file(current_user.profile_picture)
            current_user.profile_picture = save_profile_picture(picture)

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('main.my_profile'))

    return render_template('admin_profile_edit.html', form=form, profile_user=current_user)


def db_monthly_growth():
    today = date.today()
    months = []
    counts = []
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month < 1:
            month += 12
            year -= 1
        months.append(f'{year}-{month:02d}')
        count = Member.query.filter(
            func.extract('year', Member.date_joined) == year,
            func.extract('month', Member.date_joined) == month
        ).count()
        counts.append(count)
    return {'labels': months, 'data': counts}
