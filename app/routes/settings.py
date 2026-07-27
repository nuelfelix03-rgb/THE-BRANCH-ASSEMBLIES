from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import ChurchSettings
from app.forms import ChurchSettingsForm
from app.utils.decorators import super_admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@super_admin_required
def index():
    church_settings = ChurchSettings.get_settings()
    form = ChurchSettingsForm(obj=church_settings)
    if form.validate_on_submit():
        church_settings.church_name = form.church_name.data
        church_settings.church_address = form.church_address.data
        church_settings.church_phone = form.church_phone.data
        church_settings.church_email = form.church_email.data
        church_settings.service_times = form.service_times.data
        church_settings.welcome_message = form.welcome_message.data
        db.session.commit()
        flash('Church settings saved!', 'success')
        return redirect(url_for('settings.index'))
    return render_template('settings/index.html', form=form, settings=church_settings)
