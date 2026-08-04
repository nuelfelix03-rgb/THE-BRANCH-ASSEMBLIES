from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Member
from app.models_ext import FamilyMember, MemberSkill, MemberDocument, BaptismRecord
from app.utils.helpers import delete_file

profile_ext_bp = Blueprint('profile_ext', __name__, url_prefix='/members')


@profile_ext_bp.route('/<int:id>/extended')
@login_required
def extended_profile(id):
    member = Member.query.get_or_404(id)
    family = FamilyMember.query.filter_by(member_id=id).all()
    skills = MemberSkill.query.filter_by(member_id=id).all()
    documents = MemberDocument.query.filter_by(member_id=id).all()
    baptisms = BaptismRecord.query.filter_by(member_id=id).all()
    return render_template('members/extended_profile.html', member=member,
                          family=family, skills=skills, documents=documents, baptisms=baptisms)


@profile_ext_bp.route('/<int:member_id>/family/add', methods=['POST'])
@login_required
def add_family_member(member_id):
    member = Member.query.get_or_404(member_id)
    fm = FamilyMember(
        member_id=member.id,
        name=request.form['name'],
        relationship=request.form['relationship'],
        phone=request.form.get('phone', ''),
        email=request.form.get('email', ''),
        occupation=request.form.get('occupation', ''),
        is_emergency_contact=request.form.get('is_emergency') == 'on'
    )
    dob = request.form.get('date_of_birth')
    if dob:
        fm.date_of_birth = date.fromisoformat(dob)
    db.session.add(fm)
    db.session.commit()
    flash('Family member added!', 'success')
    return redirect(url_for('profile_ext.extended_profile', id=member.id))


@profile_ext_bp.route('/family/delete/<int:id>')
@login_required
def delete_family_member(id):
    fm = FamilyMember.query.get_or_404(id)
    mid = fm.member_id
    db.session.delete(fm)
    db.session.commit()
    flash('Family member removed.', 'info')
    return redirect(url_for('profile_ext.extended_profile', id=mid))


@profile_ext_bp.route('/<int:member_id>/skills/add', methods=['POST'])
@login_required
def add_skill(member_id):
    member = Member.query.get_or_404(member_id)
    skill = MemberSkill(
        member_id=member.id,
        skill_name=request.form['skill_name'],
        proficiency=request.form.get('proficiency', 'Beginner')
    )
    db.session.add(skill)
    db.session.commit()
    flash('Skill added!', 'success')
    return redirect(url_for('profile_ext.extended_profile', id=member.id))


@profile_ext_bp.route('/skills/delete/<int:id>')
@login_required
def delete_skill(id):
    skill = MemberSkill.query.get_or_404(id)
    mid = skill.member_id
    db.session.delete(skill)
    db.session.commit()
    flash('Skill removed.', 'info')
    return redirect(url_for('profile_ext.extended_profile', id=mid))


@profile_ext_bp.route('/<int:member_id>/documents/upload', methods=['POST'])
@login_required
def upload_document(member_id):
    member = Member.query.get_or_404(member_id)
    file = request.files.get('document_file')
    if file and file.filename:
        import uuid
        from app.models_ext import UploadedImage
        token = uuid.uuid4().hex
        row = UploadedImage(
            token=token,
            data=file.read(),
            mimetype=file.mimetype or 'application/octet-stream'
        )
        db.session.add(row)

        doc = MemberDocument(
            member_id=member.id,
            document_type=request.form.get('document_type', 'Other'),
            file_name=token,
            description=request.form.get('description', '')
        )
        db.session.add(doc)
        db.session.commit()
        flash('Document uploaded!', 'success')
    return redirect(url_for('profile_ext.extended_profile', id=member.id))


@profile_ext_bp.route('/documents/delete/<int:id>')
@login_required
def delete_document(id):
    doc = MemberDocument.query.get_or_404(id)
    mid = doc.member_id
    if doc.file_name:
        delete_file(doc.file_name, 'member_docs')
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted.', 'info')
    return redirect(url_for('profile_ext.extended_profile', id=mid))


@profile_ext_bp.route('/<int:member_id>/baptism/add', methods=['POST'])
@login_required
def add_baptism(member_id):
    member = Member.query.get_or_404(member_id)
    baptism = BaptismRecord(
        member_id=member.id,
        baptism_date=date.fromisoformat(request.form['baptism_date']),
        baptized_by=request.form.get('baptized_by', ''),
        church_name=request.form.get('church_name', ''),
        notes=request.form.get('notes', '')
    )
    db.session.add(baptism)
    db.session.commit()
    flash('Baptism record added!', 'success')
    return redirect(url_for('profile_ext.extended_profile', id=member.id))


@profile_ext_bp.route('/baptism/delete/<int:id>')
@login_required
def delete_baptism(id):
    b = BaptismRecord.query.get_or_404(id)
    mid = b.member_id
    db.session.delete(b)
    db.session.commit()
    flash('Baptism record removed.', 'info')
    return redirect(url_for('profile_ext.extended_profile', id=mid))
