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