from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Ministry, Member
from app.forms import MinistryForm
from app.utils.decorators import admin_required, ministry_leader_required, is_ministry_leader

ministries_bp = Blueprint('ministries', __name__, url_prefix='/ministries')


@ministries_bp.route('/')
@login_required
def list_ministries():
    ministries = Ministry.query.order_by(Ministry.name).all()
    return render_template('ministries/list.html', ministries=ministries)


@ministries_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_ministry():
    form = MinistryForm()
    if form.validate_on_submit():
        ministry = Ministry(
            name=form.name.data,
            description=form.description.data,
            leader=form.leader.data,
            leader_user_id=form.leader_user_id.data if form.leader_user_id.data != 0 else None
        )
        db.session.add(ministry)
        db.session.commit()
        flash(f'Ministry "{ministry.name}" created!', 'success')
        return redirect(url_for('ministries.list_ministries'))
    return render_template('ministries/form.html', form=form, title='Add Ministry')


@ministries_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ministry(id):
    ministry = Ministry.query.get_or_404(id)
    form = MinistryForm(obj=ministry)
    if form.validate_on_submit():
        ministry.name = form.name.data
        ministry.description = form.description.data
        ministry.leader = form.leader.data
        ministry.leader_user_id = form.leader_user_id.data if form.leader_user_id.data != 0 else None
        db.session.commit()
        flash(f'Ministry "{ministry.name}" updated!', 'success')
        return redirect(url_for('ministries.list_ministries'))
    return render_template('ministries/form.html', form=form, title='Edit Ministry', ministry=ministry)


@ministries_bp.route('/view/<int:id>')
@login_required
def view_ministry(id):
    ministry = Ministry.query.get_or_404(id)
    members = Member.query.filter_by(ministry_id=id).all()
    unassigned_members = Member.query.filter(
        (Member.ministry_id != id) | (Member.ministry_id.is_(None))
    ).filter_by(membership_status='Active').all()
    return render_template('ministries/view.html', ministry=ministry, members=members,
                          unassigned_members=unassigned_members,
                          can_edit=is_ministry_leader(ministry))


@ministries_bp.route('/assign/<int:id>', methods=['POST'])
@login_required
@admin_required
def assign_member(id):
    ministry = Ministry.query.get_or_404(id)
    member_id = request.form.get('member_id', type=int)
    if member_id:
        member = Member.query.get(member_id)
        if member:
            member.ministry_id = id
            db.session.commit()
            flash(f'{member.full_name()} assigned to {ministry.name}.', 'success')
    return redirect(url_for('ministries.view_ministry', id=id))


@ministries_bp.route('/remove/<int:ministry_id>/<int:member_id>')
@login_required
@admin_required
def remove_member(ministry_id, member_id):
    ministry = Ministry.query.get_or_404(ministry_id)
    member = Member.query.get_or_404(member_id)
    if member.ministry_id == ministry_id:
        member.ministry_id = None
        db.session.commit()
        flash(f'{member.full_name()} removed from {ministry.name}.', 'info')
    return redirect(url_for('ministries.view_ministry', id=ministry_id))


@ministries_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_ministry(id):
    ministry = Ministry.query.get_or_404(id)
    Member.query.filter_by(ministry_id=id).update({Member.ministry_id: None})
    db.session.delete(ministry)
    db.session.commit()
    flash(f'Ministry "{ministry.name}" deleted.', 'info')
    return redirect(url_for('ministries.list_ministries'))
