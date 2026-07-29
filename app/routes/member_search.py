from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Member, Ministry
from app.utils.roles import role_required, ADMIN_ROLES
from sqlalchemy import or_

search_bp = Blueprint('member_search', __name__, url_prefix='/members')


@search_bp.route('/search', methods=['GET'])
@login_required
@role_required(*ADMIN_ROLES)
def search_members():
    q = request.args.get('q', '').strip()
    gender = request.args.get('gender', '')
    ministry_id = request.args.get('ministry_id', '', type=int)
    status = request.args.get('status', '')
    occupation = request.args.get('occupation', '')
    page = request.args.get('page', 1, type=int)

    query = Member.query

    if q:
        terms = q.split()
        filters = []
        for term in terms:
            pattern = f'%{term}%'
            filters.append(or_(
                Member.first_name.ilike(pattern),
                Member.last_name.ilike(pattern),
                Member.middle_name.ilike(pattern),
                Member.member_id.ilike(pattern),
                Member.phone_number.ilike(pattern),
                Member.email.ilike(pattern),
                Member.profession.ilike(pattern)
            ))
        query = query.filter(or_(*filters))

    if gender:
        query = query.filter(Member.gender == gender)
    if ministry_id:
        query = query.filter(Member.ministry_id == ministry_id)
    if status:
        query = query.filter(Member.membership_status == status)
    if occupation:
        query = query.filter(Member.profession.ilike(f'%{occupation}%'))

    members = query.order_by(Member.first_name).paginate(page=page, per_page=20)
    ministries = Ministry.query.order_by(Ministry.name).all()
    statuses = ['Active', 'Inactive', 'Transfer', 'Former']

    return render_template('members/search.html', members=members, q=q,
                          gender=gender, ministry_id=ministry_id,
                          status=status, occupation=occupation,
                          ministries=ministries, statuses=statuses)


@search_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    members = Member.query.filter(
        or_(
            Member.first_name.ilike(f'%{q}%'),
            Member.last_name.ilike(f'%{q}%'),
            Member.member_id.ilike(f'%{q}%'),
            Member.phone_number.ilike(f'%{q}%')
        )
    ).limit(10).all()

    return jsonify([{
        'id': m.id,
        'member_id': m.member_id,
        'name': m.full_name(),
        'phone': m.phone_number,
        'email': m.email
    } for m in members])
