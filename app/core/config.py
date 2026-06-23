"""
Configuração centralizada da aplicação.

Lê as variáveis de ambiente do arquivo .env (na raiz do projeto) e
expõe um objeto `settings` tipado e validado.

Princípio: 12-Factor App (factor III - Config).
Toda configuração que muda entre ambientes vem de variável de ambiente,
nunca hardcoded no código.

Princípio: Fail Fast.
Se falta variável obrigatória, a aplicação NÃO sobe.

Uso:
    from app.core.config import settings
    print(settings.database_url_prod)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas do .env.
    """

    database_url_prod: str
    database_url_test: str
    gateway_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()