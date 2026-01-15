import base64
import json
from functools import lru_cache

from google.oauth2.service_account import Credentials
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """
    Единый класс конфигурации.
    Читает ПЛОСКИЙ .env файл и валидирует данные.
    """

    # --- GOOGLE SHEETS SETTINGS ---
    spreadsheet_id: str = Field(
        ...,
        validation_alias="SPREADSHEET_ID",
        description="ID Google Таблицы",
        min_length=10,
    )

    sheet_name: str = Field(
        "Заявки из Telegram Bot", validation_alias="SHEET_NAME"
    )

    category_column: int = Field(
        3, validation_alias="CATEGORY_COLUMN", ge=1, le=26
    )

    # --- GOOGLE CREDENTIALS ---
    # SecretStr скрывает значение при выводе в консоль (показывает '**********')
    google_credentials_base64: SecretStr = Field(
        ..., validation_alias="GOOGLE_CREDENTIALS_BASE64", min_length=50
    )

    # --- OPENROUTER / LLM ---
    openrouter_api_key: SecretStr = Field(
        SecretStr(""),  # Пустая строка по умолчанию, если ключа нет
        validation_alias="OPENROUTER_API_KEY",
    )

    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1", validation_alias="OPENROUTER_BASE_URL"
    )

    openrouter_model: str = Field(
        "openai/gpt-3.5-turbo", validation_alias="OPENROUTER_MODEL"
    )

    # --- APP SETTINGS ---
    debug: bool = Field(False, validation_alias="DEBUG")

    # --- НАСТРОЙКИ PYDANTIC ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорировать лишние переменные в .env
        case_sensitive=False,
    )

    # --- ВАЛИДАТОРЫ ---

    @field_validator("spreadsheet_id")
    @classmethod
    def validate_spreadsheet_id(cls, v: str) -> str:
        if "ваш_id" in v:
            raise ValueError("SPREADSHEET_ID не заполнен в .env файле")
        return v.strip()

    @field_validator("google_credentials_base64")
    @classmethod
    def validate_creds(cls, v: SecretStr) -> SecretStr:
        val = v.get_secret_value()
        if not val or "ваш_base64" in val:
            raise ValueError("GOOGLE_CREDENTIALS_BASE64 не заполнен")

        # Предварительная проверка валидности Base64 и JSON
        try:
            decoded = base64.b64decode(val, validate=True)
            data = json.loads(decoded)

            required = ["type", "project_id", "private_key", "client_email"]
            if any(f not in data for f in required):
                raise ValueError(
                    f"JSON ключа не содержит обязательных полей: {required}"
                )

        except Exception as e:
            raise ValueError(f"Ошибка декодирования Base64 ключа: {e}")

        return v

    # --- ПОЛЕЗНЫЕ МЕТОДЫ (HELPER METHODS) ---

    @property
    def is_llm_enabled(self) -> bool:
        """Включен ли ИИ?"""
        key = self.openrouter_api_key.get_secret_value()
        return bool(key and "ваш_api_ключ" not in key)

    def get_google_credentials(self) -> Credentials:
        """Возвращает готовый объект авторизации Google."""
        json_data = json.loads(
            base64.b64decode(self.google_credentials_base64.get_secret_value())
        )
        return Credentials.from_service_account_info(
            json_data,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

    def get_service_email(self) -> str:
        """Получить email сервисного аккаунта для логов."""
        try:
            creds = json.loads(
                base64.b64decode(
                    self.google_credentials_base64.get_secret_value()
                )
            )
            return creds.get("client_email", "unknown")
        except:
            return "error"


@lru_cache
def get_settings() -> AppConfig:
    """
    Создает конфигурацию один раз и кэширует её (Singleton).
    """
    try:
        config = AppConfig()

        if config.debug:
            print(f"✅ Config loaded from .env")
            print(f"   Spreadsheet: ...{config.spreadsheet_id[-5:]}")
            print(f"   Service Email: {config.get_service_email()}")

        return config
    except Exception as e:
        print(f"❌ Ошибка загрузки .env конфигурации: {e}")
        # Перевыбрасываем ошибку, чтобы приложение остановилось
        raise


try:
    config = get_settings()
except Exception as e:
    print(f"🔥🔧 Config error. {e}")
