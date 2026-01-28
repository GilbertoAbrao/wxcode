"""
Serviço de rastreamento de consumo de tokens do Claude Code.

Extrai métricas do output stream-json e persiste no MongoDB.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from beanie import PydanticObjectId

from wxcode.models.token_usage import TokenUsageLog


@dataclass
class TokenUsageMetrics:
    """Métricas acumuladas de uma sessão."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    total_cost_usd: float = 0.0
    model: Optional[str] = None


class TokenTracker:
    """
    Extrai e registra métricas de tokens do output do Claude Code.

    Processa linhas do stream-json emitido pelo Claude Code em modo headless
    e acumula métricas de tokens para posterior persistência.

    Exemplo de uso:
        tracker = TokenTracker()
        for line in claude_output:
            data = tracker.process_stream_line(line)
            if data:
                # processar dados parseados
                pass
        await tracker.save_usage(tenant_id, project_id, session_id)
    """

    def __init__(self):
        self._metrics = TokenUsageMetrics()

    @property
    def metrics(self) -> TokenUsageMetrics:
        """Retorna métricas acumuladas da sessão atual."""
        return self._metrics

    @property
    def total_tokens(self) -> int:
        """Total de tokens consumidos (input + output)."""
        return self._metrics.input_tokens + self._metrics.output_tokens

    def process_stream_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Processa uma linha do stream-json e extrai métricas.

        Args:
            line: Linha JSON do output stream-json do Claude Code

        Returns:
            Dados parseados ou None se a linha não for JSON válido
        """
        if not line or not line.strip():
            return None

        try:
            data = json.loads(line.strip())
        except json.JSONDecodeError:
            return None

        # Extrai usage de mensagens type=assistant
        if data.get("type") == "assistant":
            message = data.get("message", {})
            usage = message.get("usage", {})

            if usage:
                self._metrics.input_tokens += usage.get("input_tokens", 0)
                self._metrics.output_tokens += usage.get("output_tokens", 0)
                self._metrics.cache_creation_input_tokens += usage.get(
                    "cache_creation_input_tokens", 0
                )
                self._metrics.cache_read_input_tokens += usage.get(
                    "cache_read_input_tokens", 0
                )

            # Captura modelo utilizado
            if message.get("model") and not self._metrics.model:
                self._metrics.model = message.get("model")

        # Extrai custo total do resultado final
        if "total_cost_usd" in data:
            self._metrics.total_cost_usd = data["total_cost_usd"]

        # Também pode vir no nível raiz (resultado final)
        if "usage" in data and data.get("type") != "assistant":
            usage = data["usage"]
            # Só atualiza se não veio de mensagem assistant (evita duplicação)
            if "result" in data:
                self._metrics.input_tokens = usage.get("input_tokens", self._metrics.input_tokens)
                self._metrics.output_tokens = usage.get("output_tokens", self._metrics.output_tokens)

        return data

    async def save_usage(
        self,
        tenant_id: str,
        project_id: str | PydanticObjectId,
        session_id: str,
        change_id: Optional[str] = None,
    ) -> TokenUsageLog:
        """
        Persiste as métricas acumuladas no MongoDB.

        Args:
            tenant_id: ID do tenant
            project_id: ID do projeto
            session_id: ID da sessão Claude Code
            change_id: ID da change/conversão (opcional)

        Returns:
            TokenUsageLog persistido
        """
        if isinstance(project_id, str):
            project_id = PydanticObjectId(project_id)

        log = TokenUsageLog(
            tenant_id=tenant_id,
            project_id=project_id,
            session_id=session_id,
            change_id=change_id,
            input_tokens=self._metrics.input_tokens,
            output_tokens=self._metrics.output_tokens,
            cache_creation_tokens=self._metrics.cache_creation_input_tokens,
            cache_read_tokens=self._metrics.cache_read_input_tokens,
            total_cost_usd=self._metrics.total_cost_usd,
            model=self._metrics.model,
        )

        await log.insert()

        # Reset para próxima sessão
        self.reset()

        return log

    def reset(self):
        """Reseta contadores para nova sessão."""
        self._metrics = TokenUsageMetrics()

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas acumuladas."""
        return {
            "input_tokens": self._metrics.input_tokens,
            "output_tokens": self._metrics.output_tokens,
            "cache_creation_tokens": self._metrics.cache_creation_input_tokens,
            "cache_read_tokens": self._metrics.cache_read_input_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self._metrics.total_cost_usd,
            "model": self._metrics.model,
        }
