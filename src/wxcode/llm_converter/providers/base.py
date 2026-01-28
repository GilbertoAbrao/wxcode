"""BaseLLMProvider - Classe base com funcionalidades comuns."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable

from ..models import ConversionContext, LLMResponse, ProcedureContext


class BaseLLMProvider(ABC):
    """Classe base com funcionalidades comuns para todos os providers."""

    def __init__(
        self,
        model: str,
        max_retries: int = 3,
        timeout: int = 120,
    ):
        """Inicializa o provider base.

        Args:
            model: Nome do modelo a usar
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos
        """
        self._model = model
        self.max_retries = max_retries
        self.timeout = timeout

    @property
    def model(self) -> str:
        """Modelo em uso."""
        return self._model

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do provider."""
        ...

    @abstractmethod
    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Executa conversão de página usando o LLM."""
        ...

    @abstractmethod
    async def convert_procedure(self, context: ProcedureContext) -> LLMResponse:
        """Executa conversão de procedure group usando o LLM."""
        ...

    @abstractmethod
    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Estima custo em USD."""
        ...

    @classmethod
    @abstractmethod
    def available_models(cls) -> list[str]:
        """Lista modelos disponíveis."""
        ...

    def _build_user_message(self, context: ConversionContext) -> str:
        """Formata o contexto como mensagem para o usuário.

        Args:
            context: Contexto da conversão

        Returns:
            Mensagem formatada
        """
        parts = []

        # Incluir theme skills se disponíveis
        if context.theme_skills:
            parts.append("# Theme Reference")
            parts.append("")
            parts.append(f"Using theme: **{context.theme}**")
            parts.append("")
            parts.append(
                "Use the component patterns and classes from the theme reference below "
                "when generating HTML. Follow the exact class names and structure shown."
            )
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append(context.theme_skills)
            parts.append("")
            parts.append("---")
            parts.append("")

        parts.extend([
            f"# Converter Página: {context.page_name}",
            "",
            "## Hierarquia de Controles",
            "",
        ])

        # Serializar controles em formato legível
        for control in context.controls:
            parts.append(self._format_control(control, indent=0))

        # Adicionar procedures locais
        if context.local_procedures:
            parts.append("")
            parts.append("## Procedures Locais")
            parts.append("")
            for proc in context.local_procedures:
                parts.append(f"### {proc.get('name', 'unknown')}")
                parts.append("```wlanguage")
                parts.append(proc.get("code", "// código não disponível"))
                parts.append("```")
                parts.append("")

        # Adicionar procedures globais referenciadas
        if context.referenced_procedures:
            parts.append("")
            parts.append("## Procedures Globais Referenciadas")
            parts.append("")
            parts.append(
                "Estas procedures são chamadas nos eventos acima. "
                "Use a lógica abaixo para implementar a funcionalidade correta."
            )
            parts.append("")
            for proc in context.referenced_procedures:
                parts.append(f"### {proc.get('name', 'unknown')}")
                if sig := proc.get("signature"):
                    parts.append(f"Signature: `{sig}`")
                parts.append("```wlanguage")
                parts.append(proc.get("code", "// código não disponível"))
                parts.append("```")
                parts.append("")

        # Adicionar dependências
        if context.dependencies:
            parts.append("")
            parts.append("## Dependências Referenciadas")
            parts.append("")
            for dep in context.dependencies:
                if isinstance(dep, str):
                    parts.append(f"- {dep}")
                else:
                    parts.append(f"- {dep}")

        parts.append("")
        parts.append("## Instrução")
        parts.append("")
        parts.append(
            "Converta esta página para FastAPI + Jinja2. "
            "Retorne APENAS o JSON, sem markdown ou explicações."
        )

        return "\n".join(parts)

    def _format_control(self, control: dict, indent: int = 0) -> str:
        """Formata um controle para exibição.

        Args:
            control: Dicionário do controle
            indent: Nível de indentação

        Returns:
            String formatada do controle
        """
        prefix = "  " * indent
        name = control.get("name", "unknown")
        type_code = control.get("type_code", "?")

        # Propriedades relevantes
        props = control.get("properties", {}) or {}
        prop_parts = []

        if props.get("width") and props.get("height"):
            prop_parts.append(f"{props['width']}x{props['height']}")

        if not props.get("visible", True):
            prop_parts.append("hidden")

        if props.get("tab_order"):
            prop_parts.append(f"tab={props['tab_order']}")

        props_str = f" ({', '.join(prop_parts)})" if prop_parts else ""

        lines = [f"{prefix}- {name} [type={type_code}]{props_str}"]

        # Eventos com código completo
        events = control.get("events", []) or []
        for event in events:
            code = event.get("code")
            if code and code.strip():
                event_type = event.get("type_code", "?")
                event_name = event.get("event_name", f"event_{event_type}")
                lines.append(f"{prefix}  → {event_name} [type={event_type}]:")
                lines.append(f"{prefix}    ```wlanguage")
                for code_line in code.strip().split('\n'):
                    lines.append(f"{prefix}    {code_line}")
                lines.append(f"{prefix}    ```")

        # Filhos recursivamente
        for child in control.get("children", []):
            lines.append(self._format_control(child, indent + 1))

        return "\n".join(lines)

    async def _call_with_retry(
        self,
        call_fn: Callable[[], dict[str, Any]],
        retry_exceptions: tuple[type[Exception], ...],
    ) -> dict[str, Any]:
        """Chama função com retry e backoff exponencial.

        Args:
            call_fn: Função síncrona que executa a chamada
            retry_exceptions: Tupla de exceções que devem causar retry

        Returns:
            Dicionário com content, input_tokens, output_tokens

        Raises:
            Exception: Se todas as tentativas falharem
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Executar chamada síncrona em thread separada
                response = await asyncio.to_thread(call_fn)
                return response

            except retry_exceptions as e:
                last_error = e
                wait_time = 2 ** attempt  # 1, 2, 4 segundos
                await asyncio.sleep(wait_time)

        raise last_error  # type: ignore

    def _build_procedure_user_message(self, context: ProcedureContext) -> str:
        """Formata o contexto de procedure group como mensagem.

        Args:
            context: Contexto do procedure group

        Returns:
            Mensagem formatada
        """
        parts = [
            f"# Converter Grupo de Procedures: {context.group_name}",
            "",
            f"Arquivo fonte: `{context.source_file}`",
            "",
            f"Total de procedures: {len(context.procedures)}",
            "",
            "---",
            "",
            "## Procedures do Grupo",
            "",
        ]

        # Serializar cada procedure
        for proc in context.procedures:
            name = proc.get("name", "unknown")
            signature = proc.get("signature", "")
            code = proc.get("code", "// código não disponível")
            return_type = proc.get("return_type", "")

            parts.append(f"### {name}")
            if signature:
                parts.append(f"Signature: `{signature}`")
            if return_type:
                parts.append(f"Return type: `{return_type}`")
            parts.append("")
            parts.append("```wlanguage")
            parts.append(code)
            parts.append("```")
            parts.append("")

        # Adicionar procedures referenciadas de outros grupos
        if context.referenced_procedures:
            parts.append("---")
            parts.append("")
            parts.append("## Procedures de Outros Grupos (Referenciadas)")
            parts.append("")
            parts.append(
                "Estas procedures são chamadas pelo grupo acima. "
                "Use-as como referência para dependências."
            )
            parts.append("")
            for proc in context.referenced_procedures:
                name = proc.get("name", "unknown")
                code = proc.get("code", "// código não disponível")
                parts.append(f"### {name}")
                parts.append("```wlanguage")
                parts.append(code)
                parts.append("```")
                parts.append("")

        parts.append("---")
        parts.append("")
        parts.append("## Instrução")
        parts.append("")
        parts.append(
            "Converta este grupo de procedures para uma classe Python async. "
            "Retorne APENAS o JSON, sem markdown ou explicações."
        )

        return "\n".join(parts)
