from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('super_admin', 'church_admin')(f)


def super_admin_required(f):
    return role_required('super_admin')(f)


def ministry_leader_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role not in ('super_admin', 'church_admin', 'ministry_leader'):
            flash('You do not have permission to access this page.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def is_ministry_leader(ministry):
    if current_user.role in ('super_admin', 'church_admin'):
        return True
    if current_user.role == 'ministry_leader':
        return ministry.leader_user_id == current_user.id
    return False
