from datetime import date
from flask import current_app, render_template
from flask_mail import Message
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail = current_app.extensions.get('mail')
        if mail:
            mail.send(msg)


def send_email(subject, recipients, text_body, html_body=None):
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_birthday_wish(member):
    if not member.email:
        return
    subject = 'Happy Birthday!'
    text_body = f'Dear {member.full_name()},\n\nWishing you a blessed birthday! May God continue to shower you with His love and grace.\n\nWith love,\n{member.email}'
    html_body = f'''
    <div style="font-family:Arial;max-width:600px;margin:auto;padding:20px;border:1px solid #eee;border-radius:8px;">
        <h2 style="color:#C8102E;">Happy Birthday!</h2>
        <p>Dear <strong>{member.full_name()}</strong>,</p>
        <p>Wishing you a blessed and joyful birthday! May God continue to shower you with His love and grace this year.</p>
        <hr style="border:none;border-top:1px solid #eee;">
        <p style="color:#888;font-size:12px;">{current_app.config.get("CHURCH_NAME", "The Church")}</p>
    </div>'''
    send_email(subject, [member.email], text_body, html_body)


def send_event_reminder(event, recipients):
    subject = f'Reminder: {event.name}'
    text_body = f'This is a reminder for {event.name} on {event.start_date.strftime("%B %d, %Y at %I:%M %p")} at {event.venue or "Church"}.'
    html_body = f'''
    <div style="font-family:Arial;max-width:600px;margin:auto;padding:20px;border:1px solid #eee;border-radius:8px;">
        <h2 style="color:#C8102E;">Event Reminder</h2>
        <h3>{event.name}</h3>
        <p><strong>Date:</strong> {event.start_date.strftime("%B %d, %Y")}</p>
        <p><strong>Time:</strong> {event.start_date.strftime("%I:%M %p")}</p>
        <p><strong>Venue:</strong> {event.venue or "Church"}</p>
        {f"<p>{event.description}</p>" if event.description else ""}
        <hr style="border:none;border-top:1px solid #eee;">
        <p style="color:#888;font-size:12px;">We look forward to seeing you!</p>
    </div>'''
    send_email(subject, recipients, text_body, html_body)


def send_announcement_email(announcement, recipients):
    subject = announcement.title
    text_body = announcement.content[:500]
    html_body = f'''
    <div style="font-family:Arial;max-width:600px;margin:auto;padding:20px;border:1px solid #eee;border-radius:8px;">
        <h2 style="color:#C8102E;">{announcement.title}</h2>
        <p>{announcement.content[:2000]}</p>
        <hr style="border:none;border-top:1px solid #eee;">
        <p style="color:#888;font-size:12px;">{announcement.author_name or "Church Administration"}</p>
    </div>'''
    send_email(subject, recipients, text_body, html_body)


def send_sms(phone, message):
    if not phone:
        return
    clean = ''.join(c for c in phone if c.isdigit() or c == '+')
    app = current_app._get_current_object()
    with app.app_context():
        sms_api = current_app.config.get('SMS_API_URL')
        sms_key = current_app.config.get('SMS_API_KEY')
        if sms_api and sms_key:
            import requests
            try:
                requests.post(sms_api, json={
                    'to': clean,
                    'message': message,
                    'api_key': sms_key
                }, timeout=5)
            except Exception:
                pass
        else:
            print(f'SMS not configured. Would send to {clean}: {message}')
