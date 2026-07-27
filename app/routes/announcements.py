import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Announcement, AnnouncementRead, Notification, User
from app.forms import AnnouncementForm
from app.utils.decorators import admin_required
from app.utils.helpers import save_announcement_image, delete_file

announcements_bp = Blueprint('announcements', __name__, url_prefix='/announcements')


@announcements_bp.route('/')
@login_required
def list_announcements():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')

    query = Announcement.query
    if category_filter:
        query = query.filter(Announcement.category == category_filter)
    if status_filter:
        query = query.filter(Announcement.status == status_filter)

    announcements = query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=10)
    categories = ['General', 'Events', 'Meetings', 'Prayer', 'Emergency']

    read_ids = set()
    if current_user.role == 'member':
        reads = AnnouncementRead.query.filter_by(user_id=current_user.id).all()
        read_ids = {r.announcement_id for r in reads}

    return render_template('announcements/list.html', announcements=announcements,
                          categories=categories, category_filter=category_filter,
                          status_filter=status_filter, read_ids=read_ids)


@announcements_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = save_announcement_image(form.image.data)

        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            author_id=current_user.id,
            status=form.status.data,
            image=image_filename,
            author_name=form.author_name.data,
            scheduled_date=form.scheduled_date.data
        )
        db.session.add(announcement)
        db.session.commit()

        if form.status.data == 'Published':
            members = User.query.filter(User.role == 'member', User.is_active == True).all()
            for user in members:
                db.session.add(Notification(
                    title=f'New Announcement: {announcement.title}',
                    message=announcement.content[:200],
                    notification_type='In-App',
                    recipient_id=user.id,
                    sender_id=current_user.id
                ))
            db.session.commit()

        flash('Announcement created!', 'success')
        return redirect(url_for('announcements.list_announcements'))
    return render_template('announcements/form.html', form=form, title='Add Announcement')


@announcements_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    form = AnnouncementForm(obj=announcement)
    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.content = form.content.data
        announcement.category = form.category.data
        announcement.status = form.status.data
        announcement.author_name = form.author_name.data
        announcement.scheduled_date = form.scheduled_date.data

        if form.image.data:
            if announcement.image:
                delete_file(announcement.image, 'announcement_images')
            announcement.image = save_announcement_image(form.image.data)

        db.session.commit()

        if announcement.status == 'Published':
            members = User.query.filter(User.role == 'member', User.is_active == True).all()
            for user in members:
                existing = Notification.query.filter_by(
                    recipient_id=user.id,
                    title=f'New Announcement: {announcement.title}'
                ).first()
                if not existing:
                    db.session.add(Notification(
                        title=f'New Announcement: {announcement.title}',
                        message=announcement.content[:200],
                        notification_type='In-App',
                        recipient_id=user.id,
                        sender_id=current_user.id
                    ))
            db.session.commit()

        flash('Announcement updated!', 'success')
        return redirect(url_for('announcements.list_announcements'))
    return render_template('announcements/form.html', form=form, title='Edit Announcement',
                          announcement=announcement)


@announcements_bp.route('/view/<int:id>')
@login_required
def view_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    existing = AnnouncementRead.query.filter_by(announcement_id=id, user_id=current_user.id).first()
    if not existing and current_user.role == 'member':
        read = AnnouncementRead(announcement_id=id, user_id=current_user.id)
        db.session.add(read)
        db.session.commit()
    read_count = AnnouncementRead.query.filter_by(announcement_id=id).count()
    return render_template('announcements/view.html', announcement=announcement, read_count=read_count)


@announcements_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if announcement.image:
        delete_file(announcement.image, 'announcement_images')
    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('announcements.list_announcements'))
