"""OutputWriter - Escreve arquivos gerados no projeto target."""

import logging
import re
from pathlib import Path

import aiofiles

from .import_validator import ImportValidator
from .models import ConversionResult, RouteDefinition, TemplateDefinition

logger = logging.getLogger(__name__)


class OutputWriter:
    """Escreve arquivos gerados no projeto target."""

    def __init__(self, output_dir: Path):
        """Inicializa o OutputWriter.

        Args:
            output_dir: Diretório raiz do projeto target
        """
        self.output_dir = Path(output_dir)
        self.import_validator = ImportValidator(output_dir)

    async def write(self, result: ConversionResult) -> list[Path]:
        """Escreve todos os arquivos do resultado.

        Args:
            result: Resultado da conversão

        Returns:
            Lista de caminhos dos arquivos criados
        """
        files_created: list[Path] = []

        # Escrever rota
        route_path = await self._write_route(result.route)
        files_created.append(route_path)

        # Escrever template
        template_path = await self._write_template(result.template)
        files_created.append(template_path)

        # Escrever arquivos estáticos
        for static_file in result.static_files:
            # Strip leading slash to avoid absolute path issues
            filename = static_file.filename.lstrip("/")
            path = self.output_dir / filename
            await self._write_file(path, static_file.content)
            files_created.append(path)

        # Atualizar router __init__.py usando o filename real da rota
        await self._update_router_init(result.route.filename)

        # Gerar stubs para dependências faltantes
        stub_paths = await self._generate_stubs(result.dependencies.missing)
        files_created.extend(stub_paths)

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

    async def _write_route(self, route: RouteDefinition) -> Path:
        """Escreve arquivo de rota.

        Validates imports before writing, removing any that reference
        non-existent modules.

        Args:
            route: Definição da rota

        Returns:
            Caminho do arquivo criado
        """
        path = self.output_dir / route.filename

        # Validate and fix imports
        fixed_code, removed_imports = self.import_validator.validate_and_fix(route.code)

        if removed_imports:
            for module in removed_imports:
                logger.warning(f"Import removido de {route.filename}: {module} (módulo não encontrado)")

        await self._write_file(path, fixed_code)
        return path

    async def _write_template(self, template: TemplateDefinition) -> Path:
        """Escreve arquivo de template.

        Args:
            template: Definição do template

        Returns:
            Caminho do arquivo criado
        """
        path = self.output_dir / template.filename
        await self._write_file(path, template.content)
        return path

    async def _update_router_init(self, route_filename: str) -> None:
        """Atualiza __init__.py do router para incluir nova rota.

        Args:
            route_filename: Caminho do arquivo de rota (ex: app/routers/auth.py)
        """
        init_path = self.output_dir / "app" / "routers" / "__init__.py"

        # Criar arquivo se não existir
        if not init_path.exists():
            init_path.parent.mkdir(parents=True, exist_ok=True)
            initial_content = '''"""Routers package."""

from fastapi import APIRouter

router = APIRouter()

# Routers serão incluídos aqui
'''
            await self._write_file(init_path, initial_content)

        # Ler conteúdo atual
        async with aiofiles.open(init_path, "r", encoding="utf-8") as f:
            content = await f.read()

        # Extrair nome do módulo do filename (ex: app/routers/auth.py -> auth)
        route_path = Path(route_filename)
        module_name = route_path.stem  # Remove .py extension
        router_var = f"{module_name}_router"
        import_line = f"from .{module_name} import router as {router_var}"
        include_line = f'router.include_router({router_var}, tags=["{module_name}"])'

        # Verificar se já existe
        if import_line in content:
            return

        # Parse: separar imports, router declaration e includes
        lines = content.split("\n")
        imports: list[str] = []
        router_decl: list[str] = []
        includes: list[str] = []
        other: list[str] = []

        section = "imports"
        for line in lines:
            stripped = line.strip()

            # Detectar início do bloco router
            if "router = APIRouter()" in line:
                section = "router"
                router_decl.append(line)
                continue

            # Detectar includes
            if stripped.startswith("router.include_router("):
                section = "includes"
                includes.append(line)
                continue

            # Classificar linha
            if section == "imports":
                imports.append(line)
            elif section == "router":
                # Linhas entre router= e primeiro include
                if stripped and not stripped.startswith("#"):
                    router_decl.append(line)
                else:
                    other.append(line)
            elif section == "includes":
                if stripped.startswith("router.include_router("):
                    includes.append(line)
                else:
                    other.append(line)

        # Adicionar novo import (após os existentes from .)
        imports.append(import_line)

        # Adicionar novo include
        includes.append(include_line)

        # Reconstruir arquivo
        result_lines = imports + ["", ""] + router_decl + includes + [""]

        # Remover linhas vazias excessivas
        content_new = "\n".join(result_lines)
        # Normalizar múltiplas linhas vazias para no máximo 2
        while "\n\n\n" in content_new:
            content_new = content_new.replace("\n\n\n", "\n\n")

        await self._write_file(init_path, content_new)

    async def _generate_stubs(self, missing: list[str]) -> list[Path]:
        """Gera stubs para dependências não encontradas.

        Args:
            missing: Lista de dependências faltantes

        Returns:
            Lista de caminhos dos stubs criados
        """
        paths: list[Path] = []

        for dep in missing:
            # Determinar tipo de stub
            if dep.endswith("Service") or "Service" in dep:
                path = await self._generate_service_stub(dep)
            elif dep.startswith("class") or dep[0].isupper():
                path = await self._generate_model_stub(dep)
            else:
                path = await self._generate_function_stub(dep)

            if path:
                paths.append(path)

        return paths

    async def _generate_service_stub(self, name: str) -> Path:
        """Gera stub de service.

        Args:
            name: Nome do service

        Returns:
            Caminho do arquivo criado
        """
        # Converter nome para snake_case
        snake_name = self._to_snake_case(name)
        filename = f"{snake_name}.py"
        path = self.output_dir / "app" / "services" / filename

        content = f'''"""Stub para {name} - TODO: Implementar."""


class {name}:
    """TODO: Implementar {name}.

    Este stub foi gerado automaticamente porque a dependência
    não foi encontrada no código fonte original.
    """

    async def execute(self, *args, **kwargs):
        """TODO: Implementar lógica."""
        raise NotImplementedError("{name} não implementado")
'''

        await self._write_file(path, content)
        return path

    async def _generate_model_stub(self, name: str) -> Path:
        """Gera stub de model.

        Args:
            name: Nome do model

        Returns:
            Caminho do arquivo criado
        """
        snake_name = self._to_snake_case(name)
        filename = f"{snake_name}.py"
        path = self.output_dir / "app" / "models" / filename

        content = f'''"""Stub para {name} - TODO: Implementar."""

from pydantic import BaseModel


class {name}(BaseModel):
    """TODO: Implementar {name}.

    Este stub foi gerado automaticamente porque a dependência
    não foi encontrada no código fonte original.
    """

    # TODO: Adicionar campos
    pass
'''

        await self._write_file(path, content)
        return path

    async def _generate_function_stub(self, name: str) -> Path:
        """Gera stub de função.

        Args:
            name: Nome da função

        Returns:
            Caminho do arquivo criado
        """
        snake_name = self._to_snake_case(name)
        filename = f"{snake_name}.py"
        path = self.output_dir / "app" / "utils" / filename

        content = f'''"""Stub para {name} - TODO: Implementar."""


async def {snake_name}(*args, **kwargs):
    """TODO: Implementar {snake_name}.

    Este stub foi gerado automaticamente porque a dependência
    não foi encontrada no código fonte original.
    """
    raise NotImplementedError("{name} não implementado")
'''

        await self._write_file(path, content)
        return path

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
