from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Debug: Remove this after confirming PostgreSQL is connected
    print("DATABASE:", app.config["SQLALCHEMY_DATABASE_URI"])

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.members import members_bp
    from app.routes.attendance import attendance_bp
    from app.routes.ministries import ministries_bp
    from app.routes.announcements import announcements_bp
    from app.routes.events import events_bp
    from app.routes.reports import reports_bp
    from app.routes.notifications import notifications_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.settings import settings_bp
    from app.routes.church_info import church_info_bp
    from app.routes.api import api_bp
    from app.routes.giving import giving_bp
    from app.routes.qr_attendance import qr_bp
    from app.routes.member_profile_ext import profile_ext_bp
    from app.routes.member_search import search_bp
    from app.routes.dashboard_ext import dash_ext_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(ministries_bp)
    app.register_blueprint(announcements_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(church_info_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(giving_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(profile_ext_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(dash_ext_bp)

    # Session configuration
    if app.config.get("SERVER_NAME"):
        app.config["SESSION_COOKIE_DOMAIN"] = app.config["SERVER_NAME"]

    # Error pages
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    # Context processors
    @app.context_processor
    def inject_now():
        return {"now": datetime.now}

    @app.context_processor
    def inject_settings():
        from app.models import ChurchSettings, User
        settings = ChurchSettings.get_settings()
        admin = User.query.filter(User.role.in_(['super_admin', 'admin'])).order_by(User.id).first()
        return {
            "church_settings": settings,
            "church_logo": admin.profile_picture if admin and admin.profile_picture else None,
        }

    # Create tables if they don't exist
    with app.app_context():
        from app import models
        from app.models_ext import FamilyMember, MemberSkill, MemberDocument, BaptismRecord, Giving, QRCodeAttendance, ServiceSchedule
        db.create_all()

        # Migrate existing tables with new columns (SQLite doesn't auto-alter)
        from sqlalchemy import inspect, text as sa_text
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            member_cols = {
                'profession': 'VARCHAR(200)', 'is_student': 'VARCHAR(10)',
                'school': 'VARCHAR(200)', 'faculty': 'VARCHAR(200)',
                'department': 'VARCHAR(200)', 'level': 'VARCHAR(50)',
                'accommodation': 'VARCHAR(50)', 'hostel_name': 'VARCHAR(200)',
                'room_number': 'VARCHAR(50)', 'previous_church': 'VARCHAR(200)',
                'how_heard': 'VARCHAR(100)', 'friend_name': 'VARCHAR(100)',
                'other_source': 'VARCHAR(200)', 'preferred_social_platform': 'VARCHAR(100)',
                'social_handle': 'VARCHAR(100)',
            }
            if 'members' in tables:
                existing = {c['name'] for c in inspector.get_columns('members')}
                for col, typ in member_cols.items():
                    if col not in existing:
                        db.session.execute(sa_text(f'ALTER TABLE members ADD COLUMN {col} {typ}'))
            if 'announcements' in tables:
                existing = {c['name'] for c in inspector.get_columns('announcements')}
                if 'image' not in existing:
                    db.session.execute(sa_text('ALTER TABLE announcements ADD COLUMN image VARCHAR(255)'))
                if 'author_name' not in existing:
                    db.session.execute(sa_text('ALTER TABLE announcements ADD COLUMN author_name VARCHAR(100)'))
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app