"""
MilestonePromptBuilder - Constroi MILESTONE-CONTEXT.md para conversao de elemento.

Este servico gera o prompt contextualizado com dados do elemento, stack alvo,
e instrucoes para o workflow GSD de conversao.
"""

from wxcode.models.output_project import OutputProject
from wxcode.models.stack import Stack
from wxcode.services.gsd_context_collector import GSDContextData


MILESTONE_PROMPT_TEMPLATE = '''# Milestone Context for GSD

> **LANGUAGE**: Always respond in **Brazilian Portuguese (pt-BR)**.

## Objective

Convert the element **{element_name}** from WinDev/WebDev to the target stack:
- **Stack:** {stack_name}
- **Language:** {language}
- **Framework:** {framework}

## Element Overview

- **Name:** {element_name}
- **Type:** {element_type}
- **Layer:** {element_layer}
- **Project:** {project_name}

## Element Statistics

- Controls: {controls_total} ({controls_with_code} with code)
- Local Procedures: {local_procedures_count}
- Variables: {variables_count}
- Dependencies: {uses_count} used, {used_by_count} dependent
- Bound Tables: {bound_tables_count}

## Stack Characteristics

### File Structure
{file_structure}

### Type Mappings ({language})
{type_mappings}

### Model Template
```{language}
{model_template}
```

## Element Source Code

The full element source code is in `element.json` under `raw_content`.

## Controls Hierarchy

See `controls.json` for the complete control tree with:
- Event handlers (OnClick, OnChange, etc.)
- Data bindings (FileToScreen/ScreenToFile)
- Properties (width, height, position, etc.)

## Local Procedures

See `element.json` under `local_procedures` for all procedures defined in this element.

## Dependencies

See `dependencies.json` for:
- Elements this uses (calls, imports)
- Elements that use this (dependents)
- Database tables accessed
- External APIs called

## Instructions

1. Analyze the element structure and business logic
2. Generate equivalent {framework} code following stack conventions
3. Create models for bound database tables
4. Convert procedures to service methods
5. Generate route handlers for page events
6. Create template/component for UI structure

## Files Reference

| File | Content |
|------|---------|
| element.json | Full element (AST, raw_content, local_procedures, dependencies) |
| controls.json | Control hierarchy with events, properties, bindings |
| dependencies.json | Dependency graph |
| related-elements.json | Direct dependencies |
{schema_row}
{neo4j_row}

**WXCODE Workflow**: Ready for `/wxcode:new-milestone`
'''


class MilestonePromptBuilder:
    """
    Constroi o conteudo de MILESTONE-CONTEXT.md para conversao de elemento.

    Utiliza GSDContextData coletado pelo GSDContextCollector e metadata
    do Stack e OutputProject para gerar um prompt contextualizado.
    """

    @classmethod
    def build_context(
        cls,
        gsd_data: GSDContextData,
        stack: Stack,
        output_project: OutputProject,
    ) -> str:
        """
        Constroi o conteudo completo do MILESTONE-CONTEXT.md.

        Args:
            gsd_data: Dados coletados pelo GSDContextCollector
            stack: Stack de tecnologia alvo
            output_project: OutputProject pai

        Returns:
            Conteudo formatado do MILESTONE-CONTEXT.md
        """
        # Extrair dados do elemento
        element = gsd_data.element
        stats = gsd_data.stats
        project = gsd_data.project
        dependencies = gsd_data.dependencies

        # Contar dependencias
        uses_count = len(dependencies.get("uses", []))
        used_by_count = len(dependencies.get("used_by", []))

        # Formatar file_structure e type_mappings como YAML-like
        file_structure = cls._format_dict(stack.file_structure)
        type_mappings = cls._format_dict(stack.type_mappings)

        # Linhas opcionais para tabela de arquivos
        schema_row = "| schema.json | Bound tables |" if gsd_data.bound_tables else ""
        neo4j_row = "| neo4j-analysis.json | Impact analysis |" if gsd_data.neo4j_available else ""

        # Gerar prompt
        return MILESTONE_PROMPT_TEMPLATE.format(
            element_name=element.source_name,
            element_type=element.source_type.value if hasattr(element.source_type, 'value') else str(element.source_type),
            element_layer=element.layer.value if element.layer and hasattr(element.layer, 'value') else "unknown",
            project_name=project.name,
            stack_name=stack.name,
            language=stack.language,
            framework=stack.framework,
            controls_total=stats.get("controls_total", 0),
            controls_with_code=stats.get("controls_with_code", 0),
            local_procedures_count=stats.get("local_procedures_count", 0),
            variables_count=stats.get("variables_count", 0),
            uses_count=uses_count,
            used_by_count=used_by_count,
            bound_tables_count=len(gsd_data.bound_tables),
            file_structure=file_structure if file_structure else "# No file structure defined",
            type_mappings=type_mappings if type_mappings else "# No type mappings defined",
            model_template=stack.model_template or "# No template",
            schema_row=schema_row,
            neo4j_row=neo4j_row,
        )

    @staticmethod
    def _format_dict(d: dict, indent: int = 0) -> str:
        """
        Formata dict como string estilo YAML para melhor legibilidade.

        Args:
            d: Dicionario a formatar
            indent: Nivel de indentacao atual

        Returns:
            String formatada estilo YAML
        """
        if not d:
            return ""

        lines = []
        prefix = "  " * indent

        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                nested = MilestonePromptBuilder._format_dict(v, indent + 1)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{prefix}{k}: {v}")

        return "\n".join(lines)
