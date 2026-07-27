from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_mail import Message
from app import db, mail
from app.models import Notification, User
from app.forms import NotificationForm
from app.utils.decorators import admin_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def list_notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('notifications/list.html', notifications=notifications)


@notifications_bp.route('/send', methods=['GET', 'POST'])
@login_required
@admin_required
def send_notification():
    form = NotificationForm()
    if form.validate_on_submit():
        users = User.query.filter(User.id != current_user.id).all()
        email_sent = 0
        for user in users:
            notification = Notification(
                title=form.title.data,
                message=form.message.data,
                notification_type=form.notification_type.data,
                recipient_id=user.id,
                sender_id=current_user.id
            )
            db.session.add(notification)

            if form.notification_type.data == 'Email' and user.email:
                try:
                    msg = Message(form.title.data,
                        recipients=[user.email])
                    msg.body = form.message.data
                    mail.send(msg)
                    email_sent += 1
                except Exception:
                    pass
        db.session.commit()
        msg = 'Notification sent to all users!'
        if email_sent:
            msg += f' Emails sent to {email_sent} user(s).'
        flash(msg, 'success')
        return redirect(url_for('notifications.list_notifications'))
    return render_template('notifications/form.html', form=form, title='Send Notification')


@notifications_bp.route('/read/<int:id>')
@login_required
def mark_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.recipient_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/read-all')
@login_required
def mark_all_read():
    Notification.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).count()
    return {'count': count}
