from datetime import datetime, timedelta, date
import secrets
from functools import wraps
from flask import Blueprint, jsonify, request
from app import db
from app.models import User, Member, Attendance, Ministry, Event, Announcement, Notification, ChurchInformation, ChurchSettings, PasswordResetToken
from sqlalchemy import func, case

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        token = auth.split(' ', 1)[1]
        user = User.query.filter_by(api_token=token).first()
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(user, *args, **kwargs):
        if user.role not in ('super_admin', 'church_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return f(user, *args, **kwargs)
    return decorated


def to_dict(model, fields=None, extra=None):
    result = {}
    for col in model.__table__.columns:
        val = getattr(model, col.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        result[col.name] = val
    if fields:
        result = {k: v for k, v in result.items() if k in fields}
    if extra:
        result.update(extra)
    return result


# === AUTH ===

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
    token = secrets.token_urlsafe(48)
    user.api_token = token
    db.session.commit()
    return jsonify({
        'token': token,
        'user': to_dict(user, fields=['id', 'username', 'email', 'role', 'position', 'phone', 'profile_picture', 'bio', 'address', 'facebook', 'twitter', 'instagram', 'whatsapp', 'linkedin'])
    })


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    user = User(username=username, email=email, role='member')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    token = secrets.token_urlsafe(48)
    user.api_token = token
    db.session.commit()
    return jsonify({
        'token': token,
        'user': to_dict(user, fields=['id', 'username', 'email', 'role'])
    }), 201


@api_bp.route('/auth/logout', methods=['POST'])
@token_required
def api_logout(user):
    user.api_token = None
    db.session.commit()
    return jsonify({'message': 'Logged out successfully'})


@api_bp.route('/auth/profile', methods=['GET'])
@token_required
def api_profile(user):
    return jsonify(to_dict(user, fields=['id', 'username', 'email', 'role', 'position', 'phone', 'profile_picture', 'bio', 'address', 'created_at']))


@api_bp.route('/auth/change-password', methods=['POST'])
@token_required
def api_change_password(user):
    data = request.get_json() or {}
    if not user.check_password(data.get('current_password', '')):
        return jsonify({'error': 'Current password is incorrect'}), 400
    new_password = data.get('new_password', '')
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'})


# === DASHBOARD ===

@api_bp.route('/dashboard')
@token_required
def api_dashboard(user):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    first_of_month = today.replace(day=1)
    settings = ChurchSettings.get_settings()
    member = Member.query.filter_by(email=user.email).first()
    if user.role == 'member' and member:
        total = Attendance.query.filter_by(member_id=member.id).count()
        present = Attendance.query.filter_by(member_id=member.id, status='Present').count()
        attendance_rate = round((present / total * 100)) if total > 0 else 0
        my_attendance = [
            to_dict(a, fields=['id', 'service_type', 'date', 'status'])
            for a in Attendance.query.filter_by(member_id=member.id).order_by(Attendance.date.desc()).limit(5).all()
        ]
    else:
        attendance_rate = 0
        my_attendance = []
    church_info = [
        to_dict(c, fields=['id', 'title', 'category', 'content', 'display_order', 'updated_at'])
        for c in ChurchInformation.query.filter_by(is_published=True).order_by(ChurchInformation.display_order, ChurchInformation.updated_at.desc()).all()
    ]
    announcements = [
        to_dict(a, fields=['id', 'title', 'content', 'category', 'status', 'created_at'])
        for a in Announcement.query.filter_by(status='Published').order_by(Announcement.created_at.desc()).limit(5).all()
    ]
    events = [
        to_dict(e, fields=['id', 'name', 'description', 'venue', 'start_date', 'end_date', 'status'])
        for e in Event.query.filter(Event.start_date >= datetime.now(), Event.status == 'Upcoming').order_by(Event.start_date).limit(5).all()
    ]
    return jsonify({
        'church_settings': to_dict(settings, fields=['church_name', 'church_address', 'church_phone', 'church_email', 'service_times', 'welcome_message']),
        'member': to_dict(member, fields=['id', 'first_name', 'last_name', 'member_id', 'phone_number', 'membership_status', 'ministry_id']) if member else None,
        'attendance_rate': attendance_rate,
        'my_attendance': my_attendance,
        'church_info': church_info,
        'announcements': announcements,
        'events': events,
        'role': user.role,
    })


# === MEMBERS ===

@api_bp.route('/members')
@token_required
def api_list_members(user):
    if user.role == 'member':
        return jsonify({'error': 'Access denied'}), 403
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    ministry_filter = request.args.get('ministry', type=int)
    query = Member.query
    if search:
        query = query.filter(
            Member.first_name.ilike(f'%{search}%') |
            Member.last_name.ilike(f'%{search}%') |
            Member.member_id.ilike(f'%{search}%') |
            Member.phone_number.ilike(f'%{search}%')
        )
    if ministry_filter:
        query = query.filter_by(ministry_id=ministry_filter)
    query = query.order_by(Member.first_name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'members': [to_dict(m, fields=['id', 'member_id', 'first_name', 'last_name', 'middle_name', 'gender', 'phone_number', 'email', 'marital_status', 'membership_status', 'ministry_id', 'profile_picture', 'date_of_birth', 'date_joined', 'baptism_status', 'residential_address', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'notes']) for m in pagination.items],
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'per_page': per_page,
    })


@api_bp.route('/members/<int:member_id>')
@token_required
def api_get_member(user, member_id):
    member = Member.query.get_or_404(member_id)
    attendance = [
        to_dict(a, fields=['id', 'service_type', 'date', 'status', 'notes'])
        for a in Attendance.query.filter_by(member_id=member.id).order_by(Attendance.date.desc()).limit(20).all()
    ]
    result = to_dict(member, fields=['id', 'member_id', 'first_name', 'last_name', 'middle_name', 'gender', 'phone_number', 'email', 'marital_status', 'date_of_birth', 'date_joined', 'baptism_status', 'membership_status', 'ministry_id', 'residential_address', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'profile_picture', 'notes'])
    result['attendance'] = attendance
    ministry = Ministry.query.get(member.ministry_id)
    result['ministry_name'] = ministry.name if ministry else None
    return jsonify(result)


@api_bp.route('/members', methods=['POST'])
@token_required
@admin_required
def api_create_member(user):
    data = request.get_json() or {}
    if not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'First name and last name required'}), 400
    from app.utils.helpers import generate_member_id
    member = Member(
        member_id=generate_member_id(),
        first_name=data['first_name'],
        last_name=data.get('last_name'),
        middle_name=data.get('middle_name'),
        gender=data.get('gender'),
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        marital_status=data.get('marital_status', 'Single'),
        membership_status=data.get('membership_status', 'Active'),
        baptism_status=data.get('baptism_status', 'Not Baptized'),
        residential_address=data.get('residential_address'),
        ministry_id=data.get('ministry_id'),
        emergency_contact_name=data.get('emergency_contact_name'),
        emergency_contact_phone=data.get('emergency_contact_phone'),
        emergency_contact_relationship=data.get('emergency_contact_relationship'),
        notes=data.get('notes'),
    )
    if data.get('date_of_birth'):
        member.date_of_birth = datetime.fromisoformat(data['date_of_birth']).date()
    if data.get('date_joined'):
        member.date_joined = datetime.fromisoformat(data['date_joined']).date()
    db.session.add(member)
    db.session.commit()
    return jsonify(to_dict(member)), 201


