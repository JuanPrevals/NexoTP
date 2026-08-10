from dataclasses import dataclass
from pathlib import Path
import os
import secrets


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = (BACKEND_DIR / "instance" / "nexotp.db").as_posix()


def _origins() -> tuple[str, ...]:
    raw = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return tuple(value.strip().rstrip("/") for value in raw.split(",") if value.strip())


@dataclass(frozen=True)
class Settings:
    environment: str
    secret_key: str
    admin_password_hash: str
    database_url: str
    allowed_origins: tuple[str, ...]
    secure_cookies: bool


def load_settings() -> Settings:
    environment = os.environ.get("APP_ENV", "development").lower()
    production = environment == "production"
    secret_key = os.environ.get("SECRET_KEY", "")
    admin_password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")

    if production and (len(secret_key) < 32 or not admin_password_hash):
        raise RuntimeError(
            "Produccion requiere SECRET_KEY (minimo 32 caracteres) y ADMIN_PASSWORD_HASH."
        )

    return Settings(
        environment=environment,
        secret_key=secret_key or secrets.token_urlsafe(48),
        admin_password_hash=admin_password_hash,
        database_url=os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE}"),
        allowed_origins=_origins(),
        secure_cookies=production,
    )


settings = load_settings()
