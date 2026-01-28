"""
Camada de segurança entre o usuário e o Claude Code.

Valida inputs, sanitiza outputs e controla ferramentas permitidas por contexto.
"""

import re
from typing import Tuple, List, Dict, Any


class Guardrail:
    """
    Camada de segurança para comunicação com Claude Code.

    Responsável por:
    - Validar e sanitizar inputs do usuário
    - Filtrar informações sensíveis dos outputs
    - Controlar ferramentas permitidas por contexto
    """

    # Padrões bloqueados no input
    BLOCKED_INPUT_PATTERNS = [
        # Comandos e credenciais originais
        (r"^/\w+", "Comandos slash não são permitidos"),
        (r"ANTHROPIC_API_KEY", "Referência a credenciais não permitida"),
        (r"WXCODE_LLM_KEY", "Referência a credenciais não permitida"),
        (r"\.credentials\.json", "Acesso a arquivos de credenciais não permitido"),
        # Comandos destrutivos
        (r"rm\s+-rf\s+/", "Comando destrutivo não permitido"),
        (r"sudo\s+", "Elevação de privilégio não permitida"),
        (r"chmod\s+777", "Mudança de permissões perigosa"),
        (r"curl.*\|\s*bash", "Execução de scripts remotos não permitida"),
        (r"wget.*\|\s*bash", "Execução de scripts remotos não permitida"),
        # Prompt injection - manipulação de instruções
        (r"ignore\s+(previous|above|all)", "Tentativa de manipulação detectada"),
        (r"disregard\s+(previous|above|all)", "Tentativa de manipulação detectada"),
        (r"forget\s+(everything|all|previous)", "Tentativa de manipulação detectada"),
        (r"new\s+instructions?:", "Tentativa de override detectada"),
        (r"system\s*prompt", "Acesso ao system prompt não permitido"),
        (r"override\s+(your|the)\s+(instructions|rules)", "Tentativa de override detectada"),
        # Prompt injection - jailbreak
        (r"DAN\s+mode", "Tentativa de jailbreak detectada"),
        (r"developer\s+mode", "Tentativa de jailbreak detectada"),
        (r"jailbreak", "Tentativa de jailbreak detectada"),
        (r"bypass\s+(safety|security|filter)", "Tentativa de bypass detectada"),
        # Prompt injection - roleplay malicioso
        (r"you\s+are\s+(now|a)\s+", "Tentativa de roleplay não permitida"),
        (r"pretend\s+(you|to\s+be)", "Tentativa de roleplay não permitida"),
        (r"act\s+as\s+if", "Tentativa de roleplay não permitida"),
        (r"imagine\s+you\s+are", "Tentativa de roleplay não permitida"),
        (r"roleplay\s+as", "Tentativa de roleplay não permitida"),
        # Code execution / injection
        (r"eval\s*\(", "Execução dinâmica não permitida"),
        (r"exec\s*\(", "Execução dinâmica não permitida"),
        (r"__import__\s*\(", "Import dinâmico não permitido"),
        (r"os\.system\s*\(", "Comando de sistema não permitido"),
        (r"subprocess\.(run|call|Popen)", "Subprocess não permitido"),
        (r"compile\s*\([^)]*exec", "Compilação para exec não permitida"),
        # SQL injection patterns
        (r";\s*(DROP|DELETE|TRUNCATE)\s+", "SQL injection detectado"),
        (r"UNION\s+SELECT", "SQL injection detectado"),
        (r"--\s*$", "SQL comment injection detectado"),
    ]

    # Padrões removidos/substituídos no output
    OUTPUT_SANITIZE_PATTERNS = [
        (r"claude\s+-p", "[assistant]"),
        (r"/home/claude/\.claude", "[config]"),
        (r"/home/node/\.claude", "[config]"),
        (r"~/.claude", "[config]"),
        (r"sk-ant-\w{3,}-[\w-]+", "[token]"),
        (r"/workspace/[a-zA-Z0-9_-]+/", ""),
    ]

    # Ferramentas permitidas por contexto
    ALLOWED_TOOLS_BY_CONTEXT = {
        "analysis": ["Read", "Grep", "Glob"],
        "conversion": ["Read", "Write", "Edit", "Bash(npm:*)"],
        "review": ["Read", "Grep"],
        "default": ["Read"],
    }

    # Limite de tamanho de mensagem
    MAX_MESSAGE_LENGTH = 10000

    @classmethod
    def validate_input(cls, message: str) -> Tuple[bool, str]:
        """
        Valida mensagem do usuário antes de enviar ao Claude Code.

        Args:
            message: Texto da mensagem do usuário

        Returns:
            Tupla (is_valid, error_message)
            - is_valid: True se mensagem é válida
            - error_message: Mensagem de erro (vazia se válida)
        """
        if not message or not message.strip():
            return False, "Mensagem vazia"

        # Verificar limite de tamanho
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return False, f"Mensagem muito longa (máximo {cls.MAX_MESSAGE_LENGTH} caracteres)"

        # Verificar padrões bloqueados
        message_lower = message.lower()
        for pattern, error_msg in cls.BLOCKED_INPUT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE | re.MULTILINE):
                return False, "Comando não permitido"

        return True, ""

    @classmethod
    def sanitize_output(cls, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove informações sensíveis do output.

        Args:
            output: Dicionário com dados do output do Claude Code

        Returns:
            Output sanitizado
        """
        sanitized = output.copy()

        # Sanitiza campo result se existir
        if "result" in sanitized and isinstance(sanitized["result"], str):
            result = sanitized["result"]
            for pattern, replacement in cls.OUTPUT_SANITIZE_PATTERNS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            sanitized["result"] = result

        # Sanitiza campo content se existir
        if "content" in sanitized and isinstance(sanitized["content"], str):
            content = sanitized["content"]
            for pattern, replacement in cls.OUTPUT_SANITIZE_PATTERNS:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            sanitized["content"] = content

        # Remove campos internos sensíveis
        sensitive_fields = ["session_id_internal", "container_id", "credentials"]
        for field in sensitive_fields:
            sanitized.pop(field, None)

        return sanitized

    @classmethod
    def get_allowed_tools(cls, context: str) -> List[str]:
        """
        Retorna ferramentas permitidas para o contexto.

        Args:
            context: Contexto da operação (analysis, conversion, review)

        Returns:
            Lista de ferramentas permitidas
        """
        return cls.ALLOWED_TOOLS_BY_CONTEXT.get(
            context,
            cls.ALLOWED_TOOLS_BY_CONTEXT["default"]
        )

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """
        Sanitiza uma string removendo padrões sensíveis.

        Args:
            text: Texto a ser sanitizado

        Returns:
            Texto sanitizado
        """
        result = text
        for pattern, replacement in cls.OUTPUT_SANITIZE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @classmethod
    def is_safe_path(cls, path: str) -> bool:
        """
        Verifica se um caminho de arquivo é seguro.

        Args:
            path: Caminho do arquivo

        Returns:
            True se o caminho é considerado seguro
        """
        dangerous_paths = [
            "/etc/",
            "/root/",
            "/.ssh/",
            "/.claude/",
            "/var/run/",
            ".credentials",
            ".env",
        ]
        path_lower = path.lower()
        return not any(dp in path_lower for dp in dangerous_paths)
