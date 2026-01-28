"""ServiceOutputWriter - Escreve arquivos de service gerados no projeto target."""

import re
from pathlib import Path

import aiofiles

from .models import ServiceConversionResult


class ServiceOutputWriter:
    """Escreve arquivos de service gerados no projeto target."""

    def __init__(self, output_dir: Path):
        """Inicializa o ServiceOutputWriter.

        Args:
            output_dir: Diretório raiz do projeto target
        """
        self.output_dir = Path(output_dir)

    async def write(self, result: ServiceConversionResult) -> list[Path]:
        """Escreve todos os arquivos do resultado.

        Args:
            result: Resultado da conversão de service

        Returns:
            Lista de caminhos dos arquivos criados
        """
        files_created: list[Path] = []

        # Escrever arquivo de service
        service_path = await self._write_service(result)
        files_created.append(service_path)

        # Atualizar services __init__.py
        await self._update_services_init(result.class_name, result.filename)

        return files_created

    async def _write_file(self, path: Path, content: str) -> Path:
        """Escreve conteúdo em arquivo.

        Args:
            path: Caminho do arquivo
            content: Conteúdo a escrever

        Returns:
            Caminho do arquivo criado
        """
        # Criar diretórios se necessário
        path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)

        return path

    async def _write_service(self, result: ServiceConversionResult) -> Path:
        """Escreve arquivo de service.

        Args:
            result: Resultado da conversão

        Returns:
            Caminho do arquivo criado
        """
        path = self.output_dir / "app" / "services" / result.filename

        # Construir conteúdo completo com imports
        content_parts = []

        # Docstring
        content_parts.append(f'"""Service {result.class_name}."""')
        content_parts.append("")

        # Imports
        for imp in result.imports:
            content_parts.append(imp)

        if result.imports:
            content_parts.append("")

        # Código da classe
        content_parts.append(result.code)
        content_parts.append("")

        content = "\n".join(content_parts)
        await self._write_file(path, content)
        return path

    async def _update_services_init(self, class_name: str, filename: str) -> None:
        """Atualiza __init__.py dos services para incluir novo service.

        Args:
            class_name: Nome da classe do service
            filename: Nome do arquivo do service
        """
        init_path = self.output_dir / "app" / "services" / "__init__.py"

        # Criar arquivo se não existir
        if not init_path.exists():
            init_path.parent.mkdir(parents=True, exist_ok=True)
            initial_content = '''"""Services package."""

# Services serão importados aqui
'''
            await self._write_file(init_path, initial_content)

        # Ler conteúdo atual
        async with aiofiles.open(init_path, "r", encoding="utf-8") as f:
            content = await f.read()

        # Nome do módulo (sem .py)
        module_name = filename.replace(".py", "")
        import_line = f"from .{module_name} import {class_name}"

        # Verificar se já existe
        if import_line in content:
            return

        # Adicionar import
        lines = content.split("\n")
        new_lines = []
        import_added = False

        for line in lines:
            new_lines.append(line)

            # Adicionar após a docstring
            if not import_added and line.strip() == '"""Services package."""':
                # Encontrar próxima linha vazia ou comentário
                new_lines.append("")
                new_lines.append(import_line)
                import_added = True

        # Se não encontrou lugar para import, adicionar no final
        if not import_added:
            new_lines.append("")
            new_lines.append(import_line)

        content_new = "\n".join(new_lines)

        # Garantir que não há linhas em branco excessivas
        while "\n\n\n" in content_new:
            content_new = content_new.replace("\n\n\n", "\n\n")

        await self._write_file(init_path, content_new)

    def _to_snake_case(self, name: str) -> str:
        """Converte nome para snake_case.

        Args:
            name: Nome em CamelCase ou outro formato

        Returns:
            Nome em snake_case
        """
        # Inserir underscore antes de maiúsculas
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        # Inserir underscore antes de maiúsculas seguidas de minúsculas
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()
