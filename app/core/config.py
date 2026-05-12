"""
Configurações da aplicação via variáveis de ambiente.
Utiliza pydantic-settings para validação automática e tipagem forte.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações centralizadas da aplicação."""

    # Banco de dados
    database_url: str = "sqlite:///./focus_log.db"

    # Segurança — API Key (vazio = modo dev sem autenticação)
    api_key: str = ""

    # CORS — origens permitidas, separadas por vírgula
    allowed_origins: str = "http://localhost:3000"

    # Modo de depuração (nunca True em produção)
    debug: bool = True

    # Rate limiting (formato: "N/minute" ou "N/second")
    rate_limit: str = "60/minute"

    # Versão da aplicação
    app_version: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Converte a string de origens em lista."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def auth_enabled(self) -> bool:
        """Retorna True se a autenticação por API Key está habilitada."""
        return bool(self.api_key and self.api_key.strip())


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna a instância de configurações cacheada.
    O cache garante que as variáveis de ambiente sejam lidas apenas uma vez.
    """
    return Settings()
