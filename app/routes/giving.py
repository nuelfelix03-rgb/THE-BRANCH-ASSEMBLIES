import uuid
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Member
from app.models_ext import Giving
from app.utils.roles import role_required, FINANCE_ROLES, ADMIN_ROLES

giving_bp = Blueprint('giving', __name__, url_prefix='/giving')


@giving_bp.route('/')
@login_required
@role_required(*ADMIN_ROLES)
def list_givings():
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', '')
    start = request.args.get('start', '')
    end = request.args.get('end', '')

    query = Giving.query
    if type_filter:
        query = query.filter(Giving.giving_type == type_filter)
    if start:
        query = query.filter(Giving.date >= date.fromisoformat(start))
    if end:
        query = query.filter(Giving.date <= date.fromisoformat(end))

    givings = query.order_by(Giving.date.desc()).paginate(page=page, per_page=20)
    total = sum(g.amount for g in givings.items) if hasattr(givings, 'items') else 0
    grand_total = db.session.query(db.func.sum(Giving.amount)).scalar() or 0
    types = ['Tithe', 'Offering', 'First Fruits', 'Thanksgiving', 'Building Fund', 'Missions', 'Special', 'Other']

    return render_template('giving/list.html', givings=givings, types=types,
                          type_filter=type_filter, start=start, end=end,
                          total=total, grand_total=grand_total)


@giving_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required(*FINANCE_ROLES)
def add_giving():
    from flask_wtf import FlaskForm
    from wtforms import FloatField, SelectField, StringField, DateField, TextAreaField, SubmitField
    from wtforms.validators import DataRequired, Optional

    class GivingForm(FlaskForm):
        member_id = StringField('Member ID (optional)')
        giver_name = StringField('Giver Name', validators=[Optional()])
        amount = FloatField('Amount', validators=[DataRequired()])
        giving_type = SelectField('Giving Type', choices=[
            ('Tithe', 'Tithe'), ('Offering', 'Offering'),
            ('First Fruits', 'First Fruits'), ('Thanksgiving', 'Thanksgiving'),
            ('Building Fund', 'Building Fund'), ('Missions', 'Missions'),
            ('Special', 'Special'), ('Other', 'Other')
        ])
        payment_method = SelectField('Payment Method', choices=[
            ('Cash', 'Cash'), ('Bank Transfer', 'Bank Transfer'),
            ('Mobile Money', 'Mobile Money'), ('Card', 'Card'),
            ('Cheque', 'Cheque'), ('Online', 'Online')
        ])
        phone = StringField('Phone', validators=[Optional()])
        email = StringField('Email', validators=[Optional()])
        notes = TextAreaField('Notes', validators=[Optional()])
        date = DateField('Date', default=date.today)
        submit = SubmitField('Record Giving')

    form = GivingForm()
    if form.validate_on_submit():
        mid = form.member_id.data
        member = None
        if mid:
            member = Member.query.filter_by(member_id=mid).first()
            if not member:
                flash('Member ID not found. Recording as anonymous.', 'warning')

        giving = Giving(
            member_id=member.id if member else None,
            giver_name=form.giver_name.data or (member.full_name() if member else None),
            amount=form.amount.data,
            giving_type=form.giving_type.data,
            payment_method=form.payment_method.data,
            transaction_ref=uuid.uuid4().hex[:12].upper(),
            phone=form.phone.data,
            email=form.email.data,
            notes=form.notes.data,
            date=form.date.data
        )
        db.session.add(giving)
        db.session.commit()
        flash(f'Giving recorded: {giving.giving_type} of {giving.amount}', 'success')
        return redirect(url_for('giving.list_givings'))

    return render_template('giving/form.html', form=form)


@giving_bp.route('/stats')
@login_required
@role_required(*FINANCE_ROLES)
def giving_stats():
    today = date.today()
    first_of_month = today.replace(day=1)

    monthly = db.session.query(
        db.func.strftime('%Y-%m', Giving.date).label('month'),
        db.func.sum(Giving.amount).label('total'),
        db.func.count(Giving.id).label('count')
    ).filter(Giving.date >= first_of_month.replace(month=first_of_month.month - 6 if first_of_month.month > 6 else first_of_month.month)) \
     .group_by('month').order_by('month').all()

    by_type = db.session.query(
        Giving.giving_type,
        db.func.sum(Giving.amount).label('total'),
        db.func.count(Giving.id).label('count')
    ).group_by(Giving.giving_type).all()

    today_total = db.session.query(db.func.sum(Giving.amount)).filter(Giving.date == today).scalar() or 0
    month_total = db.session.query(db.func.sum(Giving.amount)).filter(Giving.date >= first_of_month).scalar() or 0

    return render_template('giving/stats.html', monthly=monthly, by_type=by_type,
                          today_total=today_total, month_total=month_total)
