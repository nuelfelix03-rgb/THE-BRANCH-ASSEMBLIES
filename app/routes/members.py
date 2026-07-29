import csv
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db
from app.models import Member, Attendance
from app.forms import MemberForm
from app.utils.decorators import admin_required
from app.utils.helpers import generate_member_id, save_profile_picture

members_bp = Blueprint('members', __name__, url_prefix='/members')


@members_bp.route('/')
@login_required
@admin_required
def list_members():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    ministry_filter = request.args.get('ministry', '')
    status_filter = request.args.get('status', '')

    query = Member.query

    if search:
        query = query.filter(
            Member.first_name.ilike(f'%{search}%') |
            Member.last_name.ilike(f'%{search}%') |
            Member.member_id.ilike(f'%{search}%') |
            Member.phone_number.ilike(f'%{search}%')
        )
    if ministry_filter:
        query = query.filter(Member.ministry_id == int(ministry_filter))
    if status_filter:
        query = query.filter(Member.membership_status == status_filter)

    members = query.order_by(Member.last_name).paginate(page=page, per_page=20, error_out=False)

    from app.models import Ministry
    ministries = Ministry.query.all()

    return render_template('members/list.html', members=members, ministries=ministries,
                          search=search, ministry_filter=ministry_filter, status_filter=status_filter)


def _split_full_name(full_name):
    import re
    parts = re.split(r'\s+', full_name.strip(), maxsplit=1)
    first = parts[0] if parts else full_name.strip()
    last = parts[1] if len(parts) > 1 else ''
    return first, last


@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_member():
    form = MemberForm()
    if form.validate_on_submit():
        first, last = _split_full_name(form.full_name.data)
        member = Member(
            member_id=generate_member_id(),
            first_name=first,
            last_name=last,
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            marital_status=form.marital_status.data,
            phone_number=form.phone_number.data,
            email=form.email.data or None,
            residential_address=form.residential_address.data,
            profession=form.profession.data,
            is_student=form.is_student.data,
            school=form.school.data or None,
            faculty=form.faculty.data or None,
            department=form.department.data or None,
            level=form.level.data or None,
            accommodation=form.accommodation.data or None,
            hostel_name=form.hostel_name.data or None,
            room_number=form.room_number.data or None,
            previous_church=form.previous_church.data or None,
            how_heard=form.how_heard.data,
            friend_name=form.friend_name.data or None,
            other_source=form.other_source.data or None,
            preferred_social_platform=form.preferred_social_platform.data or None,
            social_handle=form.social_handle.data or None,
            membership_status='Active',
            baptism_status=form.baptism_status.data or 'Not Baptized'
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Member {member.full_name()} added successfully!', 'success')
        return redirect(url_for('members.list_members'))
    return render_template('members/form.html', form=form, title='Add Member')


@members_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_member(id):
    member = Member.query.get_or_404(id)
    form = MemberForm(obj=member)
    if form.validate_on_submit():
        first, last = _split_full_name(form.full_name.data)
        member.first_name = first
        member.last_name = last
        member.gender = form.gender.data
        member.date_of_birth = form.date_of_birth.data
        member.marital_status = form.marital_status.data
        member.phone_number = form.phone_number.data
        member.email = form.email.data or None
        member.residential_address = form.residential_address.data
        member.profession = form.profession.data
        member.is_student = form.is_student.data
        member.school = form.school.data or None
        member.faculty = form.faculty.data or None
        member.department = form.department.data or None
        member.level = form.level.data or None
        member.accommodation = form.accommodation.data or None
        member.hostel_name = form.hostel_name.data or None
        member.room_number = form.room_number.data or None
        member.previous_church = form.previous_church.data or None
        member.how_heard = form.how_heard.data
        member.friend_name = form.friend_name.data or None
        member.other_source = form.other_source.data or None
        member.preferred_social_platform = form.preferred_social_platform.data or None
        member.social_handle = form.social_handle.data or None
        db.session.commit()
        flash(f'Member {member.full_name()} updated successfully!', 'success')
        return redirect(url_for('members.list_members'))
    form.full_name.data = member.full_name()
    return render_template('members/form.html', form=form, title='Edit Member', member=member)


@members_bp.route('/view/<int:id>')
@login_required
def view_member(id):
    member = Member.query.get_or_404(id)
    attendance_records = Attendance.query.filter_by(member_id=member.id).order_by(
        Attendance.date.desc()
    ).limit(10).all()
    return render_template('members/view.html', member=member, attendance_records=attendance_records)


@members_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash(f'Member {member.full_name()} deleted.', 'info')
    return redirect(url_for('members.list_members'))


@members_bp.route('/export')
@login_required
@admin_required
def export_members():
    members = Member.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Member ID', 'First Name', 'Last Name', 'Gender', 'Phone', 'Email',
                     'Membership Status', 'Ministry', 'Date Joined'])
    for m in members:
        writer.writerow([m.member_id, m.first_name, m.last_name, m.gender,
                        m.phone_number, m.email, m.membership_status,
                        m.ministry.name if m.ministry else '', m.date_joined])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=members.csv'}
    )
