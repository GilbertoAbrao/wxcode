"""
Parser de queries do PDF de documentação WebDev.

Extrai SQL e parâmetros de queries (.WDR) a partir do PDF exportado.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


@dataclass
class QueryInfo:
    """Informações extraídas de uma query."""
    name: str
    sql: str
    parameters: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    has_sql: bool = True


class QueryParser:
    """
    Parser de queries do PDF de documentação.

    Extrai:
    - Nome da query
    - SQL completo (após marcador "SQL code of {NAME}")
    - Parâmetros ({ParamName})
    - Tabelas referenciadas (FROM, JOIN)
    """

    # Marcador que indica início do SQL
    SQL_MARKER_PATTERN = r'SQL code of ([A-Za-z0-9_]+)'

    # Padrão para extrair parâmetros
    PARAM_PATTERN = r'\{([A-Za-z0-9_]+)\}'

    # Padrões para extrair tabelas
    FROM_PATTERN = r'\bFROM\s+([A-Za-z0-9_]+)'
    JOIN_PATTERN = r'\bJOIN\s+([A-Za-z0-9_]+)'

    def parse(self, pdf_path: Path) -> QueryInfo:
        """
        Parseia PDF de uma query e extrai informações.

        Args:
            pdf_path: Caminho para o PDF da query

        Returns:
            QueryInfo com SQL e metadados extraídos
        """
        doc = fitz.open(str(pdf_path))
        query_name = pdf_path.stem  # Nome do arquivo sem extensão
        sql = ""

        try:
            # Extrai todo o texto do PDF
            full_text = ""
            for page in doc:
                full_text += page.get_text()

            # Busca pelo marcador "SQL code of {NAME}"
            marker_match = re.search(self.SQL_MARKER_PATTERN, full_text, re.IGNORECASE)

            if marker_match:
                # Atualiza nome da query se encontrado no marcador
                query_name = marker_match.group(1)

                # Extrai SQL após o marcador
                marker_pos = marker_match.end()
                sql = self._extract_sql(full_text[marker_pos:])

            # Extrai parâmetros e tabelas
            parameters = self._extract_parameters(sql)
            tables = self._extract_tables(sql)

            return QueryInfo(
                name=query_name,
                sql=sql.strip(),
                parameters=parameters,
                tables=tables,
                has_sql=bool(sql.strip())
            )

        finally:
            doc.close()

    def _extract_sql(self, text: str) -> str:
        """
        Extrai SQL após o marcador.

        Args:
            text: Texto após "SQL code of {NAME}"

        Returns:
            SQL extraído
        """
        # Remove texto extra no início
        lines = text.split('\n')
        sql_lines = []
        started = False

        for line in lines:
            stripped = line.strip()

            # Pula linhas vazias ou de cabeçalho no início
            if not started:
                # Começa quando encontra SELECT, WITH, ou outra palavra-chave SQL
                if any(stripped.upper().startswith(kw) for kw in [
                    'SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE'
                ]):
                    started = True
                    sql_lines.append(line)
                continue

            # Para quando encontra marcador de nova seção ou fim
            if any(marker in stripped for marker in [
                'Part ', '›', 'Linkpay_ADM', '1/2/2026'
            ]):
                break

            sql_lines.append(line)

        return '\n'.join(sql_lines)

    def _extract_parameters(self, sql: str) -> list[str]:
        """
        Extrai parâmetros no formato {ParamName} do SQL.

        Args:
            sql: SQL da query

        Returns:
            Lista de nomes de parâmetros (sem duplicatas)
        """
        matches = re.findall(self.PARAM_PATTERN, sql)
        # Remove duplicatas preservando ordem
        seen = set()
        params = []
        for param in matches:
            if param not in seen:
                seen.add(param)
                params.append(param)
        return params

    def _extract_tables(self, sql: str) -> list[str]:
        """
        Extrai tabelas referenciadas no SQL.

        Args:
            sql: SQL da query

        Returns:
            Lista de nomes de tabelas (sem duplicatas)
        """
        tables = set()

        # Extrai de FROM
        from_matches = re.findall(self.FROM_PATTERN, sql, re.IGNORECASE)
        tables.update(from_matches)

        # Extrai de JOIN
        join_matches = re.findall(self.JOIN_PATTERN, sql, re.IGNORECASE)
        tables.update(join_matches)

        return sorted(list(tables))
