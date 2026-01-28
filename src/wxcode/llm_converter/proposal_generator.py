"""ProposalGenerator - Gera proposals OpenSpec via LLM."""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from .models import LLMResponse, ProposalOutput
from .providers.base import BaseLLMProvider
from .providers.prompts import PROPOSAL_GENERATION_PROMPT

if TYPE_CHECKING:
    from ..models import Element


class ProposalGenerator:
    """Gera proposals OpenSpec para conversão de elementos WinDev."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        output_dir: Path | None = None,
    ):
        """Inicializa o gerador.

        Args:
            provider: Provider LLM a usar
            output_dir: Diretório de saída. Default: openspec/changes/
        """
        self.provider = provider
        if output_dir is None:
            output_dir = Path("openspec/changes")
        self.output_dir = output_dir

    async def generate(
        self,
        element: "Element",
        dep_specs_context: str = "",
    ) -> ProposalOutput:
        """Gera proposal OpenSpec para um elemento.

        Args:
            element: Elemento WinDev a converter
            dep_specs_context: Contexto formatado das specs das dependências

        Returns:
            ProposalOutput com conteúdo dos arquivos
        """
        # Construir mensagem para o LLM
        user_message = self._build_user_message(element, dep_specs_context)

        # Chamar LLM
        response = await self._call_llm(user_message)

        # Parsear resposta
        proposal_data = self._parse_response(response.content)

        # Construir resultado
        element_name = self._normalize_element_name(element.source_name)
        return ProposalOutput(
            element_id=str(element.id),
            element_name=element_name,
            proposal_md=proposal_data.get("proposal_md", ""),
            tasks_md=proposal_data.get("tasks_md", ""),
            spec_md=proposal_data.get("spec_md", ""),
            design_md=proposal_data.get("design_md"),
        )

    async def generate_and_save(
        self,
        element: "Element",
        dep_specs_context: str = "",
    ) -> tuple[ProposalOutput, Path]:
        """Gera proposal e salva em disco.

        Args:
            element: Elemento WinDev
            dep_specs_context: Contexto das dependências

        Returns:
            Tuple de (ProposalOutput, caminho da proposal)
        """
        proposal = await self.generate(element, dep_specs_context)

        # Criar diretório
        proposal_dir = self.output_dir / f"{proposal.element_name}-spec"
        proposal_dir.mkdir(parents=True, exist_ok=True)

        # Salvar arquivos
        (proposal_dir / "proposal.md").write_text(proposal.proposal_md)
        (proposal_dir / "tasks.md").write_text(proposal.tasks_md)

        if proposal.design_md:
            (proposal_dir / "design.md").write_text(proposal.design_md)

        # Criar spec em subdiretório
        spec_dir = proposal_dir / "specs" / f"{proposal.element_name}-spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / "spec.md").write_text(proposal.spec_md)

        return proposal, proposal_dir

    def _build_user_message(
        self,
        element: "Element",
        dep_specs_context: str,
    ) -> str:
        """Constrói mensagem para o LLM.

        Args:
            element: Elemento WinDev
            dep_specs_context: Contexto das dependências

        Returns:
            Mensagem formatada
        """
        parts = []

        # Adicionar contexto das dependências
        if dep_specs_context:
            parts.append("# Contexto: Specs das Dependências")
            parts.append("")
            parts.append(dep_specs_context)
            parts.append("")
            parts.append("---")
            parts.append("")

        # Informações do elemento
        parts.append(f"# Elemento a Converter: {element.source_name}")
        parts.append("")
        parts.append(f"- **Tipo:** {element.source_type}")
        parts.append(f"- **Arquivo:** {element.source_file}")
        parts.append(f"- **Camada:** {element.layer or 'não definida'}")
        parts.append("")

        # AST se disponível
        if element.ast:
            if procedures := element.ast.get("procedures"):
                parts.append("## Procedures")
                parts.append("")
                for proc in procedures:
                    parts.append(f"### {proc.get('name', 'unknown')}")
                    if sig := proc.get("signature"):
                        parts.append(f"Signature: `{sig}`")
                    parts.append("```wlanguage")
                    parts.append(proc.get("code", "// código não disponível"))
                    parts.append("```")
                    parts.append("")

            if controls := element.ast.get("controls"):
                parts.append("## Controles")
                parts.append("")
                for control in controls:
                    self._format_control(control, parts, indent=0)
                parts.append("")

            if events := element.ast.get("events"):
                parts.append("## Eventos")
                parts.append("")
                for event in events:
                    parts.append(f"- {event.get('name', 'unknown')}: {event.get('type', 'unknown')}")
                parts.append("")

        # Código fonte se disponível
        if element.raw_content:
            parts.append("## Código Fonte")
            parts.append("")
            parts.append("```wlanguage")
            # Limitar tamanho para não exceder contexto
            content = element.raw_content
            if len(content) > 50000:
                content = content[:50000] + "\n... (truncado)"
            parts.append(content)
            parts.append("```")
            parts.append("")

        # Dependências
        if element.dependencies:
            if element.dependencies.uses:
                parts.append("## Dependências")
                parts.append("")
                for dep in element.dependencies.uses:
                    parts.append(f"- {dep}")
                parts.append("")

        # Instrução final
        parts.append("---")
        parts.append("")
        parts.append("## Instrução")
        parts.append("")
        parts.append(
            "Gere uma proposal OpenSpec para documentar a conversão deste elemento "
            "para Python/FastAPI. Retorne APENAS o JSON, sem markdown ou explicações."
        )

        return "\n".join(parts)

    def _format_control(self, control: dict, parts: list[str], indent: int) -> None:
        """Formata controle recursivamente.

        Args:
            control: Dicionário do controle
            parts: Lista de partes da mensagem
            indent: Nível de indentação
        """
        prefix = "  " * indent
        name = control.get("name", "unknown")
        type_code = control.get("type_code", "?")
        parts.append(f"{prefix}- {name} [type={type_code}]")

        # Eventos
        for event in control.get("events", []):
            if code := event.get("code"):
                event_name = event.get("event_name", "event")
                parts.append(f"{prefix}  → {event_name}:")
                parts.append(f"{prefix}    ```wlanguage")
                for line in code.strip().split("\n"):
                    parts.append(f"{prefix}    {line}")
                parts.append(f"{prefix}    ```")

        # Filhos
        for child in control.get("children", []):
            self._format_control(child, parts, indent + 1)

    async def _call_llm(self, user_message: str) -> LLMResponse:
        """Chama o LLM com retry.

        Args:
            user_message: Mensagem do usuário

        Returns:
            Resposta do LLM
        """
        # Implementação simplificada - assume Anthropic provider
        # Em produção, deveria usar método abstrato no provider
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.provider.model,
            max_tokens=8192,
            system=PROPOSAL_GENERATION_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _parse_response(self, content: str) -> dict:
        """Parseia resposta JSON do LLM.

        Args:
            content: Conteúdo da resposta

        Returns:
            Dicionário com proposal_md, tasks_md, spec_md

        Raises:
            ValueError: Se não conseguir parsear
        """
        # Tentar JSON direto
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # Tentar extrair de bloco markdown
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Tentar encontrar JSON por chaves
        first_brace = content.find("{")
        last_brace = content.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(content[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response: {content[:200]}...")

    def _normalize_element_name(self, name: str) -> str:
        """Normaliza nome do elemento para formato de spec.

        Args:
            name: Nome original (ex: PAGE_Login)

        Returns:
            Nome normalizado (ex: page-login)
        """
        # Converte camelCase/PascalCase para kebab-case
        result = re.sub(r"([a-z])([A-Z])", r"\1-\2", name)
        # Converte underscores para hifens
        result = result.replace("_", "-")
        # Lowercase
        return result.lower()
