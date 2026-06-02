# 💳 Microserviço de Pagamentos

API REST que simula o processamento de pagamentos com diferentes métodos
(cartão de crédito, PIX, boleto), construída com **FastAPI** e seguindo
princípios de **Clean Architecture**.

## 🎯 Objetivo

Projeto acadêmico da disciplina de **Teste e Qualidade de Software**,
desenvolvido para explorar:

- Arquitetura limpa (separação em camadas).
- Validação de dados com Pydantic.
- Testes unitários com pytest.

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

============================== 3 passed ==============================
```

## 📐 Endpoints

| Método | Rota          | Descrição                       | Status de sucesso |
|--------|---------------|---------------------------------|-------------------|
| GET    | `/health`     | Verifica se a aplicação está no ar | 200 OK            |
| POST   | `/pagamentos/`| Cria um novo pagamento          | 201 Created       |

### Exemplo: criar pagamento (cartão parcelado)

**Request:**

```json
POST /pagamentos/
{
  "valor_total": 1000.00,
  "parcelas": 3,
  "metodo": "cartao_credito",
  "descricao": "Compra teste"
}
```

**Response (201 Created):**

```json
{
  "id": "a37740a8-b71c-447b-bc77-4516418093e0",
  "valor_total": "1000.00",
  "valor_parcela": "353.33",
  "parcelas": 3,
  "juros_aplicado": "60.00",
  "valor_final": "1060.00",
  "metodo": "cartao_credito",
  "status": "aprovado",
  "criado_em": "2026-06-02T17:30:00.123456Z"
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

- **Cartão de crédito 1x:** sem juros.
- **Cartão de crédito 2x a 12x:** juros simples de 2% ao mês.
- **PIX e Boleto:** somente à vista (1 parcela).
- **Validações automáticas (Pydantic):**
  - `valor_total > 0`
  - `1 ≤ parcelas ≤ 12`
  - `descricao` entre 3 e 200 caracteres

## 👤 Autor

**Marcos Vinicius Muniz Arruda**  
Projeto da disciplina de Teste e Qualidade de Software.