@api_bp.route('/members/<int:member_id>', methods=['PUT'])
@token_required
@admin_required
def api_update_member(user, member_id):
    member = Member.query.get_or_404(member_id)
    data = request.get_json() or {}
    for field in ['first_name', 'last_name', 'middle_name', 'gender', 'phone_number', 'email', 'marital_status', 'membership_status', 'baptism_status', 'residential_address', 'ministry_id', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'notes']:
        if field in data:
            setattr(member, field, data[field])
    if data.get('date_of_birth'):
        member.date_of_birth = datetime.fromisoformat(data['date_of_birth']).date()
    if data.get('date_joined'):
        member.date_joined = datetime.fromisoformat(data['date_joined']).date()
    db.session.commit()
    return jsonify(to_dict(member))


@api_bp.route('/members/<int:member_id>', methods=['DELETE'])
@token_required
@admin_required
def api_delete_member(user, member_id):
    member = Member.query.get_or_404(member_id)
    Attendance.query.filter_by(member_id=member.id).delete()
    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member deleted'}), 200


# === ATTENDANCE ===

@api_bp.route('/attendance')
@token_required
def api_list_attendance(user):
    if user.role == 'member':
        return jsonify({'error': 'Access denied'}), 403
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    service_filter = request.args.get('service_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    query = Attendance.query
    if service_filter:
        query = query.filter_by(service_type=service_filter)
    if date_from:
        query = query.filter(Attendance.date >= datetime.fromisoformat(date_from).date())
    if date_to:
        query = query.filter(Attendance.date <= datetime.fromisoformat(date_to).date())
    query = query.order_by(Attendance.date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'records': [to_dict(a, fields=['id', 'member_id', 'service_type', 'date', 'status', 'notes', 'recorded_by']) for a in pagination.items],
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'per_page': per_page,
    })


