"""ServiceResponseParser - Parseia e valida resposta JSON do LLM para services."""

import ast
import json
import re
from typing import Any

from .models import (
    InvalidOutputError,
    ServiceConversionResult,
)


class ServiceResponseParser:
    """Parseia e valida resposta JSON do LLM para services Python."""

    def parse(self, raw_response: str) -> ServiceConversionResult:
        """Parseia resposta e valida estrutura.

        Args:
            raw_response: Resposta bruta do LLM

        Returns:
            ServiceConversionResult validado

        Raises:
            InvalidOutputError: Se a resposta não for válida
        """
        # Extrair JSON
        data = self._extract_json(raw_response)

        # Validar campos obrigatórios
        self._validate_required_fields(data)

        # Validar código Python
        python_errors = self._validate_python_syntax(data["code"])
        if python_errors:
            # Adicionar aos notes mas não falhar
            if "notes" not in data:
                data["notes"] = []
            data["notes"].extend([f"Python syntax warning: {e}" for e in python_errors])

        # Construir resultado
        return self._build_result(data)

    def _extract_json(self, response: str) -> dict[str, Any]:
        """Extrai JSON da resposta (pode estar em markdown).

        Args:
            response: Resposta do LLM

        Returns:
            Dicionário parseado

        Raises:
            InvalidOutputError: Se não conseguir extrair JSON válido
        """
        # Tentar parsear direto
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Tentar extrair de bloco markdown ```json ... ```
        # Usa greedy matching para pegar todo o conteúdo até o último ```
        json_match = re.search(r"```(?:json)?\s*\n(.*)\n```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Tentar encontrar todos os blocos ``` e testar cada um
        code_blocks = re.findall(r"```(?:json)?\s*\n([\s\S]*?)```", response)
        for block in code_blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue

        # Tentar encontrar JSON começando com { e terminando com }
        # Encontra a primeira { e a última }
        first_brace = response.find("{")
        last_brace = response.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(response[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        raise InvalidOutputError(
            f"Could not extract valid JSON from response: {response[:200]}..."
        )

    def _validate_required_fields(self, data: dict[str, Any]) -> None:
        """Valida campos obrigatórios.

        Args:
            data: Dicionário parseado

        Raises:
            InvalidOutputError: Se campos obrigatórios estiverem faltando
        """
        required = ["class_name", "filename", "code"]
        missing = [f for f in required if f not in data]
        if missing:
            raise InvalidOutputError(f"Missing required fields: {missing}")

        # Verificar se code não está vazio
        if not data["code"].strip():
            raise InvalidOutputError("code field is empty")

    def _validate_python_syntax(self, code: str) -> list[str]:
        """Valida sintaxe Python usando ast.parse.

        Args:
            code: Código Python

        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
        return errors

    def _build_result(self, data: dict[str, Any]) -> ServiceConversionResult:
        """Constrói ServiceConversionResult a partir do dicionário.

        Args:
            data: Dicionário validado

        Returns:
            ServiceConversionResult
        """
        return ServiceConversionResult(
            class_name=data["class_name"],
            filename=data["filename"],
            imports=data.get("imports", []),
            code=data["code"],
            dependencies=data.get("dependencies", []),
            notes=data.get("notes", []),
        )
