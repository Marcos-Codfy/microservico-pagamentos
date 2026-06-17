# 💳 Microserviço de Pagamentos

[![CI - Microserviço de Pagamentos](https://github.com/Marcos-Codfy/microservico-pagamentos/actions/workflows/ci.yml/badge.svg)](https://github.com/Marcos-Codfy/microservico-pagamentos/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Postgres](https://img.shields.io/badge/PostgreSQL-16-336791)
![Tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

API REST que processa pagamentos com diferentes métodos (cartão, PIX, boleto),
construída com **FastAPI**, **PostgreSQL** e **Docker**, seguindo princípios de
**Clean Architecture** e cobertura completa de testes automatizados.

---

## 🎯 Objetivo

Projeto acadêmico da disciplina de **Teste e Qualidade de Software** (UniCatólica do Tocantins),
desenvolvido para demonstrar uma abordagem profissional de qualidade de software:

- **Arquitetura Limpa** com separação clara de camadas.
- **Testes unitários** com BVA, Equivalence Partitioning e Decision Tables.
- **Testes de integração** com TestClient, mocks e banco real (não SQLite).
- **Integração com serviço externo** via httpx, com tradução de erros HTTP.
- **CI/CD** com GitHub Actions e Quality Gate de cobertura.

---

## 🛠️ Stack

| Categoria | Ferramenta |
|---|---|
| Linguagem | Python 3.12 |
| Framework | FastAPI 0.115 |
| Validação | Pydantic 2.9 |
| ORM | SQLAlchemy 2.0 |
| Banco | PostgreSQL 16 |
| Cliente HTTP | httpx 0.27 |
| Testes | pytest 8.3 + pytest-cov 5.0 |
| Container | Docker + docker-compose |
| CI/CD | GitHub Actions |

---

## 🏛️ Arquitetura

```
HTTP Request
     │
     ▼
┌──────────────────────────────────────────┐
│  app/api/        (camada de entrada)     │  ← traduz HTTP ↔ domínio
├──────────────────────────────────────────┤
│  app/core/       (regras de negócio)     │  ← código puro, sem I/O
├──────────────────────────────────────────┤
│  app/gateway/    (camada de borda)       │  ← chamada HTTP externa
├──────────────────────────────────────────┤
│  app/db/         (persistência)          │  ← SQLAlchemy + Postgres
└──────────────────────────────────────────┘
     │
     ▼
PostgreSQL  +  Fake Payment Gateway
```

**Princípios aplicados:**

- **Separation of Concerns** — cada camada tem responsabilidade única.
- **Anti-Corruption Layer (DDD)** — todo HTTP externo isolado em `app/gateway/`.
- **DTO Pattern** — schemas Pydantic separados de modelos ORM.
- **Repository Pattern** — `app/db/repositorio.py` abstrai acesso ao banco.
- **Dependency Injection** — `Depends(get_db)` permite override em testes.

---

## 📂 Estrutura do Projeto

```
microservico-pagamentos/
├── .github/
│   └── workflows/
│       └── ci.yml                       # Pipeline CI/CD
├── app/
│   ├── api/
│   │   └── routes_pagamento.py          # Rotas HTTP (POST, GET)
│   ├── core/
│   │   ├── calculadora.py               # Regra de negócio pura
│   │   ├── config.py                    # pydantic-settings
│   │   └── exceptions.py                # Exceções do domínio
│   ├── db/
│   │   ├── database.py                  # Engine, sessão, get_db
│   │   ├── models.py                    # Modelos ORM
│   │   └── repositorio.py               # Operações de persistência
│   ├── gateway/
│   │   └── cliente.py                   # Cliente httpx com timeout
│   ├── schemas/
│   │   └── pagamento.py                 # DTOs Pydantic
│   └── main.py                          # Bootstrap FastAPI
├── fake_gateway/                        # Serviço externo simulado
│   └── main.py
├── tests/
│   ├── conftest.py                      # Fixtures compartilhadas
│   ├── test_calculadora.py              # 10 testes unitários
│   └── test_pagamentos.py               # 9 testes de integração
├── docker-compose.yml                   # Postgres + fake_gateway
├── requirements.txt
└── README.md
```

---

## 🚀 Como subir o ambiente

### Pré-requisitos

- Python 3.12
- Docker e docker-compose
- Git

### 1. Clonar e preparar

```bash
git clone https://github.com/Marcos-Codfy/microservico-pagamentos.git
cd microservico-pagamentos

# Ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Dependências
pip install -r requirements.txt
```

### 2. Subir os containers (Postgres prod + Postgres test + fake_gateway)

```bash
docker compose up -d
```

Você terá 3 containers rodando:

| Container | Porta | Função |
|---|---|---|
| `pagamentos_postgres_prod` | 5432 | Banco da aplicação |
| `pagamentos_postgres_test` | 5433 | Banco efêmero para testes (tmpfs) |
| `pagamentos_fake_gateway` | 8001 | Gateway de pagamento simulado |

### 3. Configurar variáveis de ambiente

Crie um `.env` na raiz baseado no `.env.example`:

```env
DATABASE_URL_PROD=postgresql+psycopg2://pagamentos:pagamentos@localhost:5432/pagamentos
DATABASE_URL_TEST=postgresql+psycopg2://pagamentos:pagamentos@localhost:5433/pagamentos_test
GATEWAY_URL=http://localhost:8001
```

### 4. Subir a API

```bash
uvicorn app.main:app --reload
```

Acesse:

- 📘 **Swagger:** http://localhost:8000/docs
- 🩺 **Health Check:** http://localhost:8000/health

---

## 🧪 Como rodar os testes

### Todos os testes (unitários + integração)

```bash
pytest -v
```

**Esperado:** 19 testes verdes.

### Com cobertura

```bash
pytest --cov=app --cov-report=term-missing -v
```

**Cobertura atual:** 94%.

---

## 📊 Endpoints

| Método | Rota | Status codes possíveis | Descrição |
|---|---|---|---|
| `GET` | `/health` | 200 | Health check |
| `POST` | `/pagamentos/` | 201, 402, 422, 503 | Cria pagamento |
| `GET` | `/pagamentos/{id}` | 200, 404, 422 | Busca pagamento por ID |

### Exemplo — POST `/pagamentos/`

**Request:**

```json
{
  "valor_total": 1500.00,
  "parcelas": 6,
  "metodo": "cartao_credito",
  "descricao": "Notebook Dell"
}
```

**Response 201:**

```json
{
  "id": "3f2a7b8c-...",
  "valor_total": "1500.00",
  "valor_parcela": "260.00",
  "parcelas": 6,
  "juros_aplicado": "60.00",
  "valor_final": "1560.00",
  "metodo": "cartao_credito",
  "status": "aprovado",
  "criado_em": "2026-06-16T18:30:00Z"
}
```

### Significado dos status codes

| Código | Quando |
|---|---|
| `201` | Pagamento autorizado e persistido |
| `402` | Gateway recusou o pagamento |
| `422` | Regra de negócio violada (ex.: PIX parcelado) ou payload inválido |
| `503` | Gateway externo indisponível ou timeout |

---

## 🧪 Estratégia de testes

### Pirâmide de testes

```
        /\
       /E2E\         (futuro)
      /─────\
     / inte- \       9 testes — TestClient + Postgres real + mock
    /  gração \
   /───────────\
  /  unitários  \    10 testes — calculadora pura, função sem I/O
 /───────────────\
```

### Técnicas aplicadas

| Técnica | Onde |
|---|---|
| **Boundary Value Analysis (BVA)** | `test_cartao_12x_aplica_juros_no_limite_maximo` |
| **Equivalence Partitioning** | `test_pix_parcelado_lanca_pagamento_invalido_error` |
| **Decision Table** | Combinações de método × parcelas na calculadora |
| **AAA Pattern** | Todos os testes (Arrange, Act, Assert) |
| **Test Double (mock)** | Falhas do gateway via `unittest.mock.patch` |
| **Fixtures encadeadas** | `engine_teste` → `db_session` → `client` |

### Por que Postgres real nos testes (e não SQLite)

SQLite tem diferenças sutis de tipos, transações e constraints em relação ao Postgres.
Teste passando em SQLite e quebrando em produção é o **anti-padrão clássico**.
Por isso, usamos um Postgres dedicado (`tmpfs`) na porta 5433 — mesma engine que
produção, rápido o suficiente pra rodar 19 testes em 1 segundo.

---

## 🔄 CI/CD

A cada push em `main` ou branch `feature/**`, o GitHub Actions:

1. Sobe um Ubuntu fresh.
2. Instala Python 3.12 com cache de dependências.
3. Sobe um Postgres como service nativo do Actions.
4. Sobe o `fake_gateway` em background.
5. Roda `pytest --cov=app --cov-fail-under=70`.
6. Falha se a cobertura cair abaixo de **70%**.

**Quality Gate atual:** 70% mínimo, 94% praticado.

---

## 🤔 Decisões de design (trade-offs)

| Decisão | Alternativa descartada | Por quê |
|---|---|---|
| Postgres real nos testes | SQLite em memória | Fidelidade com prod |
| `uvicorn` background no CI | `docker compose up` no CI | Mais rápido, menos pontos de falha |
| `from_attributes=True` no Pydantic | Conversão manual de ORM | Padrão da indústria FastAPI |
| Conventional Commits em português | Inglês ou estilo livre | Consistência do projeto acadêmico |
| Exceções de domínio em português | Em inglês | Espelha vocabulário do negócio |
| `httpx` no cliente HTTP | `requests` | Permite migração futura pra async |

---

## 👤 Autor

**Marcos Cardoso** ([@Marcos-Codfy](https://github.com/Marcos-Codfy))
Engenharia de Software — UniCatólica do Tocantins
Disciplina: Teste e Qualidade de Software (2026)

---

## 📜 Licença

Projeto acadêmico — uso livre para fins educacionais.