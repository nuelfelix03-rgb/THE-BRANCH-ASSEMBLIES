from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import ChurchInformation, Notification, User
from app.forms import ChurchInformationForm
from app.utils.decorators import admin_required

church_info_bp = Blueprint('church_info', __name__, url_prefix='/church-info')


@church_info_bp.route('/')
@login_required
@admin_required
def list_info():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    search_query = request.args.get('q', '')

    query = ChurchInformation.query

    if category_filter:
        query = query.filter(ChurchInformation.category == category_filter)
    if search_query:
        query = query.filter(ChurchInformation.title.ilike(f'%{search_query}%'))

    infos = query.order_by(ChurchInformation.display_order, ChurchInformation.updated_at.desc()).paginate(page=page, per_page=20)

    from app.models import CHURCH_INFO_CATEGORIES

    return render_template('church_info/list.html', infos=infos,
                          categories=CHURCH_INFO_CATEGORIES,
                          category_filter=category_filter,
                          search_query=search_query)


@church_info_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_info():
    form = ChurchInformationForm()
    if form.validate_on_submit():
        info = ChurchInformation(
            title=form.title.data,
            category=form.category.data,
            content=form.content.data,
            display_order=form.display_order.data,
            is_published=form.is_published.data,
            created_by=current_user.id
        )
        db.session.add(info)
        db.session.commit()

        if info.is_published:
            members = User.query.filter(User.role == 'member', User.is_active == True).all()
            for user in members:
                db.session.add(Notification(
                    title='New Church Information Available',
                    message=f'"{info.title}" has been published.',
                    notification_type='In-App',
                    recipient_id=user.id,
                    sender_id=current_user.id
                ))
            db.session.commit()

        flash('Church information created!', 'success')
        return redirect(url_for('church_info.list_info'))
    return render_template('church_info/form.html', form=form, title='Add Information')


@church_info_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_info(id):
    info = ChurchInformation.query.get_or_404(id)
    form = ChurchInformationForm(obj=info)
    if form.validate_on_submit():
        was_unpublished = not info.is_published
        info.title = form.title.data
        info.category = form.category.data
        info.content = form.content.data
        info.display_order = form.display_order.data
        info.is_published = form.is_published.data
        db.session.commit()

        if info.is_published and was_unpublished:
            members = User.query.filter(User.role == 'member', User.is_active == True).all()
            for user in members:
                db.session.add(Notification(
                    title='New Church Information Available',
                    message=f'"{info.title}" has been published.',
                    notification_type='In-App',
                    recipient_id=user.id,
                    sender_id=current_user.id
                ))
            db.session.commit()

        flash('Church information updated!', 'success')
        return redirect(url_for('church_info.list_info'))
    return render_template('church_info/form.html', form=form, title='Edit Information', info=info)


@church_info_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_info(id):
    info = ChurchInformation.query.get_or_404(id)
    db.session.delete(info)
    db.session.commit()
    flash('Information deleted.', 'info')
    return redirect(url_for('church_info.list_info'))


@church_info_bp.route('/toggle/<int:id>')
@login_required
@admin_required
def toggle_publish(id):
    info = ChurchInformation.query.get_or_404(id)
    info.is_published = not info.is_published
    db.session.commit()

    if info.is_published:
        members = User.query.filter(User.role == 'member', User.is_active == True).all()
        for user in members:
            db.session.add(Notification(
                title='New Church Information Available',
                message=f'"{info.title}" has been published.',
                notification_type='In-App',
                recipient_id=user.id,
                sender_id=current_user.id
            ))
        db.session.commit()

    status = 'published' if info.is_published else 'unpublished'
    flash(f'Information {status}.', 'success')
    return redirect(url_for('church_info.list_info'))


@church_info_bp.route('/view')
@login_required
def view_info():
    category_filter = request.args.get('category', '')
    search_query = request.args.get('q', '')

    query = ChurchInformation.query.filter_by(is_published=True)

    if category_filter:
        query = query.filter(ChurchInformation.category == category_filter)
    if search_query:
        query = query.filter(ChurchInformation.title.ilike(f'%{search_query}%'))

    infos = query.order_by(ChurchInformation.display_order, ChurchInformation.updated_at.desc()).all()

    from app.models import CHURCH_INFO_CATEGORIES

    return render_template('church_info/member_view.html', infos=infos,
                          categories=CHURCH_INFO_CATEGORIES,
                          category_filter=category_filter,
                          search_query=search_query)
