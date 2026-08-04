import io
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Member, Attendance
from app.models_ext import QRCodeAttendance, ServiceSchedule
from app.utils.roles import role_required, ADMIN_ROLES
import qrcode

qr_bp = Blueprint('qr_attendance', __name__, url_prefix='/qr-attendance')


def generate_member_qr(member):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(f'CHURCH:{member.member_id}')
    qr.make(fit=True)
    img = qr.make_image(fill_color='#C8102E', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


@qr_bp.route('/service-qr/<int:service_id>')
@login_required
@role_required(*ADMIN_ROLES)
def service_qr(service_id):
    s = ServiceSchedule.query.get_or_404(service_id)
    url = url_for('qr_attendance.self_checkin', service=s.name, _external=True)
    qr = qrcode.QRCode(box_size=12, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#C8102E', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@qr_bp.route('/self-checkin', methods=['GET', 'POST'])
def self_checkin():
    services = ServiceSchedule.query.filter_by(is_active=True).all()
    service_types = [s.name for s in services] or ['Sunday Service', 'Bible Study', 'Prayer Meeting', 'Midweek Service']
    service = request.args.get('service') or request.form.get('service_type', 'Sunday Service')

    if request.method == 'POST':
        member_id_str = request.form.get('member_id', '').strip()
        service_type = request.form.get('service_type', 'Sunday Service')
        member = Member.query.filter_by(member_id=member_id_str).first()
        if not member:
            flash('Member ID not found. Please check your ID and try again.', 'danger')
            return redirect(url_for('qr_attendance.self_checkin', service=service_type))
        if member.membership_status != 'Active':
            flash('Your membership is not active. Please see the church office.', 'warning')
            return redirect(url_for('qr_attendance.self_checkin', service=service_type))

        ip = request.remote_addr or 'unknown'
        today = date.today()
        ip_count = QRCodeAttendance.query.filter_by(ip_address=ip, date=today).count()
        if ip_count >= 50:
            flash('Too many check-ins from this device today. Please see the check-in desk.', 'warning')
            return redirect(url_for('qr_attendance.self_checkin', service=service_type))

        existing = QRCodeAttendance.query.filter_by(
            member_id=member.id, date=today, service_type=service_type
        ).first()
        if existing:
            flash(f'You are already checked in for {service_type} today.', 'info')
        else:
            qr_att = QRCodeAttendance(
                member_id=member.id, service_type=service_type, date=today, ip_address=ip
            )
            db.session.add(qr_att)
            att = Attendance.query.filter_by(
                member_id=member.id, date=today, service_type=service_type
            ).first()
            if not att:
                att = Attendance(
                    member_id=member.id, service_type=service_type,
                    date=today, status='Present', recorded_by=None
                )
                db.session.add(att)
            db.session.commit()
            flash(f'Welcome, {member.first_name}! You are checked in for {service_type}.', 'success')
        return redirect(url_for('qr_attendance.self_checkin', service=service_type))

    return render_template('qr_attendance/self_checkin.html', services=service_types, service=service)


@qr_bp.route('/member-qr/<int:member_id>')
@login_required
def member_qr_code(member_id):
    member = Member.query.get_or_404(member_id)
    buf = generate_member_qr(member)
    return send_file(buf, mimetype='image/png')


@qr_bp.route('/scan')
@login_required
def scan_page():
    services = ServiceSchedule.query.filter_by(is_active=True).all()
    return render_template('qr_attendance/scan.html', services=services)


@qr_bp.route('/check-in', methods=['POST'])
@login_required
@role_required(*ADMIN_ROLES)
def check_in():
    data = request.get_json(silent=True) or request.form
    member_id_str = data.get('member_id', '')
    service_type = data.get('service_type', 'Sunday Service')

    member = Member.query.filter_by(member_id=member_id_str).first()
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    today = date.today()
    existing = QRCodeAttendance.query.filter_by(
        member_id=member.id, date=today, service_type=service_type
    ).first()
    if existing:
        return jsonify({'message': f'{member.full_name()} already checked in today.', 'member': member.full_name()}), 200

    qr_att = QRCodeAttendance(
        member_id=member.id, service_type=service_type, date=today,
        ip_address=request.remote_addr
    )
    db.session.add(qr_att)

    att = Attendance.query.filter_by(
        member_id=member.id, date=today, service_type=service_type
    ).first()
    if not att:
        att = Attendance(
            member_id=member.id, service_type=service_type,
            date=today, status='Present', recorded_by=current_user.id
        )
        db.session.add(att)

    db.session.commit()
    return jsonify({
        'message': f'{member.full_name()} checked in successfully!',
        'member': member.full_name(),
        'time': datetime.utcnow().strftime('%I:%M %p')
    })


@qr_bp.route('/manual-checkin', methods=['GET', 'POST'])
@login_required
@role_required(*ADMIN_ROLES)
def manual_checkin():
    services = ServiceSchedule.query.filter_by(is_active=True).all()
    service_types = [s.name for s in services] or ['Sunday Service', 'Bible Study', 'Prayer Meeting', 'Midweek Service']

    if request.method == 'POST':
        member_id_str = request.form.get('member_id', '')
        service_type = request.form.get('service_type', 'Sunday Service')
        member = Member.query.filter_by(member_id=member_id_str).first()
        if not member:
            flash('Member not found.', 'danger')
            return render_template('qr_attendance/manual.html', services=service_types)

        today = date.today()
        existing = QRCodeAttendance.query.filter_by(
            member_id=member.id, date=today, service_type=service_type
        ).first()
        if existing:
            flash(f'{member.full_name()} already checked in.', 'warning')
        else:
            qr_att = QRCodeAttendance(member_id=member.id, service_type=service_type, date=today)
            db.session.add(qr_att)
            att = Attendance.query.filter_by(member_id=member.id, date=today, service_type=service_type).first()
            if not att:
                att = Attendance(member_id=member.id, service_type=service_type, date=today, status='Present', recorded_by=current_user.id)
                db.session.add(att)
            db.session.commit()
            flash(f'{member.full_name()} checked in!', 'success')
        return redirect(url_for('qr_attendance.manual_checkin'))

    return render_template('qr_attendance/manual.html', services=service_types)


@qr_bp.route('/schedules', methods=['GET', 'POST'])
@login_required
@role_required(*ADMIN_ROLES)
def manage_schedules():
    if request.method == 'POST':
        name = request.form.get('name')
        day = request.form.get('day_of_week', type=int)
        start = request.form.get('start_time')
        end = request.form.get('end_time')
        if name and day is not None and start:
            from datetime import time
            sh, sm = start.split(':')
            eh, em = (end or '00:00').split(':')
            sched = ServiceSchedule(
                name=name, day_of_week=day,
                start_time=time(int(sh), int(sm)),
                end_time=time(int(eh), int(em)) if end else None
            )
            db.session.add(sched)
            db.session.commit()
            flash('Service schedule added!', 'success')
        return redirect(url_for('qr_attendance.manage_schedules'))

    schedules = ServiceSchedule.query.order_by(ServiceSchedule.day_of_week, ServiceSchedule.start_time).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return render_template('qr_attendance/schedules.html', schedules=schedules, days=days)


@qr_bp.route('/schedules/delete/<int:id>')
@login_required
@role_required(*ADMIN_ROLES)
def delete_schedule(id):
    s = ServiceSchedule.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash('Schedule deleted.', 'info')
    return redirect(url_for('qr_attendance.manage_schedules'))


@qr_bp.route('/today')
@login_required
def today_qr_attendance():
    today = date.today()
    records = QRCodeAttendance.query.filter_by(date=today).order_by(QRCodeAttendance.scanned_at.desc()).all()
    return render_template('qr_attendance/today.html', records=records, today=today)
