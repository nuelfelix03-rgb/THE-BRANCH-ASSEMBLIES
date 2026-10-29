from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Member, Notification
from app.utils.birthday_service import (
    ensure_today_notifications,
    get_birthdays_in_month,
    get_todays_birthdays,
    get_upcoming_birthdays,
    resolve_delivery_email,
    send_birthday_emails,
)
from app.utils.notifications import send_email_sync, send_sms
from app.utils.roles import ADMIN_ROLES, role_required

msg_bp = Blueprint('messaging', __name__)


# === Upcoming Birthdays (admin) ===

@msg_bp.route('/birthdays')
@login_required
@role_required(*ADMIN_ROLES)
def birthdays():
    ensure_today_notifications()
    today = date.today()
    todays = get_todays_birthdays()
    upcoming = get_upcoming_birthdays(days=30)
    return render_template(
        'messaging/birthdays.html',
        today=today, todays=todays, upcoming=upcoming,
    )


@msg_bp.route('/birthdays/send', methods=['POST'])
@login_required
@role_required(*ADMIN_ROLES)
def send_birthday():
    member_id = request.form.get('member_id', type=int)
    channel = request.form.get('channel', 'email')
    member = Member.query.get_or_404(member_id)
    sent = []
    if channel in ('email', 'both'):
        to_email = resolve_delivery_email(member)
        if to_email:
            ok, err = send_email_sync(
                'Happy Birthday!',
                [to_email],
                f'Dear {member.full_name()},\n\nWishing you a blessed birthday! May God continue to shower you with His love and grace.\n\nWith love,\n{current_user.username}'
            )
            if ok:
                sent.append('email')
            else:
                flash(f'Email to {member.full_name()} failed: {err}', 'danger')
        else:
            flash(f'{member.full_name()} has no linked user account with an email.', 'warning')
    if channel in ('sms', 'both'):
        if member.phone_number:
            text = f"Happy Birthday {member.first_name}! Wishing you a blessed day."
            send_sms(member.phone_number, text)
            sent.append('SMS')
        else:
            flash(f'{member.full_name()} has no phone number on file.', 'warning')
    if sent:
        flash(f'Birthday wish sent to {member.full_name()} via ' + ', '.join(s.title() for s in sent) + '.', 'success')
    return redirect(request.referrer or url_for('messaging.birthdays'))


@msg_bp.route('/birthdays/send-all', methods=['POST'])
@login_required
@role_required(*ADMIN_ROLES)
def send_all_birthdays():
    sent, skipped = send_birthday_emails()
    note = f' {skipped} skipped (no email on file).' if skipped else ''
    flash(f'Sent birthday emails to {sent} member(s).{note}', 'success')
    return redirect(url_for('messaging.birthdays'))


# === General Email / SMS messaging (admin) ===

@msg_bp.route('/messages')
@login_required
@role_required(*ADMIN_ROLES)
def messages():
    return render_template('messaging/messages.html')


@msg_bp.route('/messages/send', methods=['POST'])
@login_required
@role_required(*ADMIN_ROLES)
def send_messages():
    subject = request.form.get('subject', '').strip()
    body = request.form.get('body', '').strip()
    channel = request.form.get('channel', 'email')
    audience = request.form.get('audience', 'all')

    if not subject or not body:
        flash('Subject and message are both required.', 'danger')
        return redirect(url_for('messaging.messages'))

    if audience == 'birthdays':
        members = get_todays_birthdays()
    elif audience == 'birthdays_month':
        members = get_birthdays_in_month()
    else:
        members = Member.query.filter_by(membership_status='Active').all()

    email_count = sms_count = no_contact = failed = 0
    first_error = None
    for m in members:
        if channel in ('email', 'both'):
            to_email = resolve_delivery_email(m)
            if to_email:
                ok, err = send_email_sync(subject, [to_email], body)
                if ok:
                    email_count += 1
                else:
                    failed += 1
                    if first_error is None:
                        first_error = err
            else:
                no_contact += 1
        if channel in ('sms', 'both'):
            if m.phone_number:
                send_sms(m.phone_number, f"{subject}\n{body[:160]}")
                sms_count += 1
            else:
                no_contact += 1

    result = f'Sent {email_count} email(s) and {sms_count} SMS to {len(members)} recipient(s).'
    if no_contact:
        result += f' {no_contact} skipped (no linked user email or phone).'
    if failed:
        result += f' {failed} email(s) FAILED to send.'
    flash(result, 'success' if failed == 0 else 'warning')
    if first_error:
        flash(f'Last error: {first_error}', 'danger')
    return redirect(url_for('messaging.messages'))


# === Session-based notifications (web bell) ===

@msg_bp.route('/notifications')
@login_required
def web_notifications():
    items = Notification.query.filter_by(recipient_id=current_user.id) \
        .order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({'notifications': [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'notification_type': n.notification_type,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%b %d, %H:%M') if n.created_at else '',
    } for n in items]})


@msg_bp.route('/notifications/unread-count')
@login_required
def web_unread_count():
    count = Notification.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@msg_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def web_mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return jsonify({'ok': True})
