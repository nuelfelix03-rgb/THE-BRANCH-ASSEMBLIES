from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Event
from app.forms import EventForm
from app.utils.decorators import admin_required

events_bp = Blueprint('events', __name__, url_prefix='/events')


@events_bp.route('/')
@login_required
def list_events():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = Event.query
    if status_filter:
        query = query.filter(Event.status == status_filter)
    else:
        query = query.filter(Event.status.in_(['Upcoming', 'Ongoing']))
    events = query.order_by(Event.start_date).paginate(page=page, per_page=10)
    return render_template('events/list.html', events=events, status_filter=status_filter)


@events_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            name=form.name.data,
            description=form.description.data,
            venue=form.venue.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            organizer=form.organizer.data,
            ministry_id=form.ministry_id.data if form.ministry_id.data != 0 else None,
            status=form.status.data,
            registration_required=form.registration_required.data
        )
        db.session.add(event)
        db.session.commit()
        flash(f'Event "{event.name}" created!', 'success')
        return redirect(url_for('events.list_events'))
    return render_template('events/form.html', form=form, title='Add Event')


@events_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(id):
    event = Event.query.get_or_404(id)
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.name = form.name.data
        event.description = form.description.data
        event.venue = form.venue.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.organizer = form.organizer.data
        event.ministry_id = form.ministry_id.data if form.ministry_id.data != 0 else None
        event.status = form.status.data
        event.registration_required = form.registration_required.data
        db.session.commit()
        flash(f'Event "{event.name}" updated!', 'success')
        return redirect(url_for('events.list_events'))
    return render_template('events/form.html', form=form, title='Edit Event', event=event)


@events_bp.route('/view/<int:id>')
@login_required
def view_event(id):
    event = Event.query.get_or_404(id)
    return render_template('events/view.html', event=event)


@events_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'info')
    return redirect(url_for('events.list_events'))


@events_bp.route('/calendar')
@login_required
def calendar():
    events = Event.query.filter(Event.status.in_(['Upcoming', 'Ongoing'])).all()
    return render_template('events/calendar.html', events=events)


@events_bp.route('/api/events')
@login_required
def api_events():
    events = Event.query.all()
    event_list = []
    for e in events:
        event_list.append({
            'id': e.id,
            'title': e.name,
            'start': e.start_date.isoformat() if e.start_date else '',
            'end': e.end_date.isoformat() if e.end_date else '',
            'description': e.description or ''
        })
    return jsonify(event_list)
