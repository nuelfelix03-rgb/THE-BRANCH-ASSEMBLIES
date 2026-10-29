from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

SUPER_ADMIN = 'super_admin'
PASTOR = 'pastor'
SECRETARY = 'church_secretary'
FINANCE = 'finance'
MINISTRY_LEADER = 'ministry_leader'
MEMBER = 'member'

ROLES = [
    (SUPER_ADMIN, 'Super Admin'),
    (PASTOR, 'Pastor'),
    (SECRETARY, 'Church Secretary'),
    (FINANCE, 'Finance'),
    (MINISTRY_LEADER, 'Ministry Leader'),
    (MEMBER, 'Member'),
]

ROLE_HIERARCHY = {
    SUPER_ADMIN: 100,
    PASTOR: 80,
    SECRETARY: 60,
    FINANCE: 60,
    MINISTRY_LEADER: 40,
    MEMBER: 10,
}

ADMIN_ROLES = [SUPER_ADMIN, PASTOR, SECRETARY, FINANCE, MINISTRY_LEADER]

FINANCE_ROLES = [SUPER_ADMIN, FINANCE]


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def hierarchy_above(min_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in.', 'warning')
                return redirect(url_for('auth.login'))
            user_level = ROLE_HIERARCHY.get(current_user.role, 0)
            if user_level < min_level:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
