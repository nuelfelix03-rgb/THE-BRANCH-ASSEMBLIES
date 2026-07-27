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

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

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
    from app.routes.church_info import church_info_bp
    app.register_blueprint(church_info_bp)
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)

    # Override SERVER_NAME at runtime for context processors that build absolute URLs
    if app.config.get('SERVER_NAME'):
        app.config['SESSION_COOKIE_DOMAIN'] = app.config['SERVER_NAME']

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    @app.context_processor
    def inject_settings():
        from app.models import ChurchSettings
        settings = ChurchSettings.get_settings()
        return {'church_settings': settings}

    with app.app_context():
        from app import models
        db.create_all()

        from app.utils.seed import seed_data
        seed_data()

    return app
