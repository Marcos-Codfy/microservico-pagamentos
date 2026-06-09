# 💳 Microserviço de Pagamentos

API REST que simula o processamento de pagamentos com diferentes métodos
(cartão de crédito, PIX, boleto), construída com **FastAPI** e seguindo
princípios de **Clean Architecture**.

## 🎯 Objetivo

Projeto acadêmico da disciplina de **Teste e Qualidade de Software**,
desenvolvido para explorar:

- Arquitetura limpa (separação em camadas).
- Validação de dados com Pydantic.
- Testes unitários com pytest aplicando BVA, Equivalence Partitioning
  e Decision Table.

## 🛠️ Tecnologias

| Ferramenta | Versão |
|---|---|
| Python | 3.12 |
| FastAPI | 0.115 |
| Pydantic | 2.9 |
| pytest | 8.3 |
| httpx | 0.27 |

## 📂 Estrutura do Projeto

```
microservico-pagamentos/
├── app/
│   ├── api/                # Camada externa: rotas HTTP
│   │   └── routes_pagamento.py
│   ├── core/               # Núcleo: regras de negócio puras
│   │   ├── calculadora.py
│   │   └── exceptions.py
│   ├── schemas/            # Contratos de dados (DTOs)
│   │   └── pagamento.py
│   └── main.py             # Ponto de entrada da aplicação
├── tests/                  # Testes unitários
│   └── test_calculadora.py
├── requirements.txt        # Dependências pinadas
├── .gitignore
└── README.md
```

## 🚀 Como rodar localmente

### 1. Pré-requisitos

- Python 3.12 instalado
- Git instalado

### 2. Clonar e preparar o ambiente

```bash
# Clonar o repositório
git clone https://github.com/SEU-USUARIO/microservico-pagamentos.git
cd microservico-pagamentos

# Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 3. Subir a API

```bash
uvicorn app.main:app --reload
```

Acesse:

- **API:** http://localhost:8000
- **Documentação Swagger:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🧪 Como rodar os testes

```bash
pytest -v
```

Saída esperada:

```
tests/test_calculadora.py::test_cartao_a_vista_nao_aplica_juros PASSED
tests/test_calculadora.py::test_cartao_12x_aplica_juros_no_limite_maximo PASSED
tests/test_calculadora.py::test_pix_parcelado_lanca_pagamento_invalido_error PASSED
tests/test_calculadora.py::test_cartao_3x_nao_aplica_juros PASSED
tests/test_calculadora.py::test_cartao_4x_aplica_juros PASSED
tests/test_calculadora.py::test_pix_a_vista_processa_normalmente PASSED
tests/test_calculadora.py::test_boleto_a_vista_processa_normalmente PASSED
tests/test_calculadora.py::test_boleto_parcelado_lanca_pagamento_invalido_error PASSED
tests/test_calculadora.py::test_cartao_com_valor_decimal_calcula_corretamente PASSED
tests/test_calculadora.py::test_arredondamento_aplica_round_half_up PASSED

============================== 10 passed ==============================
```

### Estratégia de cobertura

Os testes aplicam três técnicas formais de teste caixa-preta:

- **Boundary Value Analysis (BVA):** testa os limites onde a regra
  muda de comportamento (1x, 3x, 4x, 12x).
- **Equivalence Partitioning:** cobre uma representante de cada
  família de método (cartão, PIX, boleto).
- **Decision Table:** combina método × faixa de parcelas garantindo
  que nenhum cenário escape (válido ou inválido).

## 📐 Endpoints

| Método | Rota          | Descrição                       | Status de sucesso |
|--------|---------------|---------------------------------|-------------------|
| GET    | `/health`     | Verifica se a aplicação está no ar | 200 OK            |
| POST   | `/pagamentos/`| Cria um novo pagamento          | 201 Created       |

### Exemplo: cartão em 3x (dentro da faixa sem juros)

**Request:**

```json
POST /pagamentos/
{
  "valor_total": 1000.00,
  "parcelas": 3,
  "metodo": "cartao_credito",
  "descricao": "Cartão 3x sem juros"
}
```

**Response (201 Created):**

```json
{
  "id": "a37740a8-b71c-447b-bc77-4516418093e0",
  "valor_total": "1000.00",
  "valor_parcela": "333.33",
  "parcelas": 3,
  "juros_aplicado": "0.00",
  "valor_final": "1000.00",
  "metodo": "cartao_credito",
  "status": "aprovado",
  "criado_em": "2026-06-09T17:30:00.123456Z"
}
```

### Exemplo: cartão em 4x (primeira faixa com juros)

**Request:**

```json
POST /pagamentos/
{
  "valor_total": 1000.00,
  "parcelas": 4,
  "metodo": "cartao_credito",
  "descricao": "Cartão 4x com juros"
}
```

**Response (201 Created):**

```json
{
  "id": "b8c9d10e-f1g2-3h4i-5j6k-7l8m9n0o1p2q",
  "valor_total": "1000.00",
  "valor_parcela": "270.00",
  "parcelas": 4,
  "juros_aplicado": "80.00",
  "valor_final": "1080.00",
  "metodo": "cartao_credito",
  "status": "aprovado",
  "criado_em": "2026-06-09T17:30:00.123456Z"
}
```

### Exemplo: regra de negócio violada (PIX parcelado)

**Request:**

```json
POST /pagamentos/
{
  "valor_total": 500.00,
  "parcelas": 3,
  "metodo": "pix",
  "descricao": "PIX inválido"
}
```

**Response (422 Unprocessable Entity):**

```json
{
  "detail": "O método pix não permite parcelamento. Use parcelas=1 ou escolha cartao_credito."
}
```

## 📚 Regras de Negócio

- **Cartão de crédito 1x, 2x e 3x:** sem juros.
- **Cartão de crédito 4x a 12x:** juros simples de 2% ao mês
  (`juros = valor × 0,02 × parcelas`).
- **PIX e Boleto:** somente à vista (1 parcela). Tentar parcelar
  retorna HTTP 422 com mensagem da regra violada.
- **Arredondamento monetário:** `ROUND_HALF_UP` em duas casas decimais
  (padrão contábil brasileiro).
- **Validações automáticas (Pydantic):**
  - `valor_total > 0`
  - `1 ≤ parcelas ≤ 12`
  - `descricao` entre 3 e 200 caracteres


## 🐳 Como subir o ambiente (Docker)

O projeto usa 3 containers orquestrados via `docker-compose`:

| Container | Porta (host) | Função |
|---|---|---|
| `postgres_prod` | 5432 | Banco de dados de produção (persistente) |
| `postgres_test` | 5433 | Banco de testes (em RAM, auto-limpa) |
| `fake_gateway` | 8001 | Simula gateway de pagamento externo |

### Pré-requisitos
- Docker Desktop instalado e rodando
- Arquivo `.env` criado a partir do `.env.example`

### Subir todos os containers
```bash
docker compose up -d --build
```

### Verificar status
```bash
docker compose ps
```

### Acessar o fake-gateway
- Swagger: http://localhost:8001/docs
- Health: http://localhost:8001/health

### Derrubar tudo
```bash
docker compose down
```

## 👤 Autor

**Marcos Vinicius Muniz Arruda**  
Projeto da disciplina de Teste e Qualidade de Software.