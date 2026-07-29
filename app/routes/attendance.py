from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Member, Attendance
from app.forms import AttendanceForm
from app.utils.decorators import admin_required
from sqlalchemy import func, case

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/')
@login_required
def list_attendance():
    page = request.args.get('page', 1, type=int)
    service_filter = request.args.get('service_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search_query = request.args.get('search', '').strip()

    query = Attendance.query.join(Member, Attendance.member_id == Member.id)

    if search_query:
        like = f'%{search_query}%'
        query = query.filter(
            Member.member_id.like(like) |
            Member.first_name.like(like) |
            Member.last_name.like(like) |
            Member.phone.like(like)
        )
    if service_filter:
        query = query.filter(Attendance.service_type == service_filter)
    if date_from:
        query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())

    attendance_records = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=20)

    service_types = ['Sunday Service', 'Midweek Service', 'Prayer Meeting', 'Special Program', 'Ministry Meeting']

    return render_template('attendance/list.html', attendance_records=attendance_records,
                          service_types=service_types, service_filter=service_filter,
                          date_from=date_from, date_to=date_to, search_query=search_query)


@attendance_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_attendance():
    form = AttendanceForm()
    members = Member.query.filter_by(membership_status='Active').all()
    form.member_id.choices = [(m.id, f'{m.member_id} - {m.full_name()}') for m in members]

    if form.validate_on_submit():
        existing = Attendance.query.filter_by(
            member_id=form.member_id.data,
            date=form.date.data,
            service_type=form.service_type.data
        ).first()
        if existing:
            flash('Attendance already recorded for this member on this date and service.', 'warning')
            return render_template('attendance/form.html', form=form, title='Record Attendance')

        attendance = Attendance(
            member_id=form.member_id.data,
            service_type=form.service_type.data,
            date=form.date.data,
            status=form.status.data,
            recorded_by=current_user.id,
            notes=form.notes.data
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance recorded successfully!', 'success')
        return redirect(url_for('attendance.list_attendance'))
    return render_template('attendance/form.html', form=form, title='Record Attendance')


@attendance_bp.route('/bulk', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_attendance():
    members = Member.query.filter_by(membership_status='Active').all()
    service_type = request.args.get('service_type', 'Sunday Service')
    attendance_date = request.args.get('date', date.today().isoformat())

    if request.method == 'POST':
        count = 0
        for member in members:
            status = request.form.get(f'status_{member.id}', 'Absent')
            existing = Attendance.query.filter_by(
                member_id=member.id,
                date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                service_type=service_type
            ).first()
            if not existing and status == 'Present':
                attendance = Attendance(
                    member_id=member.id,
                    service_type=service_type,
                    date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                    status='Present',
                    recorded_by=current_user.id
                )
                db.session.add(attendance)
                count += 1
        db.session.commit()
        flash(f'Attendance recorded for {count} members!', 'success')
        return redirect(url_for('attendance.list_attendance'))

    service_types = ['Sunday Service', 'Midweek Service', 'Prayer Meeting', 'Special Program', 'Ministry Meeting']
    return render_template('attendance/bulk.html', members=members,
                          service_type=service_type, attendance_date=attendance_date,
                          service_types=service_types)


@attendance_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_attendance(id):
    attendance = Attendance.query.get_or_404(id)
    db.session.delete(attendance)
    db.session.commit()
    flash('Attendance record deleted.', 'info')
    return redirect(url_for('attendance.list_attendance'))


@attendance_bp.route('/stats')
@login_required
def attendance_stats():
    today = date.today()

    weekly_data = db.session.query(
        Attendance.service_type,
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present')
    ).filter(
        Attendance.date >= (today - timedelta(days=7))
    ).group_by(Attendance.service_type).all()

    if db.engine.dialect.name == 'sqlite':
        month_expr = func.strftime('%Y-%m', Attendance.date)
    else:
        month_expr = func.date_format(Attendance.date, '%Y-%m')

    monthly_data = db.session.query(
        month_expr.label('month'),
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present')
    ).filter(
        Attendance.date >= today.replace(day=1)
    ).group_by(month_expr).all()

    return render_template('attendance/stats.html', weekly_data=weekly_data, monthly_data=monthly_data)
