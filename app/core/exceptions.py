"""
Exceções customizadas do domínio de pagamento.

Por que exceções customizadas?
------------------------------
- Semântica clara: `PagamentoInvalidoError` é mais expressivo que `ValueError`.
- Captura específica: a camada de rota consegue tratar apenas exceções do
  nosso domínio, sem capturar erros genéricos do Python ou do framework.
- Manutenção centralizada: mensagens e comportamentos ficam em um único lugar.

Padrão de idioma deste projeto:
- Domínio de negócio em português (Pagamento, Invalido, Metodo).
- Termos técnicos universais em inglês (Error, Exception, Request, Response).

Todas as exceções herdam de `PagamentoError`, que é a classe-base do domínio.
Isso permite capturar "qualquer erro de pagamento" com um único `except`.
"""


class PagamentoError(Exception):
    """
    Exceção base de todos os erros do domínio de pagamento.

    Não deve ser lançada diretamente — serve de pai para exceções
    mais específicas. Permite capturar todos os erros do domínio
    com `except PagamentoError:` na camada de cima.
    """
    pass


class PagamentoInvalidoError(PagamentoError):
    """
    Lançada quando uma regra de negócio é violada antes do processamento.

    Exemplos de uso:
    - PIX ou Boleto com mais de 1 parcela
    - Combinação inválida de método e parcelas

    Esta exceção representa um erro de **validação de negócio**,
    diferente de um pagamento que foi tentado e recusado.
    """
    pass


class GatewayError(PagamentoError):
    """
    Base para erros de comunicação ou recusa do gateway externo

    Permite a camada de rota capturar qualquer erro de gateway
    com um unico 'except Gateway'
    """
    pass

class GatewayIndisponivelError(GatewayError):
    """
    Lançada quando o gateway externo está fora do ar, deu timeout
    ou respondeu com 5xx

    Traduz-se em HTTP 503 (Service Unavailable) na camada de rota -
    sinaliza "não é culpa nossa, é da dependencia"
    """
    pass


class GatewayRecusouPagamentoError(GatewayError):
    """
    Lançada quando o gateay respondeu mas se recusou a autorizar o
    pagamento (cartão sem saldo, fraude detectada, etc.).

    Traduz-se HTTP 402 (Payment Required) na camada de rota.
    """

    pass