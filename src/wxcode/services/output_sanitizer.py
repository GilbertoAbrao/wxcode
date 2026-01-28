"""
Sanitizador de output do Claude Code.

Remove referências à CLI subjacente e detalhes técnicos internos
para que o usuário não saiba qual ferramenta está rodando por trás.
"""

import re
from typing import Dict, List, Tuple


class OutputSanitizer:
    """
    Sanitiza output do Claude Code removendo informações sensíveis.

    Responsável por:
    - Remover referências a CLIs específicas (Claude-Code, Codex, GPT, etc.)
    - Remover referências a providers (Anthropic, OpenAI, etc.)
    - Remover detalhes técnicos internos (tool_use_id, MCP, flags, etc.)
    """

    # Padrões para sanitizar referências a CLIs (pré-compilados)
    _CLI_PATTERNS: List[Tuple[re.Pattern, str]] = [
        # Claude Code variations
        (re.compile(r"claude[\s-]?code", re.IGNORECASE), "[assistant]"),
        (re.compile(r"claude\s+cli", re.IGNORECASE), "[assistant]"),
        (re.compile(r"@anthropic-ai/claude-code", re.IGNORECASE), "[assistant]"),
        # Other AI CLIs
        (re.compile(r"\bcodex\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bgpt-?4\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bgpt-?3\.?5?\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bchatgpt\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bcopilot\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bgemini\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bclaude\s+opus\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bclaude\s+sonnet\b", re.IGNORECASE), "[assistant]"),
        (re.compile(r"\bclaude\s+haiku\b", re.IGNORECASE), "[assistant]"),
    ]

    # Padrões para sanitizar referências a providers
    _PROVIDER_PATTERNS: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"\banthropic\b", re.IGNORECASE), "[provider]"),
        (re.compile(r"\bopenai\b", re.IGNORECASE), "[provider]"),
        (re.compile(r"\bgoogle\s+ai\b", re.IGNORECASE), "[provider]"),
        (re.compile(r"\bmicrosoft\s+ai\b", re.IGNORECASE), "[provider]"),
    ]

    # Padrões para remover detalhes técnicos internos
    _INTERNAL_PATTERNS: List[Tuple[re.Pattern, str]] = [
        # Comandos internos
        (re.compile(r"/(gsd|wxcode):\w+", re.IGNORECASE), "[workflow]"),
        (re.compile(r"--output-format\s+\w+"), ""),
        (re.compile(r"--allowedTools\s+[\w,]+"), ""),
        (re.compile(r"--verbose\b"), ""),
        (re.compile(r"-p\s+['\"]"), ""),
        # IDs e tokens
        (re.compile(r"tool_use_id:\s*[\w-]+"), ""),
        (re.compile(r"toolu_[\w]+"), "[tool]"),
        (re.compile(r"msg_[\w]+"), "[msg]"),
        (re.compile(r"sk-ant-[\w-]+"), "[token]"),
        (re.compile(r"sk-[\w-]{20,}"), "[token]"),
        # MCP e serviços
        (re.compile(r"MCP\s+server", re.IGNORECASE), "[service]"),
        (re.compile(r"mcp__\w+__\w+"), "[tool]"),
        # Caminhos internos
        (re.compile(r"/home/claude/\.claude[\w/]*"), "[config]"),
        (re.compile(r"/home/node/\.claude[\w/]*"), "[config]"),
        (re.compile(r"~/\.claude[\w/]*"), "[config]"),
        (re.compile(r"/workspace/[\w-]+/"), ""),
        # Container/Docker
        (re.compile(r"container[_-]?id:\s*[\w]+", re.IGNORECASE), ""),
        (re.compile(r"docker\s+exec\b", re.IGNORECASE), ""),
    ]

    # Padrões para limpar formatação excessiva
    _CLEANUP_PATTERNS: List[Tuple[re.Pattern, str]] = [
        # Múltiplos espaços em branco
        (re.compile(r"  +"), " "),
        # Múltiplas quebras de linha
        (re.compile(r"\n{3,}"), "\n\n"),
        # Espaços antes de pontuação
        (re.compile(r"\s+([.,;:!?])"), r"\1"),
    ]

    def sanitize(self, content: str) -> str:
        """
        Sanitiza conteúdo removendo informações sensíveis.

        Args:
            content: Texto a ser sanitizado

        Returns:
            Texto sanitizado
        """
        if not content:
            return content

        result = content

        # 1. Sanitizar referências a CLIs
        for pattern, replacement in self._CLI_PATTERNS:
            result = pattern.sub(replacement, result)

        # 2. Sanitizar referências a providers
        for pattern, replacement in self._PROVIDER_PATTERNS:
            result = pattern.sub(replacement, result)

        # 3. Remover detalhes técnicos internos
        for pattern, replacement in self._INTERNAL_PATTERNS:
            result = pattern.sub(replacement, result)

        # 4. Limpar formatação
        for pattern, replacement in self._CLEANUP_PATTERNS:
            result = pattern.sub(replacement, result)

        return result.strip()

    def sanitize_dict(self, data: Dict) -> Dict:
        """
        Sanitiza todos os campos de texto de um dicionário.

        Args:
            data: Dicionário com dados a sanitizar

        Returns:
            Dicionário com valores sanitizados
        """
        if not data:
            return data

        result = data.copy()

        # Campos de texto comuns para sanitizar
        text_fields = ["text", "content", "result", "message", "error"]

        for field in text_fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.sanitize(result[field])

        # Processar recursivamente campos aninhados
        if "message" in result and isinstance(result["message"], dict):
            result["message"] = self.sanitize_dict(result["message"])

        # Processar array de content
        if "content" in result and isinstance(result["content"], list):
            sanitized_content = []
            for item in result["content"]:
                if isinstance(item, dict):
                    sanitized_item = item.copy()
                    if "text" in sanitized_item:
                        sanitized_item["text"] = self.sanitize(sanitized_item["text"])
                    sanitized_content.append(sanitized_item)
                elif isinstance(item, str):
                    sanitized_content.append(self.sanitize(item))
                else:
                    sanitized_content.append(item)
            result["content"] = sanitized_content

        # Remover campos sensíveis
        sensitive_fields = [
            "session_id_internal",
            "container_id",
            "credentials",
            "api_key",
            "token",
        ]
        for field in sensitive_fields:
            result.pop(field, None)

        return result
