from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User
from app.forms import UserForm
from app.utils.decorators import super_admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@login_required
@super_admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    query = User.query
    if role_filter:
        query = query.filter(User.role == role_filter)
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users, role_filter=role_filter)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@super_admin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        if not form.password.data:
            flash('Password is required for new users.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Add User')
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created!', 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/user_form.html', form=form, title='Add User')


@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash(f'User {user.username} updated!', 'success')
        return redirect(url_for('admin.list_users'))
    form.password.data = ''
    return render_template('admin/user_form.html', form=form, title='Edit User', user=user)


@admin_bp.route('/users/delete/<int:id>')
@login_required
@super_admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.list_users'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted.', 'info')
    return redirect(url_for('admin.list_users'))
