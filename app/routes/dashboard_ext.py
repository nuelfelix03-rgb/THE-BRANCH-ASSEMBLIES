from datetime import date, timedelta, datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Member, Attendance, Event, Ministry
from app.utils.roles import ADMIN_ROLES, role_required

dash_ext_bp = Blueprint('dashboard_ext', __name__, url_prefix='/dashboard')


@dash_ext_bp.route('/stats')
@login_required
def stats():
    today = date.today()
    first_of_month = today.replace(day=1)

    total_members = Member.query.filter_by(membership_status='Active').count()
    total_ministries = Ministry.query.count()

    today_attendance = Attendance.query.filter(
        Attendance.date == today, Attendance.status == 'Present'
    ).count()

    birthdays_this_month = Member.query.filter(
        db.extract('month', Member.date_of_birth) == today.month,
        Member.membership_status == 'Active'
    ).count() if hasattr(db, 'extract') else 0

    new_members = Member.query.filter(
        Member.date_joined >= first_of_month
    ).count()

    upcoming_events = Event.query.filter(
        Event.start_date >= datetime.now(),
        Event.status == 'Upcoming'
    ).count()

    return render_template('dashboard_ext/stats.html',
        total_members=total_members,
        total_ministries=total_ministries,
        today_attendance=today_attendance,
        birthdays_this_month=birthdays_this_month,
        new_members=new_members,
        upcoming_events=upcoming_events
    )


@dash_ext_bp.route('/extended')
@login_required
def extended_dashboard():
    today = date.today()
    first_of_month = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())

    total_members = Member.query.filter_by(membership_status='Active').count()
    total_ministries = Ministry.query.count()

    today_attendance = Attendance.query.filter(
        Attendance.date == today, Attendance.status == 'Present'
    ).count()

    week_attendance = Attendance.query.filter(
        Attendance.date >= week_start, Attendance.date <= today,
        Attendance.status == 'Present'
    ).count()

    birthdays = Member.query.filter(
        db.extract('month', Member.date_of_birth) == today.month,
        Member.membership_status == 'Active'
    ).all() if hasattr(db, 'extract') else []

    new_members = Member.query.filter(
        Member.date_joined >= first_of_month
    ).all()

    upcoming_events = Event.query.filter(
        Event.start_date >= datetime.now(),
        Event.status == 'Upcoming'
    ).order_by(Event.start_date).limit(5).all()

    return render_template('dashboard_ext/extended.html',
        total_members=total_members,
        total_ministries=total_ministries,
        today_attendance=today_attendance,
        week_attendance=week_attendance,
        birthdays=birthdays,
        new_members=new_members,
        upcoming_events=upcoming_events
    )
