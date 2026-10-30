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

        # Managed Postgres providers (Render external DB, Neon, Supabase, etc.)
        # sit behind TLS. Append sslmode=require when connecting to a remote host
        # that does not already specify connection parameters in the query string.
        if (
            DATABASE_URL.startswith("postgresql://")
            and "@" in DATABASE_URL
            and "?" not in DATABASE_URL
        ):
            host_part = DATABASE_URL.split("@", 1)[1].split("/", 1)[0]
            hostname = host_part.split(":", 1)[0]
            if (
                hostname not in ("localhost", "127.0.0.1", "0.0.0.0")
                and "." in hostname
            ):
                DATABASE_URL = DATABASE_URL + "?sslmode=require"

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:
        # Local development database
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///" + os.path.join(BASE_DIR, "church.db")
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # NOTE: Do NOT set SERVER_NAME in production on platforms like Render.
    # Flask's SERVER_NAME requires every request host to match exactly, which
    # breaks routing when the platform's internal hostname differs (causes 404 on ALL routes).
    # Use PREFERRED_URL_SCHEME for https:// links in emails instead.
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
    # SMS
    # -----------------------------
    SMS_API_URL = os.environ.get("SMS_API_URL")
    SMS_API_KEY = os.environ.get("SMS_API_KEY")

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