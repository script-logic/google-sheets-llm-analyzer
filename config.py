import base64
import json
from functools import lru_cache

from google.oauth2.service_account import Credentials
from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSheetsConfig(BaseModel):
    """Конфигурация Google Sheets."""

    spreadsheet_id: str = Field(
        ...,
        validation_alias="SPREADSHEET_ID",  # Связывает переменную из .env
        description="ID Google Таблицы",
        min_length=10,
    )

    sheet_name: str = Field(
        "Заявки из Telegram Bot",
        validation_alias="SHEET_NAME",
        description="Имя листа в таблице",
    )

    category_column: int = Field(
        3,
        validation_alias="CATEGORY_COLUMN",
        ge=1,
        le=26,
    )

    @field_validator("spreadsheet_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if "ваш_id" in v:
            raise ValueError("Не настроен SPREADSHEET_ID в .env файле")
        return v.strip()


class LLMConfig(BaseModel):
    """Конфигурация OpenRouter/OpenAI."""

    api_key: SecretStr = Field(
        SecretStr(""),  # Пустой секрет по умолчанию
        validation_alias="OPENROUTER_API_KEY",
    )

    base_url: str = Field(
        "https://openrouter.ai/api/v1", validation_alias="OPENROUTER_BASE_URL"
    )

    model: str = Field(
        "openai/gpt-3.5-turbo", validation_alias="OPENROUTER_MODEL"
    )

    @property
    def is_enabled(self) -> bool:
        """Проверка, задан ли корректный ключ."""
        token = self.api_key.get_secret_value()
        return bool(token and "ваш_api_ключ" not in token)


class GoogleCredentials(BaseModel):
    """Данные сервисного аккаунта."""

    # SecretStr скрывает содержимое при печати объекта (****)
    credentials_base64: SecretStr = Field(
        ..., validation_alias="GOOGLE_CREDENTIALS_BASE64", min_length=50
    )

    @field_validator("credentials_base64")
    @classmethod
    def validate_base64_content(cls, v: SecretStr) -> SecretStr:
        val = v.get_secret_value()
        if "ваш_base64" in val:
            raise ValueError("GOOGLE_CREDENTIALS_BASE64 не настроен")

        try:
            decoded = base64.b64decode(val, validate=True).decode("utf-8")
            data = json.loads(decoded)

            if data.get("type") != "service_account":
                raise ValueError("JSON не является service_account")
            if "private_key" not in data:
                raise ValueError("В JSON отсутствует private_key")

        except Exception as e:
            raise ValueError(f"Ошибка декодирования Credentials: {e}")

        return v

    def get_creds_object(self) -> Credentials:
        """Возвращает готовый объект авторизации Google."""
        json_data = json.loads(
            base64.b64decode(self.credentials_base64.get_secret_value())
        )
        return Credentials.from_service_account_info(
            json_data,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

    @property
    def service_email(self) -> str:
        """Извлекает email без полной десериализации (для логов)."""
        try:
            # Парсим "на лету", так как это свойство вызывается редко
            data = json.loads(
                base64.b64decode(self.credentials_base64.get_secret_value())
            )
            return data.get("client_email", "unknown")
        except Exception:
            return "invalid_token"


class AppConfig(BaseSettings):
    """Корневая конфигурация."""

    # Вложенные модели
    google_sheets: GoogleSheetsConfig = Field(default_factory=dict)  # type: ignore
    google_credentials: GoogleCredentials = Field(default_factory=dict)  # type: ignore
    llm: LLMConfig = Field(default_factory=dict)  # type: ignore

    debug: bool = Field(False, validation_alias="DEBUG")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> AppConfig:
    """
    Singleton для загрузки настроек.
    Загружает один раз при первом вызове.
    """
    try:
        config = AppConfig()

        # Небольшой лог при старте (можно убрать в продакшене)
        if config.debug:
            print(
                "🔧 Config loaded. SheetID:"
                f" ...{config.google_sheets.spreadsheet_id[-5:]}"
            )
            print(f"🤖 LLM Enabled: {config.llm.is_enabled}")
            print(f"📧 Service Acc: {config.google_credentials.service_email}")

        return config
    except Exception as e:
        print(f"🔥 Critical Error loading .env: {e}")
        raise


try:
    config = get_settings()
except Exception as e:
    print(f"🔥🔧 Config error. {e}")
