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

    Trabalhamos com 2 bancos Postgres (prod e test) e 1 serviço externo
    (fake-gateway). Por isso usamos connection strings completas em vez
    de campos soltos: cada URL já carrega user, password, host, port e
    nome do banco, evitando duplicação.
    """

    # URLs de conexão dos dois Postgres (prod na 5432, test na 5433).
    # Formato esperado: postgresql+psycopg2://user:pass@host:port/db
    database_url_prod: str
    database_url_test: str

    # URL do serviço externo (fake_gateway containerizado, porta 8001).
    # Usado pelo httpx na Sessão 3.
    gateway_url: str

    # Configuração do pydantic-settings:
    # - env_file: caminho do arquivo .env a ser lido
    # - case_sensitive=False: POSTGRES_USER e postgres_user são equivalentes
    # - extra="ignore": variáveis no .env que NÃO declaramos aqui
    #   (ex.: POSTGRES_USER, POSTGRES_PASSWORD usadas pelo docker-compose)
    #   são silenciosamente ignoradas em vez de quebrar a validação.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Instância única (singleton) usada por toda a aplicação.
# Quem precisar de config faz: from app.core.config import settings
settings = Settings()