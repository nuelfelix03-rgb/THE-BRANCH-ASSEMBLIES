import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # -----------------------------
    # Security
    # -----------------------------
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    # -----------------------------
    # Database Configuration
    # -----------------------------
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        # Render/Railway compatibility
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql://",
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:
        # Local development database
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///" + os.path.join(BASE_DIR, "church.db")
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------
    # Server
    # -----------------------------
    SERVER_NAME = os.environ.get("SERVER_NAME")
    PREFERRED_URL_SCHEME = os.environ.get(
        "PREFERRED_URL_SCHEME",
        "https"
    )

    # -----------------------------
    # Email
    # -----------------------------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # -----------------------------
    # Uploads
    # -----------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Base folder that contains user uploads (uploads/, announcement_images/, member_docs/).
    # Override with UPLOAD_DIR or RENDER_DISK_PATH to point at a PERSISTENT disk
    # (e.g. a Render Disk) so uploaded files survive every redeploy.
    UPLOAD_BASE_DIR = os.environ.get(
        "UPLOAD_DIR",
        os.environ.get(
            "RENDER_DISK_PATH",
            os.path.join(BASE_DIR, "app", "static")
        )
    )

    UPLOAD_FOLDER = os.path.join(UPLOAD_BASE_DIR, "uploads")

    for _sub in ("uploads", "announcement_images", "member_docs"):
        os.makedirs(os.path.join(UPLOAD_BASE_DIR, _sub), exist_ok=True)

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # -----------------------------
    # Cookies
    # -----------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Secure cookies only in production
    SESSION_COOKIE_SECURE = os.environ.get(
        "SESSION_COOKIE_SECURE",
        "False"
    ).lower() == "true"