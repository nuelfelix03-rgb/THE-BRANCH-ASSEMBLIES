from app.models import User, Ministry, ChurchSettings
from app import db


def seed_data():
    if User.query.first() is None:
        admin = User(
            username='admin',
            email='admin@church.com',
            role='super_admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        default_ministries = [
            'Choir', 'Ushering', 'Youth Ministry', 'Children\'s Church',
            'Evangelism Team', 'Media Department', 'Prayer Team', 'Hospitality'
        ]
        for name in default_ministries:
            ministry = Ministry(name=name)
            db.session.add(ministry)

        db.session.commit()

    if ChurchSettings.query.first() is None:
        settings = ChurchSettings(
            church_name='My Church',
            church_address='',
            church_phone='',
            church_email='',
            service_times='Sunday Service: 9:00 AM\nWednesday Prayer: 7:00 PM',
            welcome_message='Welcome to our church!'
        )
        db.session.add(settings)
        db.session.commit()