@api_bp.route('/attendance/stats')
@token_required
def api_attendance_stats(user):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    first_of_month = today.replace(day=1)
    weekly_data = db.session.query(
        Attendance.service_type,
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present')
    ).filter(
        Attendance.date >= week_start
    ).group_by(Attendance.service_type).all()
    monthly_data = db.session.query(
        func.strftime('%Y-%m', Attendance.date).label('month'),
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present')
    ).filter(
        Attendance.date >= first_of_month
    ).group_by(func.strftime('%Y-%m', Attendance.date)).all()
    return jsonify({
        'weekly': [{'service_type': w.service_type, 'total': w.total, 'present': w.present} for w in weekly_data],
        'monthly': [{'month': m.month, 'total': m.total, 'present': m.present} for m in monthly_data],
    })


@api_bp.route('/attendance', methods=['POST'])
@token_required
@admin_required
def api_create_attendance(user):
    data = request.get_json() or {}
    if not data.get('member_id') or not data.get('service_type'):
        return jsonify({'error': 'member_id and service_type required'}), 400
    record = Attendance(
        member_id=data['member_id'],
        service_type=data['service_type'],
        status=data.get('status', 'Present'),
        recorded_by=user.id,
        notes=data.get('notes'),
    )
    if data.get('date'):
        record.date = datetime.fromisoformat(data['date']).date()
    db.session.add(record)
    db.session.commit()
    return jsonify(to_dict(record)), 201


# === MINISTRIES ===

@api_bp.route('/ministries')
@token_required
def api_list_ministries(user):
    ministries = Ministry.query.order_by(Ministry.name).all()
    return jsonify({
        'ministries': [to_dict(m, fields=['id', 'name', 'description', 'leader', 'leader_user_id']) for m in ministries]
    })


@api_bp.route('/ministries/<int:ministry_id>')
@token_required
def api_get_ministry(user, ministry_id):
    ministry = Ministry.query.get_or_404(ministry_id)
    members_list = [
        to_dict(m, fields=['id', 'member_id', 'first_name', 'last_name', 'phone_number', 'email', 'membership_status'])
        for m in ministry.members.all()
    ]
    result = to_dict(ministry, fields=['id', 'name', 'description', 'leader', 'leader_user_id'])
    result['members'] = members_list
    return jsonify(result)


# === EVENTS ===

@api_bp.route('/events')
@token_required
def api_list_events(user):
    status_filter = request.args.get('status', '')
    query = Event.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    events_list = query.order_by(Event.start_date).all()
    return jsonify({
        'events': [to_dict(e, fields=['id', 'name', 'description', 'venue', 'start_date', 'end_date', 'organizer', 'status', 'ministry_id', 'registration_required']) for e in events_list]
    })


