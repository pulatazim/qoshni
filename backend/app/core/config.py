"""Iloha sozlamalari: muhit o'zgaruvchilari va .env faylidan o'qiladi."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Qo'shni API"
    environment: str = "dev"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://qoshni:qoshni@localhost:5432/qoshni"
    redis_url: str = "redis://localhost:6379/0"

    # Telegram Mini App: initData HMAC tekshiruvi shu token bilan bo'ladi.
    telegram_bot_token: SecretStr | None = None
    # initData necha soniyagacha yaroqli hisoblanadi (dizayn: 24 soat).
    init_data_max_age_seconds: int = 86400

    # JWT: ishlab chiqarish/tekshirish kaliti va muddati.
    jwt_secret: SecretStr = SecretStr("dev-only-insecure-secret-change-me-0123456789abcdef")
    jwt_algorithm: str = "HS256"
    jwt_ttl_days: int = 7

    # --- Cloudflare R2: e'lon rasmlari shu yerda turadi (S3 mos API) ---
    r2_account_id: str | None = None
    r2_bucket: str = "qoshni"
    r2_access_key_id: str | None = None
    r2_secret_access_key: SecretStr | None = None
    # Ommaviy o'qish manzili: r2.dev yoki cdn domeni. Bo'sh bo'lsa URL qaytarilmaydi.
    r2_public_base_url: str = ""

    # --- Cheklovlar (spam va suiiste'moldan himoya) ---
    # "redis" — production/lockal compose; "memory" — Redis'siz ish yoki test.
    rate_limit_backend: str = "redis"
    api_requests_per_minute: int = 60
    listings_per_day: int = 20

    def bot_token(self) -> str | None:
        """Bot tokenini ochiq ko'rinishda qaytaradi; sozlanmagan bo'lsa None."""
        if self.telegram_bot_token is None:
            return None
        return self.telegram_bot_token.get_secret_value()

    @property
    def jwt_signing_key(self) -> str:
        return self.jwt_secret.get_secret_value()

    @property
    def storage_configured(self) -> bool:
        """R2 kalitlari to'liq bo'lsa haqiqiy saqlagich ishlatiladi."""
        return bool(self.r2_account_id and self.r2_access_key_id and self.r2_secret_access_key)

    @property
    def r2_endpoint_url(self) -> str:
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    @property
    def r2_secret_key(self) -> str:
        assert self.r2_secret_access_key is not None
        return self.r2_secret_access_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
