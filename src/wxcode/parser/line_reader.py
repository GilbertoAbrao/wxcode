"""
Leitor de linhas com streaming para arquivos grandes.

Suporta arquivos com 100k+ linhas sem carregar tudo na memória.
"""

import aiofiles
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator


@dataclass
class LineContext:
    """Contexto de uma linha durante o streaming."""
    line_number: int
    content: str
    indent: int
    stripped: str

    @property
    def is_list_item(self) -> bool:
        """Verifica se é um item de lista (começa com -)."""
        return self.stripped == "-"

    @property
    def is_key_value(self) -> bool:
        """Verifica se é um par chave:valor."""
        return " : " in self.stripped

    def parse_key_value(self) -> tuple[str, str]:
        """Extrai chave e valor."""
        if not self.is_key_value:
            return "", ""
        parts = self.stripped.split(" : ", 1)
        key = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else ""
        # Remove aspas
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return key, value


async def read_lines(file_path: Path) -> AsyncIterator[LineContext]:
    """
    Lê arquivo linha por linha de forma assíncrona.

    Args:
        file_path: Caminho do arquivo

    Yields:
        LineContext para cada linha
    """
    async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        line_number = 0
        async for line in f:
            line_number += 1
            content = line.rstrip('\n\r')
            stripped = content.strip()
            indent = len(content) - len(content.lstrip())

            yield LineContext(
                line_number=line_number,
                content=content,
                indent=indent,
                stripped=stripped
            )


async def count_lines(file_path: Path) -> int:
    """
    Conta linhas do arquivo de forma eficiente.

    Args:
        file_path: Caminho do arquivo

    Returns:
        Número total de linhas
    """
    count = 0
    async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        async for _ in f:
            count += 1
    return count
