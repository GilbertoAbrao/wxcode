"""
Extrator de blocos COMPILE IF de código WLanguage.

Este módulo é responsável por detectar e extrair blocos condicionais
de compilação (COMPILE IF) que dependem de configurations específicas,
transformando-os em uma representação estruturada.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class CompileIfBlock:
    """Bloco COMPILE IF extraído do código WLanguage.

    Attributes:
        conditions: Lista de nomes de configurations referenciadas no bloco.
            Ex: ["Producao", "API_Producao"]
        operator: Operador lógico entre conditions ("OR", "AND", ou None para single condition).
        code: Código dentro do bloco COMPILE IF.
        start_line: Linha onde o bloco começa (0-indexed).
        end_line: Linha onde o bloco termina (0-indexed).
    """
    conditions: list[str]
    operator: Optional[str]
    code: str
    start_line: int
    end_line: int


@dataclass
class ExtractedVariable:
    """Variável extraída de um bloco COMPILE IF.

    Attributes:
        name: Nome da variável normalizado (UPPER_SNAKE_CASE).
            Ex: "URL_API", "GPARAMS_URL"
        value: Valor atribuído à variável (string literal).
        var_type: Tipo da declaração ("CONSTANT" ou "GLOBAL").
        configurations: Lista de configurations onde esta variável está definida.
    """
    name: str
    value: str
    var_type: str
    configurations: list[str]


class CompileIfExtractor:
    """Extrator de blocos COMPILE IF e suas variáveis."""

    # Regex para detectar blocos COMPILE IF
    # Captura: Configuration="Name" ou Configuration="A" OR Configuration="B"
    COMPILE_IF_PATTERN = re.compile(
        r'<COMPILE\s+IF\s+(.+?)>\s*\n(.*?)\n\s*<END>',
        re.IGNORECASE | re.DOTALL
    )

    # Regex para extrair conditions específicas
    CONDITION_PATTERN = re.compile(
        r'Configuration\s*=\s*"([^"]+)"',
        re.IGNORECASE
    )

    # Regex para detectar operador entre conditions
    OPERATOR_PATTERN = re.compile(
        r'\b(OR|AND)\b',
        re.IGNORECASE
    )

    # Regex para extrair declarações CONSTANT
    # Usa greedy .+ para capturar tudo até fim de linha
    CONSTANT_PATTERN = re.compile(
        r'CONSTANT\s+(\w+)\s*=\s*(.+)$',
        re.IGNORECASE | re.MULTILINE
    )

    # Regex para extrair atribuições globais (gVar.X = ...)
    # Usa greedy .+ para capturar tudo até fim de linha
    GLOBAL_ASSIGN_PATTERN = re.compile(
        r'(g\w+)\.(\w+)\s*=\s*(.+)$',
        re.IGNORECASE | re.MULTILINE
    )

    def extract(self, code: str) -> list[CompileIfBlock]:
        """Extrai todos os blocos COMPILE IF do código.

        Args:
            code: Código WLanguage fonte.

        Returns:
            Lista de CompileIfBlock encontrados.
        """
        blocks: list[CompileIfBlock] = []

        # Remove blocos comentados (linhas que começam com //)
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.lstrip()
            # Se a linha é um comentário, não incluir
            if not stripped.startswith('//'):
                cleaned_lines.append(line)

        cleaned_code = '\n'.join(cleaned_lines)

        # Encontra todos os blocos COMPILE IF
        for match in self.COMPILE_IF_PATTERN.finditer(cleaned_code):
            condition_clause = match.group(1)
            block_code = match.group(2)

            # Extrai todas as conditions
            conditions = self.CONDITION_PATTERN.findall(condition_clause)

            # Detecta operador (OR ou AND)
            operator_match = self.OPERATOR_PATTERN.search(condition_clause)
            operator = operator_match.group(1).upper() if operator_match else None

            # Calcula linhas (aproximação baseada em posição)
            start_pos = match.start()
            end_pos = match.end()
            start_line = cleaned_code[:start_pos].count('\n')
            end_line = cleaned_code[:end_pos].count('\n')

            blocks.append(CompileIfBlock(
                conditions=conditions,
                operator=operator,
                code=block_code,
                start_line=start_line,
                end_line=end_line
            ))

        return blocks

    def extract_variables(self, blocks: list[CompileIfBlock]) -> list[ExtractedVariable]:
        """Extrai variáveis dos blocos COMPILE IF.

        Args:
            blocks: Lista de blocos COMPILE IF.

        Returns:
            Lista de ExtractedVariable encontradas.
        """
        variables: list[ExtractedVariable] = []

        for block in blocks:
            # Expande configurations baseado no operador
            if block.operator == "OR":
                # Cada condition pode ter a variável
                configs = block.conditions
            elif block.operator == "AND":
                # Todas as conditions devem estar presentes (interseção)
                # Para simplificar, usamos todas as conditions
                configs = block.conditions
            else:
                # Single condition
                configs = block.conditions

            # Extrai CONSTANTs
            for const_match in self.CONSTANT_PATTERN.finditer(block.code):
                var_name = const_match.group(1)
                var_value = const_match.group(2).strip()

                # Remove comentários // apenas se estiver fora de aspas
                # Se há aspas no valor, não fazer split porque // pode ser parte da string
                if '//' in var_value and ('"' not in var_value and "'" not in var_value):
                    var_value = var_value.split('//')[0].strip()

                # Remove aspas se for string
                var_value = var_value.strip('"').strip("'")

                # Normaliza nome para UPPER_SNAKE_CASE
                normalized_name = self._normalize_variable_name(var_name)

                variables.append(ExtractedVariable(
                    name=normalized_name,
                    value=var_value,
                    var_type="CONSTANT",
                    configurations=configs.copy()
                ))

            # Extrai atribuições globais
            for global_match in self.GLOBAL_ASSIGN_PATTERN.finditer(block.code):
                prefix = global_match.group(1)  # gParams, gVar, etc.
                field = global_match.group(2)
                var_value = global_match.group(3).strip()

                # Remove comentários // apenas se estiver fora de aspas
                # Se há aspas no valor, não fazer split porque // pode ser parte da string
                if '//' in var_value and ('"' not in var_value and "'" not in var_value):
                    var_value = var_value.split('//')[0].strip()

                # Remove aspas se for string
                var_value = var_value.strip('"').strip("'")

                # Normaliza: gParams.URL → GPARAMS_URL
                normalized_name = self._normalize_variable_name(f"{prefix}_{field}")

                variables.append(ExtractedVariable(
                    name=normalized_name,
                    value=var_value,
                    var_type="GLOBAL",
                    configurations=configs.copy()
                ))

        return variables

    def _normalize_variable_name(self, name: str) -> str:
        """Normaliza nome de variável para UPPER_SNAKE_CASE.

        Args:
            name: Nome original da variável.

        Returns:
            Nome normalizado.

        Examples:
            >>> self._normalize_variable_name("URL_API")
            "URL_API"
            >>> self._normalize_variable_name("gParams_URL")
            "GPARAMS_URL"
        """
        # Remove prefixos comuns e converte para upper
        name = name.replace('.', '_')
        return name.upper()
