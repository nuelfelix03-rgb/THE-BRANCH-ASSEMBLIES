from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    with app.test_client() as c:
        resp = c.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123'})
        data = resp.get_json()
        print('Login status:', resp.status_code)
        print('Has token:', 'token' in data)
        token = data.get('token', '')

        endpoints = [
            ('/api/v1/dashboard', 'Dashboard'),
            ('/api/v1/members', 'Members'),
            ('/api/v1/events', 'Events'),
            ('/api/v1/announcements', 'Announcements'),
            ('/api/v1/church-info', 'Church Info'),
            ('/api/v1/notifications', 'Notifications'),
            ('/api/v1/settings', 'Settings'),
            ('/api/v1/attendance/stats', 'Attendance Stats'),
            ('/api/v1/ministries', 'Ministries'),
            ('/api/v1/reports/attendance', 'Reports Attendance'),
            ('/api/v1/reports/members', 'Reports Members'),
        ]
        all_ok = True
        for url, name in endpoints:
            resp = c.get(url, headers={'Authorization': f'Bearer {token}'})
            ok = resp.status_code in (200, 201)
            status = 'OK' if ok else f'FAIL ({resp.status_code})'
            print(f'  {name:25s} {status}')
            if not ok:
                all_ok = False
        print()
        print('All API endpoints OK!' if all_ok else 'Some endpoints FAILED!')