@api_bp.route('/events/<int:event_id>')
@token_required
def api_get_event(user, event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(to_dict(event, fields=['id', 'name', 'description', 'venue', 'start_date', 'end_date', 'organizer', 'status', 'ministry_id', 'registration_required', 'created_at']))


# === ANNOUNCEMENTS ===

@api_bp.route('/announcements')
@token_required
def api_list_announcements(user):
    announcements_list = Announcement.query.filter_by(status='Published').order_by(Announcement.created_at.desc()).all()
    return jsonify({
        'announcements': [to_dict(a, fields=['id', 'title', 'content', 'category', 'author_id', 'created_at']) for a in announcements_list]
    })


@api_bp.route('/announcements/<int:announcement_id>')
@token_required
def api_get_announcement(user, announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    return jsonify(to_dict(announcement, fields=['id', 'title', 'content', 'category', 'author_id', 'status', 'created_at']))


# === CHURCH INFORMATION ===

@api_bp.route('/church-info')
@token_required
def api_list_church_info(user):
    info_list = ChurchInformation.query.filter_by(is_published=True).order_by(ChurchInformation.display_order, ChurchInformation.updated_at.desc()).all()
    return jsonify({
        'church_info': [to_dict(i, fields=['id', 'title', 'category', 'content', 'display_order', 'updated_at']) for i in info_list]
    })


# === NOTIFICATIONS ===

@api_bp.route('/notifications')
@token_required
def api_list_notifications(user):
    notifications_list = Notification.query.filter_by(recipient_id=user.id).order_by(Notification.created_at.desc()).all()
    return jsonify({
        'notifications': [to_dict(n, fields=['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']) for n in notifications_list]
    })


@api_bp.route('/notifications/unread-count')
@token_required
def api_unread_count(user):
    count = Notification.query.filter_by(recipient_id=user.id, is_read=False).count()
    return jsonify({'count': count})


@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@token_required
def api_mark_read(user, notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_id != user.id and user.role not in ('super_admin', 'church_admin'):
        return jsonify({'error': 'Access denied'}), 403
    notification.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked as read'})


# === REPORTS ===

@api_bp.route('/reports/attendance')
@token_required
@admin_required
def api_attendance_report(user):
    period = request.args.get('period', 'week')
    today = date.today()
    if period == 'week':
        start = today - timedelta(days=today.weekday())
    elif period == 'month':
        start = today.replace(day=1)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today - timedelta(days=30)
    records = db.session.query(
        Attendance.service_type,
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present'),
        func.sum(case((Attendance.status == 'Absent', 1), else_=0)).label('absent')
    ).filter(Attendance.date >= start).group_by(Attendance.service_type).all()
    return jsonify({
        'period': period,
        'records': [{'service_type': r.service_type, 'total': r.total, 'present': r.present, 'absent': r.absent} for r in records]
    })


@api_bp.route('/reports/members')
@token_required
@admin_required
def api_members_report(user):
    total = Member.query.count()
    active = Member.query.filter_by(membership_status='Active').count()
    new_this_month = Member.query.filter(
        Member.date_joined >= date.today().replace(day=1)
    ).count()
    by_ministry = db.session.query(
        Ministry.name,
        func.count(Member.id).label('count')
    ).join(Ministry, Member.ministry_id == Ministry.id, isouter=True).group_by(Ministry.name).all()
    return jsonify({
        'total': total,
        'active': active,
        'new_this_month': new_this_month,
        'by_ministry': [{'name': m.name or 'Unassigned', 'count': m.count} for m in by_ministry],
    })


# === SETTINGS ===

@api_bp.route('/settings')
@token_required
def api_get_settings(user):
    settings = ChurchSettings.get_settings()
    return jsonify(to_dict(settings, fields=['church_name', 'church_address', 'church_phone', 'church_email', 'service_times', 'welcome_message']))


# === REGISTER MEMBER PROFILE (for member users) ===

@api_bp.route('/members/self-register', methods=['POST'])
@token_required
def api_self_register(user):
    if user.role != 'member':
        return jsonify({'error': 'Only members can register a profile'}), 403
    existing = Member.query.filter_by(email=user.email).first()
    if existing:
        return jsonify({'error': 'Profile already exists', 'member': to_dict(existing)}), 409
    data = request.get_json() or {}
    from app.utils.helpers import generate_member_id
    member = Member(
        member_id=generate_member_id(),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        middle_name=data.get('middle_name'),
        gender=data.get('gender'),
        phone_number=data.get('phone_number'),
        email=user.email,
        marital_status=data.get('marital_status', 'Single'),
        membership_status='Active',
        baptism_status=data.get('baptism_status', 'Not Baptized'),
        residential_address=data.get('residential_address'),
        emergency_contact_name=data.get('emergency_contact_name'),
        emergency_contact_phone=data.get('emergency_contact_phone'),
        emergency_contact_relationship=data.get('emergency_contact_relationship'),
    )
    if data.get('date_of_birth'):
        member.date_of_birth = datetime.fromisoformat(data['date_of_birth']).date()
    db.session.add(member)
    db.session.commit()
    return jsonify(to_dict(member)), 201


# === PASSWORD RESET ===

@api_bp.route('/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '')
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
    token = secrets.token_urlsafe(32)
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.session.add(reset)
    db.session.commit()
    from flask import current_app
    with current_app.app_context():
        from flask_mail import Message
        from app import mail
        try:
            msg = Message('Password Reset Request', recipients=[user.email])
            msg.body = f'Your password reset token: {token}\n\nThis token expires in 1 hour.'
            mail.send(msg)
        except Exception:
            pass
    return jsonify({'message': 'If the email exists, check your inbox', 'reset_token': token if not mail else None}), 200


@api_bp.route('/auth/reset-password', methods=['POST'])
def api_reset_password():
    data = request.get_json() or {}
    token = data.get('token', '')
    new_password = data.get('new_password', '')
    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.is_expired():
        return jsonify({'error': 'Invalid or expired token'}), 400
    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    user = User.query.get(reset.user_id)
    user.set_password(new_password)
    reset.used = True
    db.session.commit()
    return jsonify({'message': 'Password reset successfully'}), 200
