"""
Chat AI Agent para processar comunicação com Claude Code.

Orquestra classificação de mensagens, sanitização de output e validação de input.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from wxcode.services.guardrail import Guardrail
from wxcode.services.message_classifier import MessageClassifier, MessageType
from wxcode.services.output_sanitizer import OutputSanitizer


@dataclass
class ProcessedInput:
    """Resultado do processamento de input do usuário."""

    valid: bool
    error: str = ""
    cleaned: str = ""


@dataclass
class ProcessedMessage:
    """Resultado do processamento de output do Claude Code."""

    type: MessageType
    content: str
    options: Optional[List[Dict[str, str]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChatAgent:
    """
    Agente de chat que processa comunicação entre usuário e Claude Code.

    Responsável por:
    - Validar e sanitizar inputs do usuário (via Guardrail)
    - Classificar mensagens do Claude Code (via MessageClassifier)
    - Sanitizar outputs removendo referências sensíveis (via OutputSanitizer)
    - Extrair opções de perguntas estruturadas
    """

    def __init__(self):
        """Inicializa o agente com seus componentes."""
        self.classifier = MessageClassifier()
        self.sanitizer = OutputSanitizer()

    def process_input(self, message: str) -> ProcessedInput:
        """
        Processa e valida input do usuário.

        Args:
            message: Mensagem enviada pelo usuário

        Returns:
            ProcessedInput com resultado da validação
        """
        # Validar com Guardrail
        is_valid, error = Guardrail.validate_input(message)

        if not is_valid:
            return ProcessedInput(valid=False, error=error)

        # Input válido - retornar limpo
        cleaned = message.strip()
        return ProcessedInput(valid=True, cleaned=cleaned)

    def process_output(self, json_data: Dict[str, Any]) -> ProcessedMessage:
        """
        Processa output JSON do Claude Code.

        Args:
            json_data: Dicionário com dados da resposta do Claude Code

        Returns:
            ProcessedMessage com tipo, conteúdo sanitizado e opções
        """
        if not json_data:
            return ProcessedMessage(
                type=MessageType.INFO,
                content="",
                metadata={},
            )

        # 1. Classificar tipo de mensagem
        msg_type = self.classifier.classify(json_data)

        # 2. Extrair conteúdo
        content = self._extract_content(json_data)

        # 3. Sanitizar conteúdo
        sanitized_content = self.sanitizer.sanitize(content)

        # 4. Extrair opções se for multi-question
        options = None
        if msg_type == MessageType.MULTI_QUESTION:
            options = self.classifier.extract_options(json_data)

        # 5. Extrair metadata segura
        metadata = self._extract_safe_metadata(json_data)

        return ProcessedMessage(
            type=msg_type,
            content=sanitized_content,
            options=options,
            metadata=metadata,
        )

    def _extract_content(self, json_data: Dict[str, Any]) -> str:
        """
        Extrai conteúdo de texto de uma mensagem JSON.

        Suporta múltiplas estruturas de resposta do Claude Code.

        Args:
            json_data: Dicionário com dados da mensagem

        Returns:
            Texto extraído
        """
        # Campos diretos
        if "text" in json_data and isinstance(json_data["text"], str):
            return json_data["text"]

        if "content" in json_data and isinstance(json_data["content"], str):
            return json_data["content"]

        if "result" in json_data and isinstance(json_data["result"], str):
            return json_data["result"]

        if "message" in json_data and isinstance(json_data["message"], str):
            return json_data["message"]

        if "error" in json_data and isinstance(json_data["error"], str):
            return json_data["error"]

        # Estrutura de assistente com blocos de conteúdo
        message = json_data.get("message", {})
        if isinstance(message, dict):
            content = message.get("content", [])
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            texts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            # Incluir indicador de ferramenta
                            tool_name = block.get("name", "unknown")
                            texts.append(f"[executando: {tool_name}]")
                if texts:
                    return "\n".join(texts)

        # Fallback: tentar serializar como string
        return ""

    def _extract_safe_metadata(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai metadata segura de uma mensagem.

        Remove informações sensíveis como IDs internos, tokens, etc.

        Args:
            json_data: Dicionário com dados da mensagem

        Returns:
            Metadata sanitizada
        """
        safe_fields = [
            "type",
            "timestamp",
            "status",
            "success",
            "exit_code",
        ]

        metadata = {}
        for field in safe_fields:
            if field in json_data:
                metadata[field] = json_data[field]

        # Extrair usage se presente (tokens consumidos)
        if "usage" in json_data:
            usage = json_data["usage"]
            if isinstance(usage, dict):
                metadata["usage"] = {
                    k: v
                    for k, v in usage.items()
                    if k in ["input_tokens", "output_tokens", "total_tokens"]
                }

        return metadata

    def to_websocket_message(self, processed: ProcessedMessage) -> Dict[str, Any]:
        """
        Converte ProcessedMessage para formato de mensagem WebSocket.

        Args:
            processed: Mensagem processada

        Returns:
            Dicionário pronto para envio via WebSocket
        """
        msg = {
            "type": processed.type.value,
            "content": processed.content,
        }

        if processed.options:
            msg["options"] = processed.options

        if processed.metadata:
            msg["metadata"] = processed.metadata

        return msg

    def should_display(self, msg_type: MessageType) -> bool:
        """
        Verifica se uma mensagem deve ser exibida ao usuário.

        Alguns tipos como THINKING podem ser ocultados.

        Args:
            msg_type: Tipo da mensagem

        Returns:
            True se deve exibir, False caso contrário
        """
        # Por padrão, ocultar apenas THINKING
        return msg_type != MessageType.THINKING
