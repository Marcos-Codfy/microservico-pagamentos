# 💳 Microserviço de Pagamentos

> Microserviço acadêmico de processamento de pagamentos em Python/FastAPI, construído com **Clean Architecture**, **testes em múltiplas camadas** e **CI/CD profissional** como projeto da disciplina de Teste e Qualidade de Software (UniCatólica do Tocantins).

[![CI](https://github.com/Marcos-Codfy/microservico-pagamentos/actions/workflows/ci.yml/badge.svg)](https://github.com/Marcos-Codfy/microservico-pagamentos/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-22%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)
![Mutation Score](https://img.shields.io/badge/mutation%20score-96%25-brightgreen)

---

## 📌 Sobre o projeto

Este microserviço implementa o **processamento de pagamentos** (cartão de crédito, PIX e boleto) com cálculo de juros, validação de regras de negócio, persistência em PostgreSQL e integração com um gateway externo (simulado).

O projeto serve a dois propósitos:

1. **Acadêmico**: entregar uma aplicação real para a disciplina de Teste e Qualidade de Software, evidenciando aplicação prática de conceitos como BVA, Decision Tables, Pirâmide de Testes, Mutation Testing, CI/CD e Clean Architecture.
2. **Portfólio profissional**: demonstrar habilidades de engenharia de software além de "código que funciona" — engenharia de qualidade aplicada do primeiro ao último commit.

---

## 🏗️ Arquitetura

O projeto segue **Clean Architecture** (Robert C. Martin), com camadas isoladas por responsabilidade:

```
┌────────────────────────────────────────────────────┐
│  API Layer (FastAPI routes)                        │
│  app/api/routes_pagamento.py                       │
│  → Recebe HTTP, valida payload, delega ao core     │
├────────────────────────────────────────────────────┤
│  Core / Domínio (lógica pura, sem framework)       │
│  app/core/calculadora.py                           │
│  app/core/exceptions.py                            │
│  → Regras de negócio, cálculo de juros             │
├────────────────────────────────────────────────────┤
│  Schemas (Pydantic — validação e contratos)        │
│  app/schemas/pagamento.py                          │
├────────────────────────────────────────────────────┤
│  Persistência (SQLAlchemy 2.0)                     │
│  app/db/database.py, app/db/models.py              │
│  → Conecta no Postgres, persiste agregados         │
├────────────────────────────────────────────────────┤
│  Gateway externo (cliente HTTP)                    │
│  app/gateway/cliente.py                            │
│  → Comunica com fake_gateway (simulação)           │
└────────────────────────────────────────────────────┘
```

**Princípios aplicados:**

- **SRP** (Single Responsibility Principle): cada módulo tem uma única razão pra mudar.
- **DIP** (Dependency Inversion): a camada de domínio não conhece HTTP nem banco.
- **Fail Fast**: regras violadas lançam exceções de domínio (`PagamentoInvalidoError`), capturadas pela camada de rota e traduzidas em HTTP apropriado.
- **Anti-Corruption Layer**: a camada de rota traduz exceções de domínio em HTTP, isolando o core da web.

---

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | **Python 3.12** |
| Framework web | **FastAPI** |
| ORM | **SQLAlchemy 2.0** |
| Banco de dados | **PostgreSQL 16** |
| Containerização | **Docker + Docker Compose** |
| Testes unitários/integração | **pytest** + **pytest-cov** |
| Testes E2E | **TestClient** + **uvicorn** em background |
| Mutation testing | **mutmut 2.5** |
| CI/CD | **GitHub Actions** |
| Validação de schemas | **Pydantic v2** |

---

## 🚀 Como rodar localmente

### Pré-requisitos

- **Python 3.12** instalado
- **Docker Desktop** instalado e rodando
- **Git** instalado

### 1. Clonar o repositório

```bash
git clone https://github.com/Marcos-Codfy/microservico-pagamentos.git
cd microservico-pagamentos
```

### 2. Criar e ativar o ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Subir os serviços de infraestrutura

```bash
docker compose up -d
```

Isso sobe **3 containers**:

| Container | Porta | Função |
|---|---|---|
| `postgres_prod` | `5432` | Banco de produção/desenvolvimento |
| `postgres_test` | `5433` | Banco de testes (com `tmpfs` pra velocidade) |
| `fake_gateway` | `8001` | Gateway de pagamento simulado |

Confere que estão saudáveis:

```bash
docker compose ps
```

Os 3 devem aparecer com status `Up (healthy)`.

### 5. Subir a aplicação

```bash
uvicorn app.main:app --reload
```

A API estará disponível em **http://localhost:8000**.

A **documentação interativa (Swagger)** fica em **http://localhost:8000/docs**.

---

## 🧪 Como rodar os testes

### Suite completa (rápido — exclui E2E)

```bash
pytest -m "not e2e" -v
```

### Apenas testes E2E

```bash
pytest -m e2e -v
```

### Todos os testes + relatório de cobertura

```bash
pytest --cov=app --cov-report=term-missing
```

### Mutation testing (calculadora)

```bash
# Limpar cache (recomendado entre execuções)
rm .mutmut-cache       # Linux/Mac
del .mutmut-cache      # Windows

# Rodar (no Windows, antes setar encoding UTF-8)
mutmut run
```

Gerar relatório HTML do mutmut:

```bash
mutmut html
# Abre html/index.html no navegador
```

---

## 🧱 Estratégia de testes (risk-proportional testing)

A estratégia segue o princípio: **rigor de teste proporcional ao risco do componente**.

| Componente | Estratégia | Justificativa |
|---|---|---|
| **Calculadora** (cálculo de juros) | Mutation testing + BVA + Decision Table | Lógica financeira; bugs aqui custam dinheiro real |
| **Gateway externo** | Mocks (`unittest.mock.patch`) | Dependência externa volátil; isolar pra velocidade |
| **Persistência** | Integração real com Postgres em container | Validar SQL/ORM contra banco real, não mock |
| **Fluxo HTTP completo** | 1 teste E2E sem mocks | Validar montagem; rodar muitos E2E é lento e frágil |

### Pirâmide de testes resultante

```
            ┌─────┐
            │  1  │  E2E (fluxo completo sem mocks)
            └─────┘
         ┌──────────┐
         │    9     │  Integração (HTTP + Postgres real + gateway mockado)
         └──────────┘
   ┌────────────────────┐
   │         12         │  Unit (calculadora — Decimal puro)
   └────────────────────┘
```

**Total: 22 testes**. Pirâmide saudável (mais base unit, topo enxuto).

### Cobertura de testes (caixa-preta)

Os testes unitários da calculadora aplicam **3 técnicas combinadas**:

- **Boundary Value Analysis (BVA)**: fronteiras de juros (1x, 3x, 4x, 12x).
- **Equivalence Partitioning**: pelo menos 1 representante de cada família (cartão / PIX / boleto).
- **Decision Table**: combinação método × parcelas; nenhum combo válido ou inválido escapa.

### Defesa contra mutação

A calculadora é submetida ao **mutmut**, que introduz mutações no código e roda a suite pra ver se algum teste pega. Resultado atual:

| Métrica | Valor |
|---|---|
| Mutantes gerados | 25 |
| Mortos (caught by tests) | 24 |
| Sobreviventes | 1 (mutante equivalente conhecido) |
| **Mutation score** | **96%** |

O único sobrevivente é uma mutação em string de construtor `Decimal` (`Decimal("XX0.02XX")`), uma **limitação documentada do mutmut 2.5** no Windows pra strings que lançam exceção no import. Não é um teste faltando — é um mutante equivalente.

> 💡 **Frase pronta:** _Cobertura mede execução; mutação mede DETECÇÃO de bug. São métricas complementares — código pode ter 100% de cobertura e baixa detecção._

---

## 🔁 CI/CD — Pipeline em camadas

O `.github/workflows/ci.yml` implementa **gate em camadas**, otimizando tempo de feedback:

| Evento | O que roda | Por quê |
|---|---|---|
| **Pull Request** | Testes rápidos (`pytest -m "not e2e"`) + cobertura | Feedback em <2min pra dev iterar |
| **Push em `main`** | Tudo acima + testes E2E | Gate completo só após PR aprovado |

### Fluxo de trabalho do projeto

1. Criar branch `feature/<nome-descritivo>` a partir de `main`.
2. Commits atômicos com **Conventional Commits** em português.
3. Push da branch e abrir PR para `main`.
4. CI rápido roda automaticamente; corrigir se falhar.
5. Merge no GitHub (preferindo **merge commit** pra preservar histórico).
6. CI completo (incluindo E2E) roda em `main` após merge.

---

## 📁 Estrutura do projeto

```
microservico-pagamentos/
├── app/
│   ├── api/
│   │   └── routes_pagamento.py       # Endpoints HTTP
│   ├── core/
│   │   ├── calculadora.py            # Lógica de negócio pura
│   │   └── exceptions.py             # Exceções de domínio
│   ├── db/
│   │   ├── database.py               # Configuração SQLAlchemy
│   │   └── models.py                 # Modelos ORM
│   ├── gateway/
│   │   └── cliente.py                # Cliente HTTP do gateway
│   ├── schemas/
│   │   └── pagamento.py              # Schemas Pydantic
│   └── main.py                       # Bootstrap FastAPI
├── tests/
│   ├── test_calculadora.py           # Unit (12 testes)
│   ├── test_routes_pagamento.py      # Integração (9 testes)
│   ├── test_e2e.py                   # E2E (1 teste)
│   └── conftest.py                   # Fixtures compartilhadas
├── fake_gateway/
│   └── main.py                       # Gateway simulado
├── .github/
│   └── workflows/
│       └── ci.yml                    # Pipeline GitHub Actions
├── docker-compose.yml                # Infra local
├── pyproject.toml                    # Config pytest + mutmut
├── requirements.txt                  # Dependências
└── README.md                         # Este arquivo
```

---

## 📚 Endpoints disponíveis

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/pagamentos` | Cria um novo pagamento (cálculo + persistência + autorização) |
| `GET` | `/pagamentos/{pagamento_id}` | Busca um pagamento pelo ID |
| `GET` | `/health` | Health check da aplicação |

### Exemplo de requisição

```bash
curl -X POST "http://localhost:8000/pagamentos" \
  -H "Content-Type: application/json" \
  -d '{
    "valor_total": "1000.00",
    "parcelas": 4,
    "metodo": "cartao_credito",
    "descricao": "Notebook"
  }'
```

### Exemplo de resposta

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "valor_total": "1000.00",
  "valor_parcela": "270.00",
  "parcelas": 4,
  "juros_aplicado": "80.00",
  "valor_final": "1080.00",
  "metodo": "cartao_credito",
  "status": "APROVADO",
  "criado_em": "2026-06-22T14:30:00Z"
}
```

---

## 📐 Regras de negócio

| Método | Parcelas permitidas | Juros |
|---|---|---|
| Cartão de crédito | 1 a 12 | Sem juros até 3x; juros simples de **2% × parcelas** a partir de 4x |
| PIX | Apenas 1 | Nunca |
| Boleto | Apenas 1 | Nunca |

**Arredondamento:** todos os cálculos usam `Decimal` com `ROUND_HALF_UP` (padrão contábil brasileiro). **`float` nunca é usado para valores monetários.**

---

## 🗺️ Roadmap do projeto

| Aula | Conteúdo | Status |
|---|---|---|
| Aula 1 | Setup do projeto, FastAPI, Clean Architecture | ✅ Concluída |
| Aula 2 | Testes unitários (BVA, EP, AAA) + Docker + Testes de integração | ✅ Concluída |
| Aula 3 | Testes E2E + Mutation Testing + CI em camadas | ✅ Concluída |
| Aula 4 | Observabilidade (logs estruturados, healthcheck, métricas Prometheus) + 5 Quality Gates | 🚧 Em andamento |
| Finalização | README + Relatório de Bugs Evitados + Apresentação | 🚧 Em andamento |

---

## 🎓 Sobre o autor

**Marcos** ([@Marcos-Codfy](https://github.com/Marcos-Codfy))
Estudante de Engenharia de Software — UniCatólica do Tocantins
Projeto para a disciplina de **Teste e Qualidade de Software**

---

## 📝 Licença

Este projeto é acadêmico e está disponível para fins educacionais.