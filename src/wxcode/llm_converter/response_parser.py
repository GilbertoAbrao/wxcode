"""ResponseParser - Parseia e valida resposta JSON do LLM."""

import ast
import json
import re
from typing import Any

from .models import (
    ConversionResult,
    DependencyList,
    InvalidOutputError,
    RouteDefinition,
    StaticFile,
    TemplateDefinition,
)


class ResponseParser:
    """Parseia e valida resposta JSON do LLM."""

    def parse(self, raw_response: str) -> ConversionResult:
        """Parseia resposta e valida estrutura.

        Args:
            raw_response: Resposta bruta do LLM

        Returns:
            ConversionResult validado

        Raises:
            InvalidOutputError: Se a resposta não for válida
        """
        # Extrair JSON
        data = self._extract_json(raw_response)

        # Validar campos obrigatórios
        self._validate_required_fields(data)

        # Validar código Python
        python_errors = self._validate_python_syntax(data["route"]["code"])
        if python_errors:
            # Adicionar aos notes mas não falhar
            if "notes" not in data:
                data["notes"] = []
            data["notes"].extend([f"Python syntax warning: {e}" for e in python_errors])

        # Validar HTML
        html_errors = self._validate_html_structure(data["template"]["content"])
        if html_errors:
            if "notes" not in data:
                data["notes"] = []
            data["notes"].extend([f"HTML warning: {e}" for e in html_errors])

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
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Tentar encontrar JSON começando com {
        brace_match = re.search(r"\{.*\}", response, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
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
        required = ["page_name", "route", "template"]
        missing = [f for f in required if f not in data]
        if missing:
            raise InvalidOutputError(f"Missing required fields: {missing}")

        # Validar route
        route_required = ["path", "methods", "filename", "code"]
        route_missing = [f for f in route_required if f not in data.get("route", {})]
        if route_missing:
            raise InvalidOutputError(f"Missing route fields: {route_missing}")

        # Validar template
        template_required = ["filename", "content"]
        template_missing = [
            f for f in template_required if f not in data.get("template", {})
        ]
        if template_missing:
            raise InvalidOutputError(f"Missing template fields: {template_missing}")

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

    def _validate_html_structure(self, html: str) -> list[str]:
        """Validação básica de estrutura HTML.

        Args:
            html: Código HTML/Jinja2

        Returns:
            Lista de warnings encontrados
        """
        warnings = []

        # Verificar se estende base.html
        if "{% extends" not in html:
            warnings.append("Template does not extend base.html")

        # Verificar se tem block content
        if "{% block content %}" not in html and "{% block content%}" not in html:
            warnings.append("Template missing {% block content %}")

        # Verificar tags não fechadas (básico)
        open_tags = re.findall(r"<(\w+)[^>]*>", html)
        close_tags = re.findall(r"</(\w+)>", html)

        # Tags que não precisam fechar
        void_tags = {
            "br", "hr", "img", "input", "meta", "link",
            "area", "base", "col", "embed", "param", "source", "track", "wbr"
        }

        open_count: dict[str, int] = {}
        for tag in open_tags:
            tag_lower = tag.lower()
            if tag_lower not in void_tags:
                open_count[tag_lower] = open_count.get(tag_lower, 0) + 1

        close_count: dict[str, int] = {}
        for tag in close_tags:
            tag_lower = tag.lower()
            close_count[tag_lower] = close_count.get(tag_lower, 0) + 1

        # Verificar desbalanceamento
        for tag, count in open_count.items():
            closed = close_count.get(tag, 0)
            if count > closed:
                warnings.append(f"Possible unclosed <{tag}> tag")

        return warnings

    def _build_result(self, data: dict[str, Any]) -> ConversionResult:
        """Constrói ConversionResult a partir do dicionário.

        Args:
            data: Dicionário validado

        Returns:
            ConversionResult
        """
        # Route
        route = RouteDefinition(
            path=data["route"]["path"],
            methods=data["route"]["methods"],
            filename=data["route"]["filename"],
            code=data["route"]["code"],
        )

        # Template
        template = TemplateDefinition(
            filename=data["template"]["filename"],
            content=data["template"]["content"],
        )

        # Static files (pode ser lista de dicts ou lista de strings)
        static_files = []
        for sf in data.get("static_files", []):
            if isinstance(sf, str):
                # LLM retornou apenas path, sem conteúdo
                static_files.append(StaticFile(
                    filename=sf,
                    content="",  # Conteúdo vazio - arquivo precisa existir
                ))
            elif isinstance(sf, dict):
                static_files.append(StaticFile(
                    filename=sf.get("filename", ""),
                    content=sf.get("content", ""),
                ))

        # Dependencies
        deps_data = data.get("dependencies", {})
        dependencies = DependencyList(
            services=deps_data.get("services", []),
            models=deps_data.get("models", []),
            missing=deps_data.get("missing", []),
        )

        return ConversionResult(
            page_name=data["page_name"],
            route=route,
            template=template,
            static_files=static_files,
            dependencies=dependencies,
            notes=data.get("notes", []),
        )
