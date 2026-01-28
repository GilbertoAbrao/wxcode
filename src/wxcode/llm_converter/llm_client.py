"""LLMClient - DEPRECATED: Use create_provider('anthropic') instead.

Este módulo mantém compatibilidade com código existente que usa LLMClient.
Para novo código, use:

    from wxcode.llm_converter.providers import create_provider
    provider = create_provider('anthropic', model='claude-sonnet-4-20250514')
"""

import warnings

from .providers import AnthropicProvider

# Re-export SYSTEM_PROMPT para compatibilidade
from .providers.prompts import SYSTEM_PROMPT


class LLMClient(AnthropicProvider):
    """DEPRECATED: Use AnthropicProvider ou create_provider('anthropic') ao invés.

    Esta classe é mantida apenas para compatibilidade com código existente.
    Emite DeprecationWarning quando instanciada.

    Para novo código, use:
        from wxcode.llm_converter.providers import create_provider
        provider = create_provider('anthropic')
    """

    def __init__(self, *args, **kwargs):
        """Inicializa LLMClient (deprecated).

        Args:
            *args: Passados para AnthropicProvider
            **kwargs: Passados para AnthropicProvider
        """
        warnings.warn(
            "LLMClient is deprecated. Use create_provider('anthropic') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["LLMClient", "SYSTEM_PROMPT"]
