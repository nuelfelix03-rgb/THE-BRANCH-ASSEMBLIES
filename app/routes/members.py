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


@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_member():
    form = MemberForm()
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
            email=form.email.data,
            residential_address=form.residential_address.data,
            date_joined=form.date_joined.data,
            baptism_status=form.baptism_status.data,
            ministry_id=form.ministry_id.data if form.ministry_id.data != 0 else None,
            membership_status=form.membership_status.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_relationship=form.emergency_contact_relationship.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
            notes=form.notes.data
        )
        if form.profile_picture.data:
            picture_file = save_profile_picture(form.profile_picture.data)
            member.profile_picture = picture_file
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
        member.first_name = form.first_name.data
        member.last_name = form.last_name.data
        member.middle_name = form.middle_name.data
        member.gender = form.gender.data
        member.date_of_birth = form.date_of_birth.data
        member.marital_status = form.marital_status.data
        member.phone_number = form.phone_number.data
        member.email = form.email.data
        member.residential_address = form.residential_address.data
        member.date_joined = form.date_joined.data
        member.baptism_status = form.baptism_status.data
        member.ministry_id = form.ministry_id.data if form.ministry_id.data != 0 else None
        member.membership_status = form.membership_status.data
        member.emergency_contact_name = form.emergency_contact_name.data
        member.emergency_contact_relationship = form.emergency_contact_relationship.data
        member.emergency_contact_phone = form.emergency_contact_phone.data
        member.notes = form.notes.data
        if form.profile_picture.data:
            picture_file = save_profile_picture(form.profile_picture.data)
            member.profile_picture = picture_file
        db.session.commit()
        flash(f'Member {member.full_name()} updated successfully!', 'success')
        return redirect(url_for('members.list_members'))
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
