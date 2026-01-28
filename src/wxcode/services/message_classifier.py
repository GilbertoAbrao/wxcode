"""
Classificador de mensagens JSON do Claude Code.

Identifica o tipo semântico de cada mensagem para adaptar a UI.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    """Tipos de mensagens do Claude Code."""

    QUESTION = "question"  # Pergunta simples esperando resposta
    MULTI_QUESTION = "multi_question"  # Múltiplas perguntas/opções estruturadas
    INFO = "info"  # Informação/status a ser exibida
    TOOL_RESULT = "tool_result"  # Resultado de execução de ferramenta
    ERROR = "error"  # Mensagem de erro
    THINKING = "thinking"  # Processo de raciocínio (pode ocultar)


class MessageClassifier:
    """
    Classifica mensagens JSON do Claude Code em tipos semânticos.

    Usa heurísticas baseadas em:
    - Estrutura do JSON (campos presentes)
    - Padrões de texto (regex)
    - Tipo declarado no JSON
    """

    # Padrões para identificar perguntas (pré-compilados para performance)
    _QUESTION_PATTERNS = [
        re.compile(r"\?\s*$", re.MULTILINE),  # Termina com ?
        re.compile(r"what\s+would\s+you", re.IGNORECASE),
        re.compile(r"which\s+option", re.IGNORECASE),
        re.compile(r"do\s+you\s+want", re.IGNORECASE),
        re.compile(r"should\s+I", re.IGNORECASE),
        re.compile(r"would\s+you\s+like", re.IGNORECASE),
        re.compile(r"can\s+you\s+confirm", re.IGNORECASE),
        re.compile(r"please\s+(choose|select)", re.IGNORECASE),
    ]

    # Padrões para identificar erros
    _ERROR_PATTERNS = [
        re.compile(r"error:", re.IGNORECASE),
        re.compile(r"failed\s+to", re.IGNORECASE),
        re.compile(r"exception:", re.IGNORECASE),
        re.compile(r"cannot\s+(find|read|write|access)", re.IGNORECASE),
    ]

    # Padrões para identificar thinking/raciocínio
    _THINKING_PATTERNS = [
        re.compile(r"^let\s+me\s+(think|analyze|check)", re.IGNORECASE),
        re.compile(r"^I('m|\s+am)\s+(thinking|analyzing|checking)", re.IGNORECASE),
        re.compile(r"^analyzing", re.IGNORECASE),
    ]

    def classify(self, json_data: Dict[str, Any]) -> MessageType:
        """
        Classifica uma mensagem JSON do Claude Code.

        Args:
            json_data: Dicionário com dados da mensagem

        Returns:
            MessageType correspondente
        """
        if not json_data:
            return MessageType.INFO

        # 1. Verificar tipo explícito no JSON
        msg_type = json_data.get("type", "")

        if msg_type == "error":
            return MessageType.ERROR

        if msg_type == "tool_result" or "tool_use" in json_data:
            return MessageType.TOOL_RESULT

        # 2. Verificar estrutura de multi-question (AskUserQuestion)
        if self._is_multi_question(json_data):
            return MessageType.MULTI_QUESTION

        # 3. Extrair conteúdo de texto para análise
        text_content = self._extract_text(json_data)

        if not text_content:
            return MessageType.INFO

        # 4. Verificar padrões de erro no texto
        if self._matches_patterns(text_content, self._ERROR_PATTERNS):
            return MessageType.ERROR

        # 5. Verificar padrões de thinking
        if self._matches_patterns(text_content, self._THINKING_PATTERNS):
            return MessageType.THINKING

        # 6. Verificar padrões de pergunta
        if self._matches_patterns(text_content, self._QUESTION_PATTERNS):
            return MessageType.QUESTION

        # 7. Default: informação
        return MessageType.INFO

    def _is_multi_question(self, json_data: Dict[str, Any]) -> bool:
        """
        Verifica se é uma estrutura de múltiplas perguntas/opções.

        Detecta:
        - AskUserQuestion do Claude Code
        - Arrays de opções
        - Estruturas com 'questions' ou 'options'
        """
        # Verificar AskUserQuestion
        if json_data.get("type") == "AskUserQuestion":
            return True

        # Verificar campo 'questions' com array
        questions = json_data.get("questions")
        if isinstance(questions, list) and len(questions) > 0:
            return True

        # Verificar campo 'options' com array
        options = json_data.get("options")
        if isinstance(options, list) and len(options) > 1:
            return True

        # Verificar em content se é assistente
        message = json_data.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    # Verificar tool_use do tipo AskUserQuestion
                    if block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        if "ask" in tool_name.lower() or "question" in tool_name.lower():
                            return True
                        # Verificar input com options
                        tool_input = block.get("input", {})
                        if isinstance(tool_input.get("questions"), list):
                            return True
                        if isinstance(tool_input.get("options"), list):
                            return True

        return False

    def _extract_text(self, json_data: Dict[str, Any]) -> str:
        """
        Extrai conteúdo de texto de uma mensagem JSON.

        Suporta várias estruturas:
        - Campo 'text' direto
        - Campo 'content' string
        - Campo 'message.content' array com blocos de texto
        - Campo 'result'
        """
        # Campo direto
        if "text" in json_data and isinstance(json_data["text"], str):
            return json_data["text"]

        if "content" in json_data and isinstance(json_data["content"], str):
            return json_data["content"]

        if "result" in json_data and isinstance(json_data["result"], str):
            return json_data["result"]

        if "message" in json_data and isinstance(json_data["message"], str):
            return json_data["message"]

        # Estrutura de assistente com blocos
        message = json_data.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            return "\n".join(texts)

        return ""

    def _matches_patterns(
        self, text: str, patterns: List[re.Pattern]
    ) -> bool:
        """
        Verifica se o texto corresponde a algum dos padrões.

        Args:
            text: Texto a verificar
            patterns: Lista de regex compilados

        Returns:
            True se algum padrão corresponder
        """
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False

    def extract_options(self, json_data: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """
        Extrai opções de uma mensagem multi-question.

        Args:
            json_data: Dicionário com dados da mensagem

        Returns:
            Lista de opções ou None se não houver
        """
        # Verificar campo 'options' direto
        options = json_data.get("options")
        if isinstance(options, list):
            return self._normalize_options(options)

        # Verificar em questions
        questions = json_data.get("questions", [])
        if isinstance(questions, list) and len(questions) > 0:
            first_q = questions[0]
            if isinstance(first_q, dict):
                opts = first_q.get("options", [])
                if opts:
                    return self._normalize_options(opts)

        # Verificar em tool_use input
        message = json_data.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_input = block.get("input", {})
                    questions = tool_input.get("questions", [])
                    if isinstance(questions, list) and len(questions) > 0:
                        first_q = questions[0]
                        if isinstance(first_q, dict):
                            opts = first_q.get("options", [])
                            if opts:
                                return self._normalize_options(opts)

        return None

    def _normalize_options(self, options: List[Any]) -> List[Dict[str, str]]:
        """
        Normaliza opções para formato consistente.

        Args:
            options: Lista de opções (strings ou dicts)

        Returns:
            Lista de dicts com 'label' e 'value'
        """
        normalized = []
        for opt in options:
            if isinstance(opt, str):
                normalized.append({"label": opt, "value": opt})
            elif isinstance(opt, dict):
                normalized.append({
                    "label": opt.get("label", opt.get("text", str(opt))),
                    "value": opt.get("value", opt.get("label", str(opt))),
                    "description": opt.get("description", ""),
                })
        return normalized
