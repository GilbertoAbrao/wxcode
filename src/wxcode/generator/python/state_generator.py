"""
Gerador de arquivos de estado global para Python/FastAPI.

Este módulo implementa a geração de arquivos de estado global
para stack Python/FastAPI usando Dependency Injection.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from wxcode.generator.python.type_mapper import PythonTypeMapper
from wxcode.generator.state_generator import BaseStateGenerator
from wxcode.models.global_state_context import GlobalStateContext
from wxcode.parser.global_state_extractor import Scope


class PythonStateGenerator(BaseStateGenerator):
    """
    Gerador de estado global para Python/FastAPI.

    Gera 3 arquivos:
    - app/state.py: Dataclass AppState com variáveis globais
    - app/lifespan.py: Lifecycle manager (startup/shutdown)
    - app/dependencies.py: Funções Depends() para DI
    """

    def __init__(self):
        """Inicializa generator com PythonTypeMapper."""
        super().__init__(PythonTypeMapper())

        # Configura Jinja2
        templates_dir = Path(__file__).parent.parent / "templates" / "python"
        self.jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate(
        self, context: GlobalStateContext, output_dir: Path
    ) -> list[Path]:
        """
        Gera arquivos de estado para Python/FastAPI.

        Args:
            context: Contexto de estado global (IR stack-agnostic)
            output_dir: Diretório raiz de saída

        Returns:
            Lista de caminhos dos arquivos gerados
        """
        generated_files = []

        # Cria diretório app/ se não existir
        app_dir = output_dir / "app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Gera app/state.py
        state_file = self._generate_state_file(context, app_dir)
        generated_files.append(state_file)

        # Gera app/lifespan.py
        lifespan_file = self._generate_lifespan_file(context, app_dir)
        generated_files.append(lifespan_file)

        # Gera app/dependencies.py
        dependencies_file = self._generate_dependencies_file(context, app_dir)
        generated_files.append(dependencies_file)

        return generated_files

    def _generate_state_file(
        self, context: GlobalStateContext, app_dir: Path
    ) -> Path:
        """Gera app/state.py com dataclass AppState."""
        # Filtra apenas variáveis APP e MODULE (ignora REQUEST)
        app_vars = context.get_by_scope(Scope.APP)
        module_vars = context.get_by_scope(Scope.MODULE)
        variables = app_vars + module_vars

        # Mapeia variáveis para Python
        fields = []
        imports = set()

        for var in variables:
            mapped_type = self.type_mapper.map_type(var.wlanguage_type)
            normalized_name = self.normalize_var_name(var.name)

            # Adiciona import se necessário
            if mapped_type.import_statement:
                imports.add(mapped_type.import_statement)

            # Mapeia valor default
            default_value = None
            if var.default_value:
                default_value = self.type_mapper.map_default_value(
                    var.default_value, var.wlanguage_type
                )
            elif mapped_type.default_value:
                default_value = mapped_type.default_value

            fields.append({
                "name": normalized_name,
                "type": mapped_type.type_name,
                "default": default_value,
                "comment": f"Original: {var.name} ({var.wlanguage_type}) - {var.source_element}",
            })

        # Coleta sources únicos
        sources = list(set(var.source_element for var in variables))

        # Renderiza template
        template = self.jinja_env.get_template("state.py.j2")
        content = template.render(fields=fields, imports=sorted(imports), sources=sources)

        # Escreve arquivo
        state_file = app_dir / "state.py"
        state_file.write_text(content)

        return state_file

    def _generate_lifespan_file(
        self, context: GlobalStateContext, app_dir: Path
    ) -> Path:
        """Gera app/lifespan.py com lifecycle manager."""
        # Filtra apenas variáveis APP e MODULE
        app_vars = context.get_by_scope(Scope.APP)
        module_vars = context.get_by_scope(Scope.MODULE)
        variables = app_vars + module_vars

        # Prepara blocos de inicialização
        initialization_blocks = []
        imports = set()

        for block in context.initialization_blocks:
            # TODO: Converter código WLanguage para Python
            # Por enquanto, adiciona como comentário
            initialization_blocks.append({
                "comment": "Código de inicialização (TODO: converter WLanguage)",
                "code": f"# {block.code[:100]}...",  # Primeira linha como comentário
            })

        # Prepara campos do estado para inicialização
        state_fields = []
        for var in variables:
            mapped_type = self.type_mapper.map_type(var.wlanguage_type)
            normalized_name = self.normalize_var_name(var.name)

            # Valor de inicialização
            if var.default_value:
                init_value = self.type_mapper.map_default_value(
                    var.default_value, var.wlanguage_type
                )
            else:
                init_value = "None"

            state_fields.append({"name": normalized_name, "init_value": init_value})

        # Renderiza template
        template = self.jinja_env.get_template("lifespan.py.j2")
        content = template.render(
            imports=sorted(imports),
            initialization_blocks=initialization_blocks,
            state_fields=state_fields,
            has_cleanup=False,
            cleanup_blocks=[],
        )

        # Escreve arquivo
        lifespan_file = app_dir / "lifespan.py"
        lifespan_file.write_text(content)

        return lifespan_file

    def _generate_dependencies_file(
        self, context: GlobalStateContext, app_dir: Path
    ) -> Path:
        """Gera app/dependencies.py com funções Depends()."""
        # Filtra apenas variáveis APP e MODULE
        app_vars = context.get_by_scope(Scope.APP)
        module_vars = context.get_by_scope(Scope.MODULE)
        variables = app_vars + module_vars

        # Prepara campos
        fields = []
        for var in variables:
            mapped_type = self.type_mapper.map_type(var.wlanguage_type)
            normalized_name = self.normalize_var_name(var.name)

            fields.append({
                "name": normalized_name,
                "type": mapped_type.type_name,
                "original_name": var.name,
                "wlanguage_type": var.wlanguage_type,
            })

        # Renderiza template
        template = self.jinja_env.get_template("dependencies.py.j2")
        content = template.render(fields=fields)

        # Escreve arquivo
        dependencies_file = app_dir / "dependencies.py"
        dependencies_file.write_text(content)

        return dependencies_file

    def get_state_access(self, var_name: str) -> str:
        """
        Retorna código para acessar variável de estado.

        Args:
            var_name: Nome original da variável (ex: 'gCnn')

        Returns:
            Código de acesso Python (ex: 'app_state.db')
        """
        normalized = self.normalize_var_name(var_name)
        return f"app_state.{normalized}"

    def get_state_import(self) -> str:
        """
        Retorna import necessário para usar estado.

        Returns:
            Statement de import Python
        """
        return "from app.dependencies import get_app_state"
