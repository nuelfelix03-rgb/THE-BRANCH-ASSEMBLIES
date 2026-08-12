from datetime import date, timedelta

from app import db
from app.models import Member, Notification, User

ADMIN_ROLE_NAMES = ('super_admin', 'pastor', 'church_secretary', 'finance', 'ministry_leader')


def _next_birthday(member, today):
    """Return the next birthday date (this year or next) for a member, or None."""
    if not member.date_of_birth:
        return None
    dob = member.date_of_birth
    try:
        birthday = date(today.year, dob.month, dob.day)
    except ValueError:
        birthday = date(today.year, dob.month, 28)
    if birthday < today:
        year = today.year + 1
        try:
            birthday = date(year, dob.month, dob.day)
        except ValueError:
            birthday = date(year, dob.month, 28)
    return birthday


def get_todays_birthdays():
    today = date.today()
    members = Member.query.filter_by(membership_status='Active').all()
    return [
        m for m in members
        if m.date_of_birth
        and m.date_of_birth.month == today.month
        and m.date_of_birth.day == today.day
    ]


def get_birthdays_in_month(month=None, year=None):
    today = date.today()
    month = month or today.month
    year = year or today.year
    members = Member.query.filter_by(membership_status='Active').all()
    return [
        m for m in members
        if m.date_of_birth and m.date_of_birth.month == month and m.date_of_birth.year <= year
    ]


def get_upcoming_birthdays(days=30):
    today = date.today()
    end = today + timedelta(days=days)
    rows = []
    for m in Member.query.filter_by(membership_status='Active').all():
        bd = _next_birthday(m, today)
        if bd and today <= bd <= end:
            rows.append((m, bd))
    rows.sort(key=lambda x: x[1])
    return rows


def ensure_today_notifications():
    """Create one in-app notification per admin listing today's birthdays (once per day)."""
    today = date.today()
    birthdays = get_todays_birthdays()
    if not birthdays:
        return 0
    title = f"Birthdays Today - {today.strftime('%B %d')}"
    names = ', '.join(m.full_name() for m in birthdays)
    message = f"{len(birthdays)} member(s) celebrate a birthday today: {names}"
    created = 0
    admins = User.query.filter(
        User.role.in_(ADMIN_ROLE_NAMES),
        User.is_active == True,  # noqa: E712
    ).all()
    for admin in admins:
        exists = Notification.query.filter_by(
            recipient_id=admin.id, title=title
        ).first()
        if not exists:
            db.session.add(Notification(
                title=title,
                message=message,
                notification_type='In-App',
                recipient_id=admin.id,
            ))
            created += 1
    if created:
        db.session.commit()
    return created


def send_birthday_emails(dry_run=False):
    """Send a birthday-wish email to every active member whose birthday is today."""
    from app.utils.notifications import send_birthday_wish

    birthdays = get_todays_birthdays()
    sent = skipped = 0
    for m in birthdays:
        if not m.email:
            skipped += 1
            continue
        if not dry_run:
            send_birthday_wish(m)
        sent += 1
    return sent, skipped
