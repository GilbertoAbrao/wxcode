"""
CLI do WXCODE.

Comandos para importar, analisar, converter e exportar projetos WinDev.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import typer

# Carrega variáveis de ambiente do .env
load_dotenv()
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from wxcode import __version__
from wxcode.config import get_settings

# Cria aplicação Typer
app = typer.Typer(
    name="wxcode",
    help="Conversor universal de projetos WinDev/WebDev/WinDev Mobile",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Exibe versão e sai."""
    if value:
        console.print(f"[bold blue]wxcode[/] versão [green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Exibe a versão do wxcode",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    WXCODE - Conversor Universal WinDev/WebDev/WinDev Mobile

    Converte projetos da plataforma PC Soft para stacks modernas.
    Stack padrão: FastAPI + Jinja2
    """
    pass


@app.command("import")
def import_project(
    project_path: Path = typer.Argument(
        ...,
        help="Caminho para o arquivo .wwp/.wdp/.wpp do projeto",
        exists=True,
        readable=True,
    ),
    batch_size: int = typer.Option(
        100,
        "--batch-size",
        "-b",
        help="Número de elementos por batch para inserção no MongoDB",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Sobrescreve projeto existente (faz purge automático)",
    ),
    workspace_id: Optional[str] = typer.Option(
        None,
        "--workspace-id",
        help="ID do workspace (8 hex chars) para associar ao projeto",
    ),
    workspace_path: Optional[str] = typer.Option(
        None,
        "--workspace-path",
        help="Caminho do diretorio do workspace",
    ),
) -> None:
    """
    Importa um projeto WinDev/WebDev/WinDev Mobile para o banco de dados.

    Usa streaming para processar arquivos grandes (100k+ linhas) eficientemente.
    Extrai metadados do projeto e mapeia todos os elementos para o MongoDB.

    Se o projeto já existir:
    - Sem --force: exibe erro e sugere usar --force
    - Com --force: faz purge do projeto existente e reimporta
    """
    # Variável para armazenar o nome do projeto (detectado do arquivo)
    detected_project_name: str | None = None

    async def _import() -> None:
        nonlocal detected_project_name
        from wxcode.database import init_db, close_db
        from wxcode.parser.project_mapper import ProjectElementMapper
        from wxcode.models import Project
        from wxcode.services import purge_project_by_name

        # Callback de progresso
        def on_progress(lines_done: int, total_lines: int, elements: int) -> None:
            percent = (lines_done / total_lines) * 100 if total_lines else 0
            console.print(
                f"\r[dim]Linhas: {lines_done:,}/{total_lines:,} ({percent:.1f}%) | "
                f"Elementos: {elements:,}[/]",
                end=""
            )

        console.print(Panel(
            f"[bold]Arquivo:[/] {project_path}\n"
            f"[bold]Batch size:[/] {batch_size}",
            title="Importando Projeto",
            border_style="blue",
        ))

        # Conecta ao banco
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando ao MongoDB...", total=None)
            client = await init_db()
            progress.update(task, description="Conectado ao MongoDB")

        # Detecta nome do projeto do arquivo antes de criar
        mapper = ProjectElementMapper(
            project_path,
            on_progress,
            workspace_id=workspace_id,
            workspace_path=workspace_path,
        )
        mapper.BATCH_SIZE = batch_size

        # Extrai metadados para verificar nome
        await mapper._extract_project_metadata()
        detected_project_name = mapper._project_data.get("name", project_path.stem)

        # Verifica se projeto já existe
        existing_project = await Project.find_one(Project.name == detected_project_name)
        if existing_project:
            if force:
                # Purge automático
                console.print(f"\n[yellow]Projeto '{detected_project_name}' já existe. Removendo...[/]")
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Removendo projeto existente...", total=None)
                    purge_stats = await purge_project_by_name(detected_project_name)
                    progress.update(task, description="Projeto removido")

                console.print(f"[dim]Removidos: {purge_stats.total} documentos[/]")
            else:
                # Erro: projeto já existe
                console.print(f"\n[red]Erro:[/] Projeto '{detected_project_name}' já existe!")
                console.print(f"[dim]Use --force para sobrescrever o projeto existente.[/]")
                await close_db(client)
                raise typer.Exit(1)

        # Mapeia projeto com streaming (reseta mapper para nova importação)
        mapper = ProjectElementMapper(
            project_path,
            on_progress,
            workspace_id=workspace_id,
            workspace_path=workspace_path,
        )
        mapper.BATCH_SIZE = batch_size
        project, stats = await mapper.map()

        console.print("")  # Nova linha após progresso

        # Fecha conexão
        await close_db(client)

        # Exibe resultado
        table = Table(title="Resultado da Importação")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        table.add_row("Projeto", project.name)
        table.add_row("Versão WinDev", f"{project.major_version}.{project.minor_version}")
        table.add_row("Total de linhas", f"{stats.total_lines:,}")
        table.add_row("Elementos mapeados", f"{stats.elements_saved:,}")
        table.add_row("Configurações", str(stats.configurations_found))
        table.add_row("Tempo", f"{stats.duration_seconds:.2f}s")

        if stats.errors:
            table.add_row("Erros", str(len(stats.errors)))

        console.print(table)

        # Mostra distribuição por tipo
        if project.elements_by_type:
            console.print("\n[bold]Distribuição por tipo:[/]")
            for elem_type, count in sorted(project.elements_by_type.items()):
                console.print(f"  [cyan]{elem_type}:[/] {count}")

        # Mostra erros se houver
        if stats.errors:
            console.print("\n[yellow]Erros encontrados:[/]")
            for error in stats.errors[:5]:
                console.print(f"  [red]•[/] Batch {error['batch_size']}: {error['error']}")
            if len(stats.errors) > 5:
                console.print(f"  [dim]... e mais {len(stats.errors) - 5} erros[/]")

    asyncio.run(_import())


@app.command("init-project")
def init_project(
    output_dir: Path = typer.Argument(
        ...,
        help="Diretório onde criar o projeto",
    ),
    name: str = typer.Option(
        "app",
        "--name",
        "-n",
        help="Nome do projeto",
    ),
    use_postgres: bool = typer.Option(
        False,
        "--postgres",
        help="Usar PostgreSQL ao invés de MongoDB",
    ),
    no_docker: bool = typer.Option(
        False,
        "--no-docker",
        help="Não gerar arquivos Docker",
    ),
    no_tests: bool = typer.Option(
        False,
        "--no-tests",
        help="Não gerar arquivos de teste",
    ),
) -> None:
    """
    Gera o starter kit da stack target (FastAPI + Jinja2).

    Cria a estrutura base do projeto que será populada
    pelas conversões de páginas via LLM.

    Exemplos:
      wxcode init-project ./meu-projeto
      wxcode init-project ./meu-projeto --name MeuApp
      wxcode init-project ./meu-projeto --postgres
    """
    from wxcode.generator.starter_kit import StarterKitConfig, StarterKitGenerator

    config = StarterKitConfig(
        project_name=name,
        use_mongodb=not use_postgres,
        include_docker=not no_docker,
        include_tests=not no_tests,
    )

    console.print(Panel(
        f"[bold]Projeto:[/] {name}\n"
        f"[bold]Diretório:[/] {output_dir}\n"
        f"[bold]Database:[/] {'PostgreSQL' if use_postgres else 'MongoDB'}\n"
        f"[bold]Docker:[/] {'Não' if no_docker else 'Sim'}\n"
        f"[bold]Testes:[/] {'Não' if no_tests else 'Sim'}",
        title="[blue]Gerando Starter Kit[/]",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Criando estrutura...", total=None)

        generator = StarterKitGenerator(output_dir, config)
        result = generator.generate()

        progress.update(task, description="Concluído!")

    # Mostra resultado
    console.print(f"\n[green]✓ Starter kit criado com sucesso![/]")
    console.print(f"  [bold]Diretórios:[/] {len(result.directories_created)}")
    console.print(f"  [bold]Arquivos:[/] {len(result.files_created)}")

    # Mostra próximos passos
    console.print("\n[bold]Próximos passos:[/]")
    console.print(f"  1. cd {output_dir}")
    console.print("  2. pip install -e .")
    console.print("  3. cp .env.example .env")
    console.print("  4. uvicorn app.main:app --reload")


@app.command()
def analyze(
    project: str = typer.Argument(..., help="Nome do projeto"),
    build_graph: bool = typer.Option(
        True,
        "--build-graph/--no-graph",
        help="Construir grafo de dependências",
    ),
    export_dot: Optional[Path] = typer.Option(
        None,
        "--export-dot",
        "-e",
        help="Exportar grafo para arquivo DOT (Graphviz)",
    ),
    export_html: Optional[Path] = typer.Option(
        None,
        "--export-html",
        "-h",
        help="Exportar grafo para HTML interativo (vis.js)",
    ),
    no_persist: bool = typer.Option(
        False,
        "--no-persist",
        help="Não persistir ordem topológica no MongoDB",
    ),
) -> None:
    """
    Analisa dependências de um projeto importado.

    Constrói o grafo de dependências, detecta ciclos e calcula
    a ordem topológica para conversão em camadas.
    """
    async def _analyze() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project
        from wxcode.analyzer import DependencyAnalyzer

        client = await init_db()

        # Busca projeto
        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado.[/]")
            await close_db(client)
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Projeto:[/] {project}\n"
            f"[bold]Construir grafo:[/] {'Sim' if build_graph else 'Não'}\n"
            f"[bold]Persistir ordem:[/] {'Não' if no_persist else 'Sim'}",
            title="Análise de Dependências",
            border_style="blue",
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if build_graph:
                task = progress.add_task("Construindo grafo de dependências...", total=None)

                # Usa o DependencyAnalyzer
                analyzer = DependencyAnalyzer(proj.id)
                result = await analyzer.analyze(persist=not no_persist)

                progress.update(task, description="Análise concluída!")

                # Exporta DOT se solicitado
                if export_dot:
                    dot_content = analyzer.export_dot()
                    export_dot.write_text(dot_content)
                    console.print(f"\n[dim]Grafo DOT exportado para: {export_dot}[/]")

                # Exporta HTML interativo se solicitado
                if export_html:
                    from wxcode.analyzer.graph_exporter import export_to_html
                    export_to_html(analyzer.graph, str(export_html), f"Dependências - {project}")
                    console.print(f"[dim]Grafo HTML exportado para: {export_html}[/]")

            # Atualiza status do projeto
            from wxcode.models.project import ProjectStatus
            proj.status = ProjectStatus.ANALYZED
            await proj.save()

        await close_db(client)

        # Exibe resultado
        if build_graph:
            # Tabela de estatísticas
            table = Table(title="Resultado da Análise")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", justify="right", style="green")

            table.add_row("Total de nós", str(result.total_nodes))
            table.add_row("Total de arestas", str(result.total_edges))
            table.add_row("Ciclos detectados", str(len(result.cycles)))

            console.print(table)

            # Tabela de nós por tipo
            if result.nodes_by_type:
                nodes_table = Table(title="Nós por Tipo")
                nodes_table.add_column("Tipo", style="cyan")
                nodes_table.add_column("Quantidade", justify="right", style="green")

                for node_type, count in sorted(result.nodes_by_type.items()):
                    nodes_table.add_row(node_type, str(count))

                console.print(nodes_table)

            # Tabela de arestas por tipo
            if result.edges_by_type:
                edges_table = Table(title="Arestas por Tipo")
                edges_table.add_column("Tipo", style="cyan")
                edges_table.add_column("Quantidade", justify="right", style="green")

                for edge_type, count in sorted(result.edges_by_type.items()):
                    edges_table.add_row(edge_type, str(count))

                console.print(edges_table)

            # Exibe ciclos se houver
            if result.cycles:
                console.print("\n[yellow]Ciclos detectados:[/]")
                for i, cycle in enumerate(result.cycles[:5], 1):
                    cycle_path = " → ".join(cycle.nodes[:4])
                    if len(cycle.nodes) > 4:
                        cycle_path += " → ..."
                    console.print(f"  [yellow]{i}.[/] {cycle_path}")
                    console.print(f"      [dim]Sugestão de quebra: {cycle.suggested_break}[/]")
                if len(result.cycles) > 5:
                    console.print(f"  [dim]... e mais {len(result.cycles) - 5} ciclos[/]")
            else:
                console.print("\n[green]✓ Nenhum ciclo detectado[/]")

            # Estatísticas por camada
            if result.layer_stats:
                console.print("\n[bold]Ordem por camada:[/]")
                for stat in result.layer_stats:
                    console.print(
                        f"  [cyan]{stat.layer.value}:[/] {stat.count} elementos "
                        f"(posições {stat.order_start}-{stat.order_end})"
                    )

        console.print(Panel(
            f"[green]Análise concluída![/]\n\n"
            f"Projeto: [bold]{project}[/]",
            title="Análise Completa",
            border_style="green",
        ))

    asyncio.run(_analyze())


@app.command()
def plan(
    project: str = typer.Argument(..., help="Nome do projeto"),
    target: str = typer.Option(
        "fastapi-jinja2",
        "--target",
        "-t",
        help="Stack alvo para conversão",
    ),
) -> None:
    """
    Gera um plano de conversão para o projeto.

    Mostra a ordem de conversão e estimativas.
    """
    async def _plan() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project, Element

        client = await init_db()

        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado.[/]")
            await close_db(client)
            raise typer.Exit(1)

        elements = await Element.find(Element.project_id == proj.id).to_list()

        # Agrupa por camada
        layers = {}
        for elem in elements:
            layer = elem.layer or "unknown"
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(elem)

        await close_db(client)

        # Exibe plano
        table = Table(title=f"Plano de Conversão: {project} → {target}")
        table.add_column("Camada", style="cyan")
        table.add_column("Elementos", justify="right", style="green")
        table.add_column("Ordem", justify="center")

        order = ["schema", "domain", "business", "api", "ui", "unknown"]
        for i, layer in enumerate(order):
            count = len(layers.get(layer, []))
            if count > 0:
                table.add_row(layer.upper(), str(count), str(i + 1))

        console.print(table)

    asyncio.run(_plan())


@app.command()
def convert(
    project: str = typer.Argument(..., help="Nome do projeto"),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Configuration específica para converter (ex: Producao, API_Homolog)",
    ),
    all_configs: bool = typer.Option(
        False,
        "--all-configs",
        help="Converter todas as configurations do projeto",
    ),
    output: Path = typer.Option(
        Path("./output/generated"),
        "--output",
        "-o",
        help="Diretório base de saída (configurations criam subpastas)",
    ),
    elements: Optional[list[str]] = typer.Option(
        None,
        "--element",
        "-e",
        help="Elementos específicos para converter (pode usar wildcards como PAGE_*). Pode ser repetido.",
    ),
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-P",
        help="LLM provider (anthropic, openai, ollama)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo específico (usa default do provider se não fornecido)",
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        "-t",
        help="Tema Bootstrap para geração (ex: dashlite). Use 'themes list' para ver disponíveis.",
    ),
    deploy_assets: bool = typer.Option(
        False,
        "--deploy-assets",
        help="Copia assets do tema (CSS, JS, fonts, images). Requer --theme.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Não escreve arquivos, apenas mostra o que seria gerado",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Exibe detalhes do contexto e resposta do LLM",
    ),
    layer: str = typer.Option(
        "route",
        "--layer",
        "-l",
        help="Camada: schema, domain, service, route, api, template, ou all",
    ),
) -> None:
    """
    Converte um projeto para FastAPI + Jinja2 usando LLM.

    Usa LLM para gerar código de alta qualidade baseado em tema.
    Gera estrutura base + converte cada página/procedure com inteligência.

    Exemplos:
      wxcode convert Linkpay_ADM --theme dashlite          # Com tema
      wxcode convert Linkpay_ADM -e PAGE_Login             # Só PAGE_Login
      wxcode convert Linkpay_ADM -e "PAGE_*" --theme tabler  # Wildcards
      wxcode convert Linkpay_ADM --provider openai         # Usar OpenAI
      wxcode convert Linkpay_ADM --dry-run                 # Preview
      wxcode convert Linkpay_ADM --layer service           # Só services
      wxcode convert Linkpay_ADM --layer all               # Tudo
    """
    # Validar que --deploy-assets requer --theme
    if deploy_assets and not theme:
        console.print("[red]Erro: --deploy-assets requer --theme[/]")
        console.print("[dim]Exemplo: wxcode convert Linkpay_ADM --theme dashlite --deploy-assets[/]")
        raise typer.Exit(1)

    # Validar layer
    valid_layers = ("schema", "domain", "service", "route", "api", "template", "all")
    if layer not in valid_layers:
        console.print(f"[red]Erro: --layer inválido. Use: {', '.join(valid_layers)}[/]")
        raise typer.Exit(1)

    async def _convert() -> None:
        import fnmatch
        from wxcode.config import get_settings
        from wxcode.database import init_db, close_db
        from wxcode.models import Project
        from wxcode.llm_converter import PageConverter, ProcedureConverter, ConversionError
        from wxcode.llm_converter.providers import create_provider
        from wxcode.generator import StarterKitGenerator

        settings = get_settings()

        # Conecta ao banco
        client = await init_db()
        db = client[settings.mongodb_database]

        # Busca projeto no MongoDB
        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado no MongoDB.[/]")
            console.print("[dim]Execute 'wxcode import' primeiro.[/]")
            await close_db(client)
            raise typer.Exit(1)

        # Determina configuration a usar
        config_name = config
        if not config_name and proj.configurations:
            config_name = proj.configurations[0].name
            console.print(f"[dim]Usando configuration padrão: {config_name}[/]")

        # Determina output dir
        if config_name:
            if output.name.lower() == config_name.lower():
                config_output = output
            else:
                config_output = output / config_name
        else:
            config_output = output

        # Info panel
        model_display = model or "(default)"
        theme_display = theme or "(nenhum)"

        layer_display = {
            "schema": "schemas (Pydantic models)",
            "domain": "classes de domínio",
            "service": "services",
            "route": "páginas",
            "api": "APIs REST",
            "template": "templates Jinja2",
            "all": "todas as camadas",
        }[layer]
        console.print(Panel(
            f"[bold]Projeto:[/] {project}\n"
            f"[bold]Configuration:[/] {config_name or 'N/A'}\n"
            f"[bold]Provider:[/] {provider}\n"
            f"[bold]Modelo:[/] {model_display}\n"
            f"[bold]Tema:[/] {theme_display}\n"
            f"[bold]Camada:[/] {layer_display}\n"
            f"[bold]Saída:[/] {config_output}\n"
            f"[bold]Dry run:[/] {'Sim' if dry_run else 'Não'}",
            title="Conversão com LLM",
            border_style="blue",
        ))

        # Deploy assets do tema se solicitado
        if deploy_assets and theme:
            from wxcode.generator.theme_deployer import deploy_theme_assets, get_theme_path

            theme_path = get_theme_path(theme)
            if theme_path is None:
                console.print(f"[red]Tema '{theme}' não encontrado.[/]")
                await close_db(client)
                raise typer.Exit(1)

            console.print(f"[dim]Copiando assets do tema {theme}...[/]")
            deploy_result = deploy_theme_assets(theme=theme, output_dir=config_output)

            if deploy_result.success:
                console.print(
                    f"[green]✓[/] {deploy_result.stats.total} assets copiados "
                    f"({deploy_result.stats.css_count} CSS, {deploy_result.stats.js_count} JS)"
                )
            else:
                console.print(f"[yellow]Aviso: Falha ao copiar alguns assets[/]")

        # 1. Gerar estrutura base do projeto (config, database, main.py, etc.)
        if not dry_run:
            console.print("\n[cyan]1. Gerando estrutura base do projeto...[/]")
            from wxcode.generator.starter_kit import StarterKitConfig
            from wxcode.models.schema import DatabaseSchema

            # Carrega connections do projeto (se existirem)
            db_schema = await DatabaseSchema.find_one(
                DatabaseSchema.project_id == proj.id
            )
            connections = db_schema.connections if db_schema else []

            starter_config = StarterKitConfig(
                project_name=config_name or project,
                connections=connections,
                use_mongodb=False,  # Usa SQLAlchemy para SQL Server
                include_auth=True,
                include_docker=True,
            )
            starter_generator = StarterKitGenerator(config_output, starter_config)
            starter_generator.generate()
            console.print(f"[green]✓ Estrutura base gerada ({len(connections)} conexões)[/]")

        # Criar provider LLM (compartilhado)
        try:
            llm_provider = create_provider(provider, model=model)
        except ValueError as e:
            console.print(f"[red]Erro ao criar provider: {e}[/]")
            await close_db(client)
            raise typer.Exit(1)

        results = []
        service_results = []
        total_tokens_input = 0
        total_tokens_output = 0
        total_cost = 0.0
        step = 2

        # 2. Converter camadas não-LLM via orchestrator (schema, domain, api, template)
        non_llm_layers = ("schema", "domain", "api", "template")
        if layer in non_llm_layers or layer == "all":
            from wxcode.generator import GeneratorOrchestrator

            layers_to_generate = [layer] if layer in non_llm_layers else list(non_llm_layers)

            for gen_layer in layers_to_generate:
                console.print(f"\n[cyan]{step}. Gerando {gen_layer}...[/]")
                step += 1

                try:
                    orchestrator = GeneratorOrchestrator(str(proj.id), config_output, None, "python")
                    files = await orchestrator.generate_layer(gen_layer)
                    console.print(f"[green]✓ {len(files)} arquivos gerados[/]")
                    if dry_run:
                        for f in files[:5]:
                            console.print(f"  [dim]{f}[/]")
                        if len(files) > 5:
                            console.print(f"  [dim]... e mais {len(files) - 5} arquivos[/]")
                except Exception as e:
                    console.print(f"[red]✗ Erro: {e}[/]")

            # Se só estamos gerando camadas não-LLM, podemos sair mais cedo
            if layer in non_llm_layers:
                await close_db(client)
                return

        # 3. Converter páginas (se layer == "route" ou "all")
        if layer in ("route", "all"):
            console.print(f"\n[cyan]{step}. Buscando páginas para converter...[/]")
            step += 1

            # Monta query para buscar elementos (source_type=page)
            base_query = {"source_type": "page"}

            # Filtra por elementos específicos se fornecido
            if elements:
                # Suporta wildcards como PAGE_*
                all_pages = await db.elements.find(base_query).to_list(length=None)
                filtered_pages = []
                for page in all_pages:
                    page_name = page.get("source_name", "")
                    for pattern in elements:
                        if fnmatch.fnmatch(page_name, pattern):
                            filtered_pages.append(page)
                            break
                pages = filtered_pages
            else:
                pages = await db.elements.find(base_query).to_list(length=None)

            if pages:
                console.print(f"[green]✓ {len(pages)} páginas encontradas[/]")

                console.print(f"\n[cyan]{step}. Convertendo páginas com {provider}...[/]")
                step += 1

                converter = PageConverter(
                    db,
                    config_output,
                    llm_provider=llm_provider,
                    theme=theme,
                    project_root=Path.cwd(),
                )

                for i, page in enumerate(pages, 1):
                    page_name = page.get("source_name", "unknown")
                    console.print(f"  [{i}/{len(pages)}] {page_name}...", end=" ")

                    try:
                        result = await converter.convert(page["_id"], dry_run=dry_run)
                        results.append((page_name, result, None))
                        total_tokens_input += result.tokens_used.get("input", 0)
                        total_tokens_output += result.tokens_used.get("output", 0)
                        total_cost += result.cost_usd
                        console.print(f"[green]✓[/] ({result.duration_seconds:.1f}s, ${result.cost_usd:.4f})")
                    except ConversionError as e:
                        results.append((page_name, None, str(e)))
                        console.print(f"[red]✗ {e}[/]")
                    except Exception as e:
                        results.append((page_name, None, str(e)))
                        console.print(f"[red]✗ {e}[/]")
            else:
                console.print("[yellow]Nenhuma página encontrada para converter.[/]")

        # 4. Converter procedure groups (se layer == "service" ou "all")
        if layer in ("service", "all"):
            console.print(f"\n[cyan]{step}. Buscando procedure groups para converter...[/]")
            step += 1

            # Monta query para buscar procedure groups
            base_query = {"source_type": "procedure_group"}

            # Filtra por elementos específicos se fornecido
            if elements:
                all_groups = await db.elements.find(base_query).to_list(length=None)
                filtered_groups = []
                for group in all_groups:
                    group_name = group.get("source_name", "").replace(".wdg", "")
                    for pattern in elements:
                        if fnmatch.fnmatch(group_name, pattern) or fnmatch.fnmatch(group_name + ".wdg", pattern):
                            filtered_groups.append(group)
                            break
                groups = filtered_groups
            else:
                groups = await db.elements.find(base_query).to_list(length=None)

            if groups:
                console.print(f"[green]✓ {len(groups)} procedure groups encontrados[/]")

                console.print(f"\n[cyan]{step}. Convertendo services com {provider}...[/]")
                step += 1

                proc_converter = ProcedureConverter(
                    db,
                    config_output,
                    llm_provider=llm_provider,
                )

                for i, group in enumerate(groups, 1):
                    group_name = group.get("source_name", "unknown").replace(".wdg", "")
                    console.print(f"  [{i}/{len(groups)}] {group_name}...", end=" ")

                    try:
                        result = await proc_converter.convert(group["_id"], dry_run=dry_run)
                        service_results.append((group_name, result, None))
                        total_tokens_input += result.tokens_used.get("input", 0)
                        total_tokens_output += result.tokens_used.get("output", 0)
                        total_cost += result.cost_usd
                        console.print(f"[green]✓[/] ({result.duration_seconds:.1f}s, ${result.cost_usd:.4f})")
                    except ConversionError as e:
                        service_results.append((group_name, None, str(e)))
                        console.print(f"[red]✗ {e}[/]")
                    except Exception as e:
                        service_results.append((group_name, None, str(e)))
                        console.print(f"[red]✗ {e}[/]")
            else:
                console.print("[yellow]Nenhum procedure group encontrado para converter.[/]")

        await close_db(client)

        # 4. Resumo final
        console.print("\n")
        table = Table(title="Resumo da Conversão")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        page_success = sum(1 for _, r, e in results if r is not None)
        page_errors = sum(1 for _, r, e in results if e is not None)
        service_success = sum(1 for _, r, e in service_results if r is not None)
        service_errors = sum(1 for _, r, e in service_results if e is not None)

        if layer in ("route", "all") and results:
            table.add_row("Páginas convertidas", f"{page_success}/{len(results)}")
        if layer in ("service", "all") and service_results:
            table.add_row("Services convertidos", f"{service_success}/{len(service_results)}")
        table.add_row("Erros totais", str(page_errors + service_errors))
        table.add_row("Tokens (input)", f"{total_tokens_input:,}")
        table.add_row("Tokens (output)", f"{total_tokens_output:,}")
        table.add_row("Custo total", f"${total_cost:.4f}")
        table.add_row("Saída", str(config_output))

        console.print(table)

        if page_errors > 0:
            console.print("\n[yellow]Páginas com erro:[/]")
            for name, _, error in results:
                if error:
                    console.print(f"  [red]•[/] {name}: {error}")

        if service_errors > 0:
            console.print("\n[yellow]Services com erro:[/]")
            for name, _, error in service_results:
                if error:
                    console.print(f"  [red]•[/] {name}: {error}")

        total_success = page_success + service_success
        if total_success > 0:
            console.print(f"\n[green]✓ Conversão concluída![/]")
            console.print(f"[dim]Execute: cd {config_output} && ./run.sh (ou run.bat no Windows)[/]")

    asyncio.run(_convert())


@app.command()
def validate(
    project: str = typer.Argument(..., help="Nome do projeto"),
    generate_tests: bool = typer.Option(
        False,
        "--generate-tests",
        help="Gerar testes automaticamente",
    ),
) -> None:
    """
    Valida o código convertido.

    Verifica sintaxe e opcionalmente gera testes.
    """
    console.print(f"[yellow]Validando projeto '{project}'[/]")
    if generate_tests:
        console.print("[yellow]Gerando testes...[/]")
    console.print("[dim]TODO: Implementar validação[/]")


@app.command()
def export(
    project: str = typer.Argument(..., help="Nome do projeto"),
    output: Path = typer.Option(
        Path("./output/exported"),
        "--output",
        "-o",
        help="Diretório de saída",
    ),
    include_docker: bool = typer.Option(
        True,
        "--docker/--no-docker",
        help="Incluir arquivos Docker (Dockerfile, docker-compose.yml)",
    ),
) -> None:
    """
    Exporta o projeto convertido para o sistema de arquivos.

    Gera um projeto FastAPI + Jinja2 completo e pronto para execução.
    Inclui Dockerfile e docker-compose.yml por padrão.
    """
    async def _export() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project
        from wxcode.generator import GeneratorOrchestrator

        # Conecta ao banco
        client = await init_db()

        # Busca projeto no MongoDB
        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado no MongoDB.[/]")
            console.print("[dim]Execute 'wxcode import' primeiro.[/]")
            await close_db(client)
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Projeto:[/] {project}\n"
            f"[bold]Saída:[/] {output}\n"
            f"[bold]Docker:[/] {'Sim' if include_docker else 'Não'}",
            title="Exportação de Projeto",
            border_style="blue",
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Gerando projeto...", total=None)

            orchestrator = GeneratorOrchestrator(str(proj.id), output, None, "python")
            result = await orchestrator.generate_all()

            progress.update(task, description="Concluído!")

        await close_db(client)

        # Exibe resultado
        if result.success:
            console.print(f"\n[green]Projeto exportado com sucesso![/]")
            console.print(f"Total de arquivos: {result.total_files}")
            console.print(f"\n[bold]Para executar:[/]")
            console.print(f"  cd {output}")
            console.print(f"  pip install .")
            console.print(f"  uvicorn app.main:app --reload")

            if include_docker:
                console.print(f"\n[bold]Ou com Docker:[/]")
                console.print(f"  docker-compose up --build")
        else:
            console.print(f"\n[red]Exportação com erros:[/]")
            for error in result.errors:
                console.print(f"  [red]•[/] {error}")

    asyncio.run(_export())


@app.command()
def list_projects() -> None:
    """
    Lista todos os projetos importados.
    """
    async def _list() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project

        client = await init_db()
        projects = await Project.find_all().to_list()
        await close_db(client)

        if not projects:
            console.print("[yellow]Nenhum projeto importado.[/]")
            return

        table = Table(title="Projetos Importados")
        table.add_column("Nome", style="cyan")
        table.add_column("Versão", justify="center")
        table.add_column("Elementos", justify="right")
        table.add_column("Status", style="green")
        table.add_column("Importado em")

        for proj in projects:
            table.add_row(
                proj.name,
                f"{proj.major_version}.{proj.minor_version}",
                str(proj.total_elements),
                proj.status.value,
                proj.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

    asyncio.run(_list())


@app.command()
def status(
    project: str = typer.Argument(..., help="Nome do projeto"),
) -> None:
    """
    Exibe o status de conversão de um projeto.
    """
    async def _status() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project, Element, Conversion

        client = await init_db()

        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado.[/]")
            await close_db(client)
            raise typer.Exit(1)

        # Busca conversão ativa
        conversion = await Conversion.find_one(
            Conversion.project_id == proj.id
        )

        # Conta elementos por status
        elements = await Element.find(Element.project_id == proj.id).to_list()

        status_counts = {}
        for elem in elements:
            status = elem.conversion.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        await close_db(client)

        # Exibe status
        console.print(Panel(
            f"Projeto: [bold]{proj.name}[/]\n"
            f"Status: [bold]{proj.status.value}[/]\n"
            f"Total de elementos: [bold]{len(elements)}[/]",
            title="Status do Projeto",
            border_style="blue",
        ))

        if status_counts:
            table = Table(title="Status de Conversão")
            table.add_column("Status", style="cyan")
            table.add_column("Quantidade", justify="right")

            for status, count in sorted(status_counts.items()):
                table.add_row(status, str(count))

            console.print(table)

    asyncio.run(_status())


@app.command("split-pdf")
def split_pdf(
    pdf_path: Path = typer.Argument(
        ...,
        help="Caminho do PDF de documentação",
        exists=True,
        readable=True,
    ),
    output: Path = typer.Option(
        Path("./output/pdf_docs"),
        "--output",
        "-o",
        help="Diretório de saída",
    ),
    batch_size: int = typer.Option(
        50,
        "--batch-size",
        "-b",
        help="Número de páginas por batch",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-P",
        help="Nome do projeto no MongoDB. Se fornecido, usa nomes de elementos conhecidos para detectar PDFs.",
    ),
) -> None:
    """
    Divide PDF de documentação em elementos individuais.

    Processa PDFs grandes (3000+ páginas) em batches e extrai cada
    elemento (Page, Report, Window) para um PDF individual.

    Se --project for especificado, busca os nomes dos elementos no MongoDB
    para detectar elementos com prefixos não-padrão (ex: ESPELHO_, LISTAGEM_).
    """
    async def _split() -> dict:
        from wxcode.parser.pdf_doc_splitter import split_documentation_pdf

        known_elements: Optional[dict[str, str]] = None

        # Se projeto foi especificado, busca elementos do MongoDB
        if project:
            from wxcode.database import init_db, close_db
            from wxcode.models import Project, Element

            client = await init_db()

            proj = await Project.find_one(Project.name == project)
            if not proj:
                console.print(f"[red]Projeto '{project}' não encontrado no MongoDB.[/]")
                console.print("[dim]Execute 'wxcode import' primeiro.[/]")
                await close_db(client)
                raise typer.Exit(1)

            # Busca todos os elementos do projeto
            elements = await Element.find({"project_id.$id": proj.id}).to_list()

            # Cria dict de elementos conhecidos {nome: source_type}
            known_elements = {
                elem.source_name: elem.source_type.value
                for elem in elements
                if elem.source_name
            }

            await close_db(client)

            console.print(f"[dim]Carregados {len(known_elements)} elementos do projeto '{project}'[/]")

        def on_progress(done: int, total: int) -> None:
            percent = (done / total) * 100
            console.print(f"\r[dim]Processando: {done}/{total} páginas ({percent:.1f}%)[/]", end="")

        project_info = f"\n[bold]Projeto:[/] {project}" if project else ""
        console.print(Panel(
            f"[bold]PDF:[/] {pdf_path}\n"
            f"[bold]Saída:[/] {output}\n"
            f"[bold]Batch size:[/] {batch_size}{project_info}",
            title="PDF Documentation Splitter",
            border_style="blue",
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processando PDF...", total=None)

            result = split_documentation_pdf(
                pdf_path=pdf_path,
                output_dir=output,
                batch_size=batch_size,
                on_progress=on_progress,
                known_elements=known_elements
            )

            progress.update(task, description="Concluído!")

        return result

    result = asyncio.run(_split())

    console.print("")  # Nova linha após progress

    # Exibe resultado
    table = Table(title="Resultado da Extração")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", justify="right", style="green")

    table.add_row("Total de páginas", str(result['total_pages']))
    table.add_row("Elementos encontrados", str(result['stats']['total_elements']))
    table.add_row("Páginas extraídas", str(result['stats']['pages']))
    table.add_row("Relatórios extraídos", str(result['stats']['reports']))
    table.add_row("Janelas extraídas", str(result['stats']['windows']))
    table.add_row("Tempo de processamento", f"{result['stats']['processing_time_seconds']}s")

    if result['stats']['errors']:
        table.add_row("Erros", str(len(result['stats']['errors'])))

    console.print(table)

    # Exibe erros se houver
    if result['stats']['errors']:
        console.print("\n[yellow]Erros encontrados:[/]")
        for error in result['stats']['errors'][:5]:  # Mostra apenas os 5 primeiros
            console.print(f"  [red]•[/] {error['element']}: {error['error']}")
        if len(result['stats']['errors']) > 5:
            console.print(f"  [dim]... e mais {len(result['stats']['errors']) - 5} erros[/]")

    console.print(f"\n[green]Manifest salvo em:[/] {output}/manifest.json")


def _find_project_file(directory: Path) -> Optional[Path]:
    """Encontra arquivo de projeto (.wwp/.wdp/.wpp) no diretório."""
    for ext in ['.wwp', '.wdp', '.wpp']:
        files = list(directory.glob(f'*{ext}'))
        if files:
            return files[0]
    return None


def _extract_project_name(project_file: Path) -> Optional[str]:
    """Extrai o nome do projeto do arquivo .wwp/.wdp/.wpp."""
    try:
        with open(project_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('name :'):
                    # Formato: name : "NomeProjeto" ou name : NomeProjeto
                    name = line.split(':', 1)[1].strip()
                    # Remove aspas se existirem
                    if name.startswith('"') and name.endswith('"'):
                        name = name[1:-1]
                    return name
    except Exception:
        pass
    return None


@app.command()
def enrich(
    project_dir: Path = typer.Argument(
        ...,
        help="Diretório do projeto WinDev/WebDev",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    pdf_docs: Path = typer.Option(
        Path("./output/pdf_docs"),
        "--pdf-docs",
        "-p",
        help="Diretório com PDFs splitados",
    ),
    screenshots_dir: Optional[Path] = typer.Option(
        None,
        "--screenshots",
        "-s",
        help="Diretório para salvar screenshots extraídos",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-P",
        help="Nome do projeto no MongoDB (sobrescreve detecção automática)",
    ),
) -> None:
    """
    Enriquece elementos do projeto com dados dos PDFs e arquivos fonte.

    Extrai controles, hierarquia, eventos e propriedades visuais,
    salvando tudo no MongoDB.

    O nome do projeto é extraído automaticamente do arquivo .wwp/.wdp/.wpp
    encontrado no diretório especificado.
    """
    async def _enrich() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project
        from wxcode.parser.element_enricher import ElementEnricher

        # Encontra arquivo de projeto
        project_file = _find_project_file(project_dir)
        if not project_file:
            console.print(f"[red]Nenhum arquivo de projeto (.wwp/.wdp/.wpp) encontrado em {project_dir}[/]")
            raise typer.Exit(1)

        # Extrai nome do projeto (ou usa o fornecido via --project)
        if project:
            project_name = project
            console.print(f"[dim]Projeto: {project_name} (fornecido via --project)[/]")
        else:
            project_name = _extract_project_name(project_file)
            if not project_name:
                console.print(f"[red]Não foi possível extrair o nome do projeto de {project_file.name}[/]")
                raise typer.Exit(1)
            console.print(f"[dim]Projeto detectado: {project_name} ({project_file.name})[/]")

        # Conecta ao banco
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando ao MongoDB...", total=None)
            client = await init_db()
            progress.update(task, description="Conectado ao MongoDB")

        # Busca projeto no MongoDB
        proj = await Project.find_one(Project.name == project_name)
        if not proj:
            console.print(f"[red]Projeto '{project_name}' não encontrado no MongoDB.[/]")
            console.print("[dim]Execute 'wxcode import' primeiro para importar o projeto.[/]")
            await close_db(client)
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Projeto:[/] {project_name}\n"
            f"[bold]PDF docs:[/] {pdf_docs}\n"
            f"[bold]Projeto dir:[/] {project_dir}\n"
            f"[bold]Screenshots:[/] {screenshots_dir or 'Não extrair'}",
            title="Enriquecimento de Elementos",
            border_style="blue",
        ))

        # Callback de progresso
        import sys
        is_interactive = sys.stdout.isatty()  # Detecta se está em terminal interativo

        current_element = [""]
        def on_progress(element_name: str, current: int, total: int) -> None:
            current_element[0] = element_name
            percent = (current / total) * 100 if total else 0

            if is_interactive:
                # Terminal interativo: sobrescreve a mesma linha
                console.print(
                    f"\r[dim]Processando: {current}/{total} ({percent:.1f}%) - {element_name}[/]",
                    end=""
                )
            else:
                # Subprocess/pipe: imprime para stdout a cada elemento (WebSocket precisa dos logs)
                print(f"[INFO] Processando: {current}/{total} ({percent:.1f}%) - {element_name}", flush=True)

        # Enriquece
        enricher = ElementEnricher(
            pdf_docs_dir=pdf_docs,
            project_dir=project_dir,
            screenshots_dir=screenshots_dir,
            on_progress=on_progress
        )

        if is_interactive:
            console.print("[dim]Iniciando enriquecimento de páginas/windows...[/]")
        else:
            print("[INFO] Iniciando enriquecimento de páginas/windows...", flush=True)
        stats = await enricher.enrich_project(proj.id)

        if is_interactive:
            console.print("")  # Nova linha

        # Enriquece queries
        if is_interactive:
            console.print("[dim]Iniciando enriquecimento de queries...[/]")
        else:
            print("[INFO] Iniciando enriquecimento de queries...", flush=True)
        from wxcode.parser.query_enricher import QueryEnricher

        query_enricher = QueryEnricher(proj.id, pdf_docs)
        query_stats = await query_enricher.enrich_all()

        if is_interactive:
            console.print("")  # Nova linha
        else:
            print(f"[INFO] Enriquecimento concluído! {stats.elements_processed} elementos processados, {stats.total_controls} controles extraídos", flush=True)

        # Fecha conexão
        await close_db(client)

        # Exibe resultado
        table = Table(title="Resultado do Enriquecimento")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        table.add_row("Elementos processados", str(stats.elements_processed))
        table.add_row("Elementos ignorados", str(stats.elements_skipped))
        table.add_row("Elementos com erros", str(stats.elements_with_errors))
        table.add_row("Total de controles", str(stats.total_controls))
        table.add_row("Tipos descobertos", str(stats.total_types))
        table.add_row("Controles órfãos", str(stats.total_orphans))
        table.add_row("Procedures locais", str(stats.total_local_procedures))
        table.add_row("Dependências extraídas", str(stats.total_dependencies))
        table.add_row("─" * 25, "─" * 10)  # Separator
        table.add_row("Queries enriquecidas", str(query_stats['enriched']))
        table.add_row("Queries sem PDF", str(query_stats['pdf_not_found']))
        table.add_row("Queries sem SQL", str(query_stats['sql_not_found']))
        table.add_row("─" * 25, "─" * 10)  # Separator
        table.add_row("Tempo", f"{stats.duration_seconds:.2f}s")

        console.print(table)

        # Exibe erros se houver
        if stats.errors:
            console.print("\n[yellow]Erros encontrados:[/]")
            for error in stats.errors[:10]:
                console.print(f"  [red]•[/] {error}")
            if len(stats.errors) > 10:
                console.print(f"  [dim]... e mais {len(stats.errors) - 10} erros[/]")

        # Exibe detalhes por elemento
        if stats.results:
            console.print("\n[bold]Detalhes por elemento:[/]")
            for result in stats.results[:15]:
                status = "[green]✓[/]" if not result.errors else "[yellow]![/]"
                orphan_info = f" [dim]({result.orphan_controls} órfãos)[/]" if result.orphan_controls else ""
                procs_info = f" [cyan]+{result.local_procedures_created} procs[/]" if result.local_procedures_created else ""
                console.print(
                    f"  {status} {result.element_name}: "
                    f"{result.controls_created} criados, "
                    f"{result.controls_updated} atualizados"
                    f"{procs_info}"
                    f"{orphan_info}"
                )
            if len(stats.results) > 15:
                console.print(f"  [dim]... e mais {len(stats.results) - 15} elementos[/]")

    asyncio.run(_enrich())


@app.command("parse-procedures")
def parse_procedures(
    project_dir: Path = typer.Argument(
        ...,
        help="Diretório do projeto WinDev/WebDev",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-P",
        help="Nome do projeto no MongoDB (sobrescreve detecção automática)",
    ),
) -> None:
    """
    Parseia procedures de arquivos .wdg e armazena no MongoDB.

    Extrai:
    - Nome, parâmetros e tipo de retorno
    - Código WLanguage completo
    - Dependências (procedures chamadas, arquivos HyperFile, APIs)
    """
    async def _parse_procedures() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project, Element, ElementType
        from wxcode.models.procedure import Procedure, ProcedureParameter, ProcedureDependencies
        from wxcode.parser.wdg_parser import parse_wdg_file

        # Encontra arquivo de projeto
        project_file = _find_project_file(project_dir)
        if not project_file:
            console.print(f"[red]Nenhum arquivo de projeto (.wwp/.wdp/.wpp) encontrado em {project_dir}[/]")
            raise typer.Exit(1)

        # Extrai nome do projeto (ou usa o fornecido via --project)
        if project:
            project_name = project
            console.print(f"[dim]Projeto: {project_name} (fornecido via --project)[/]")
        else:
            project_name = _extract_project_name(project_file)
            if not project_name:
                console.print(f"[red]Não foi possível extrair o nome do projeto de {project_file.name}[/]")
                raise typer.Exit(1)
            console.print(f"[dim]Projeto detectado: {project_name} ({project_file.name})[/]")

        # Conecta ao banco
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando ao MongoDB...", total=None)
            client = await init_db()
            progress.update(task, description="Conectado ao MongoDB")

        # Busca projeto no MongoDB
        proj = await Project.find_one(Project.name == project_name)
        if not proj:
            console.print(f"[red]Projeto '{project_name}' não encontrado no MongoDB.[/]")
            console.print("[dim]Execute 'wxcode import' primeiro para importar o projeto.[/]")
            await close_db(client)
            raise typer.Exit(1)

        # Busca elementos .wdg (usa sintaxe DBRef para project_id)
        wdg_elements = await Element.find({
            "project_id.$id": proj.id,
            "source_type": ElementType.PROCEDURE_GROUP.value
        }).to_list()

        if not wdg_elements:
            console.print("[yellow]Nenhum arquivo .wdg encontrado no projeto.[/]")
            await close_db(client)
            return

        console.print(Panel(
            f"[bold]Projeto:[/] {project_name}\n"
            f"[bold]Arquivos .wdg:[/] {len(wdg_elements)}",
            title="Parsing de Procedures",
            border_style="blue",
        ))

        # Estatísticas
        total_files = 0
        total_procedures = 0
        total_lines = 0
        errors = []

        # Detecta se está em terminal interativo
        import sys
        is_interactive = sys.stdout.isatty()

        # Processa cada arquivo
        for i, element in enumerate(wdg_elements, 1):
            # Normaliza caminho (remove .\ do Windows e converte barras)
            source_file = element.source_file.lstrip('.\\').lstrip('./').replace('\\', '/')
            wdg_path = project_dir / source_file

            if is_interactive:
                console.print(
                    f"\r[dim]Processando: {i}/{len(wdg_elements)} - {element.source_name}[/]",
                    end=""
                )
            else:
                if i % 5 == 0 or i == len(wdg_elements):
                    print(f"[INFO] Parseando procedures: {i}/{len(wdg_elements)} - {element.source_name}", flush=True)

            if not wdg_path.exists():
                errors.append(f"{element.source_name}: arquivo não encontrado")
                continue

            try:
                # Parseia o arquivo
                result = parse_wdg_file(wdg_path)

                # Remove procedures antigas do elemento
                await Procedure.find(
                    Procedure.element_id == element.id
                ).delete()

                # Salva novas procedures
                for proc in result.procedures:
                    procedure = Procedure(
                        element_id=element.id,
                        project_id=proj.id,
                        name=proc.name,
                        procedure_id=proc.procedure_id,
                        type_code=proc.type_code,
                        windev_type=proc.windev_type,
                        internal_properties=proc.internal_properties,
                        parameters=[
                            ProcedureParameter(
                                name=p.name,
                                type=p.type,
                                is_local=p.is_local,
                                default_value=p.default_value
                            )
                            for p in proc.parameters
                        ],
                        return_type=proc.return_type,
                        code=proc.code,
                        code_lines=proc.code_lines,
                        dependencies=ProcedureDependencies(
                            calls_procedures=proc.dependencies.calls_procedures,
                            uses_files=proc.dependencies.uses_files,
                            uses_apis=proc.dependencies.uses_apis,
                            uses_queries=proc.dependencies.uses_queries
                        ),
                        has_documentation=proc.has_documentation,
                        is_public=proc.is_public,
                        is_internal=proc.is_internal,
                        has_error_handling=proc.has_error_handling
                    )
                    await procedure.insert()

                # Atualiza o campo ast do Element com resumo das procedures
                from wxcode.models.element import ElementAST
                if element.ast is None:
                    element.ast = ElementAST()

                element.ast.procedures = [
                    {
                        "name": proc.name,
                        "parameters": [{"name": p.name, "type": p.type} for p in proc.parameters],
                        "return_type": proc.return_type,
                        "code_lines": proc.code_lines,
                        "has_error_handling": proc.has_error_handling,
                    }
                    for proc in result.procedures
                ]
                await element.save()

                total_files += 1
                total_procedures += result.total_procedures
                total_lines += result.total_code_lines

            except Exception as e:
                errors.append(f"{element.source_name}: {str(e)}")

        console.print("")  # Nova linha

        # Fecha conexão
        await close_db(client)

        # Exibe resultado
        table = Table(title="Resultado do Parsing de Procedures")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        table.add_row("Arquivos processados", str(total_files))
        table.add_row("Procedures extraídas", str(total_procedures))
        table.add_row("Linhas de código", f"{total_lines:,}")
        table.add_row("Erros", str(len(errors)))

        console.print(table)

        # Exibe erros se houver
        if errors:
            console.print("\n[yellow]Erros encontrados:[/]")
            for error in errors[:10]:
                console.print(f"  [red]•[/] {error}")
            if len(errors) > 10:
                console.print(f"  [dim]... e mais {len(errors) - 10} erros[/]")

    asyncio.run(_parse_procedures())


@app.command("parse-classes")
def parse_classes(
    project_dir: Path = typer.Argument(
        ...,
        help="Diretório do projeto WinDev/WebDev",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-P",
        help="Nome do projeto no MongoDB (sobrescreve detecção automática)",
    ),
) -> None:
    """
    Parseia as classes (arquivos .wdc) do projeto.

    Extrai estrutura completa: herança, membros, métodos, constantes
    e armazena no MongoDB para uso na conversão.
    """
    async def _parse_classes() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project, Element, ClassDefinition
        from wxcode.parser.wdc_parser import WdcParser

        # Encontra arquivo do projeto
        project_file = _find_project_file(project_dir)
        if not project_file:
            console.print("[red]Arquivo de projeto não encontrado (.wwp/.wdp/.wpp)[/]")
            raise typer.Exit(1)

        # Extrai nome do projeto (ou usa o fornecido via --project)
        if project:
            project_name = project
            console.print(f"[dim]Projeto: {project_name} (fornecido via --project)[/]")
        else:
            project_name = _extract_project_name(project_file)
            if not project_name:
                project_name = project_file.stem
            console.print(f"[dim]Projeto detectado: {project_name}[/]")

        # Conecta ao banco
        client = await init_db()

        # Busca projeto no MongoDB
        proj = await Project.find_one(Project.name == project_name)
        if not proj:
            console.print(f"[red]Projeto '{project_name}' não encontrado no MongoDB.[/]")
            console.print("[dim]Execute 'wxcode import' primeiro.[/]")
            await close_db(client)
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Projeto:[/] {project_name}\n"
            f"[bold]Diretório:[/] {project_dir}",
            title="Parsing de Classes",
            border_style="blue",
        ))

        # Encontra todos os arquivos .wdc
        wdc_files = list(project_dir.glob("*.wdc"))

        if not wdc_files:
            console.print("[yellow]Nenhum arquivo .wdc encontrado no projeto.[/]")
            await close_db(client)
            raise typer.Exit(0)

        # Detecta se está em terminal interativo
        import sys
        is_interactive = sys.stdout.isatty()

        # Parseia classes
        parsed_classes = []
        errors = []

        if is_interactive:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Parseando {len(wdc_files)} classes...", total=None
                )

                for wdc_file in wdc_files:
                    try:
                        parser = WdcParser(wdc_file)
                        parsed_class = parser.parse()
                        parsed_classes.append((wdc_file, parsed_class))
                    except Exception as e:
                        errors.append(f"{wdc_file.name}: {e}")

                progress.update(task, description="Salvando no MongoDB...")

                # Remove classes antigas (idempotente)
                await ClassDefinition.find(
                    ClassDefinition.project_id == proj.id
                ).delete()

                # Salva classes
                total_members = 0
                total_methods = 0
                total_code_lines = 0

                for wdc_file, parsed_class in parsed_classes:
                    # Busca Element correspondente
                    element = await Element.find_one(
                        Element.project_id == proj.id,
                        Element.source_file == wdc_file.name
                    )

                    if not element:
                        # Cria element se não existir
                        from wxcode.models import ElementType
                        element = Element(
                            project_id=proj.id,
                            source_type=ElementType.CLASS,
                            source_name=parsed_class.name,
                            source_file=wdc_file.name,
                            windev_type=4,
                        )
                        await element.insert()

                    # Converte para ClassDefinition
                    class_def = ClassDefinition(
                        project_id=proj.id,
                        element_id=element.id,
                        name=parsed_class.name,
                        identifier=parsed_class.identifier,
                        inherits_from=parsed_class.inherits_from,
                        is_abstract=parsed_class.is_abstract,
                        members=[
                            {
                                "name": m.name,
                                "type": m.type,
                                "visibility": m.visibility,
                                "default_value": m.default_value,
                                "serialize": m.serialize,
                            }
                            for m in parsed_class.members
                        ],
                        methods=[
                            {
                                "name": m.name,
                                "method_type": m.method_type,
                                "visibility": m.visibility,
                                "parameters": m.parameters,
                                "return_type": m.return_type,
                                "code": m.code,
                                "code_lines": m.code_lines,
                                "is_static": m.is_static,
                                "procedure_id": m.procedure_id,
                                "type_code": m.type_code,
                                "windev_type": m.windev_type,
                                "internal_properties": m.internal_properties,
                            }
                            for m in parsed_class.methods
                        ],
                        constants=[
                            {
                                "name": c.name,
                                "value": c.value,
                                "type": c.type,
                            }
                            for c in parsed_class.constants
                        ],
                        dependencies={
                            "uses_classes": parsed_class.dependencies.uses_classes,
                            "uses_files": parsed_class.dependencies.uses_files,
                            "calls_procedures": parsed_class.dependencies.calls_procedures,
                        },
                    )
                    await class_def.insert()

                    total_members += parsed_class.total_members
                    total_methods += parsed_class.total_methods
                    total_code_lines += parsed_class.total_code_lines

                progress.update(task, description="Concluído!")
        else:
            print(f"[INFO] Parseando {len(wdc_files)} classes...", flush=True)

            for i, wdc_file in enumerate(wdc_files, 1):
                try:
                    parser = WdcParser(wdc_file)
                    parsed_class = parser.parse()
                    parsed_classes.append((wdc_file, parsed_class))
                    print(f"[INFO] Classe parseada: {i}/{len(wdc_files)} - {wdc_file.name}", flush=True)
                except Exception as e:
                    errors.append(f"{wdc_file.name}: {e}")

            print("[INFO] Salvando no MongoDB...", flush=True)

            # Remove classes antigas (idempotente)
            await ClassDefinition.find(
                ClassDefinition.project_id == proj.id
            ).delete()

            # Salva classes
            total_members = 0
            total_methods = 0
            total_code_lines = 0

            for wdc_file, parsed_class in parsed_classes:
                # Busca Element correspondente
                element = await Element.find_one(
                    Element.project_id == proj.id,
                    Element.source_file == wdc_file.name
                )

                if not element:
                    # Cria element se não existir
                    from wxcode.models import ElementType
                    element = Element(
                        project_id=proj.id,
                        source_type=ElementType.CLASS,
                        source_name=parsed_class.name,
                        source_file=wdc_file.name,
                        windev_type=4,
                    )
                    await element.insert()

                # Converte para ClassDefinition
                class_def = ClassDefinition(
                    project_id=proj.id,
                    element_id=element.id,
                    name=parsed_class.name,
                    identifier=parsed_class.identifier,
                    inherits_from=parsed_class.inherits_from,
                    is_abstract=parsed_class.is_abstract,
                    members=[
                        {
                            "name": m.name,
                            "type": m.type,
                            "visibility": m.visibility,
                            "default_value": m.default_value,
                            "serialize": m.serialize,
                        }
                        for m in parsed_class.members
                    ],
                    methods=[
                        {
                            "name": m.name,
                            "method_type": m.method_type,
                            "visibility": m.visibility,
                            "parameters": m.parameters,
                            "return_type": m.return_type,
                            "code": m.code,
                            "code_lines": m.code_lines,
                            "is_static": m.is_static,
                            "procedure_id": m.procedure_id,
                            "type_code": m.type_code,
                            "windev_type": m.windev_type,
                            "internal_properties": m.internal_properties,
                        }
                        for m in parsed_class.methods
                    ],
                    constants=[
                        {
                            "name": c.name,
                            "value": c.value,
                            "type": c.type,
                        }
                        for c in parsed_class.constants
                    ],
                    dependencies={
                        "uses_classes": parsed_class.dependencies.uses_classes,
                        "uses_files": parsed_class.dependencies.uses_files,
                        "calls_procedures": parsed_class.dependencies.calls_procedures,
                    },
                )
                await class_def.insert()

                total_members += parsed_class.total_members
                total_methods += parsed_class.total_methods
                total_code_lines += parsed_class.total_code_lines

            print("[INFO] Concluído!", flush=True)

        # Exibe resultado
        table = Table(title="Resultado do Parsing de Classes")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        table.add_row("Classes", str(len(parsed_classes)))
        table.add_row("Membros", str(total_members))
        table.add_row("Métodos", str(total_methods))
        table.add_row("Linhas de código", str(total_code_lines))

        if errors:
            table.add_row("Erros", str(len(errors)), style="red")

        console.print(table)

        # Exibe erros se houver
        if errors:
            console.print("\n[red]Erros:[/]")
            for error in errors[:5]:
                console.print(f"  [red]•[/] {error}")
            if len(errors) > 5:
                console.print(f"  [dim]... e mais {len(errors) - 5} erros[/]")

        # Exibe árvore de herança
        if parsed_classes:
            console.print("\n[bold]Árvore de herança:[/]")

            # Agrupa por classe pai
            inheritance_map: dict[Optional[str], list[str]] = {}
            for _, parsed_class in parsed_classes:
                parent = parsed_class.inherits_from
                if parent not in inheritance_map:
                    inheritance_map[parent] = []
                inheritance_map[parent].append(parsed_class.name)

            # Exibe classes base (sem pai)
            if None in inheritance_map:
                for class_name in sorted(inheritance_map[None])[:5]:
                    abstract = " (abstract)" if any(
                        c.is_abstract for _, c in parsed_classes if c.name == class_name
                    ) else ""
                    console.print(f"  [cyan]•[/] {class_name}{abstract}")

                    # Exibe filhas
                    if class_name in inheritance_map:
                        for child in sorted(inheritance_map[class_name])[:3]:
                            console.print(f"      [dim]└─[/] {child}")
                        if len(inheritance_map[class_name]) > 3:
                            console.print(
                                f"      [dim]   ... e mais {len(inheritance_map[class_name]) - 3}[/]"
                            )

            # Exibe classes com pai
            for parent, children in sorted(
                [(k, v) for k, v in inheritance_map.items() if k is not None],
                key=lambda x: x[0]
            ):
                if parent not in [c.name for _, c in parsed_classes]:
                    # Classe pai não está no projeto (externa)
                    console.print(f"  [yellow]•[/] {parent} (externa)")
                    for child in sorted(children)[:3]:
                        console.print(f"      [dim]└─[/] {child}")
                    if len(children) > 3:
                        console.print(f"      [dim]   ... e mais {len(children) - 3}[/]")

        await close_db(client)

        console.print(f"\n[green]Classes salvas no MongoDB![/]")

    asyncio.run(_parse_classes())


@app.command("list-orphans")
def list_orphans(
    project: str = typer.Argument(..., help="Nome do projeto"),
    element: Optional[str] = typer.Option(
        None,
        "--element",
        "-e",
        help="Filtrar por nome do elemento (ex: FORM_CLIENTE)",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Caminho do arquivo (padrão: ./output/orphans.json ou .txt)",
    ),
    no_file: bool = typer.Option(
        False,
        "--no-file",
        help="Apenas imprime no console, não salva arquivo",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Formato de saída: json ou table (Markdown)",
    ),
) -> None:
    """
    Lista controles órfãos do projeto.

    Órfãos são controles que existem no arquivo .wwh/.wdw mas não foram
    encontrados no PDF de documentação correspondente.

    Formatos disponíveis:
      - json: JSON estruturado (padrão, salva em ./output/orphans.json)
      - table: Markdown com tabelas (salva em ./output/orphans.md)
    """
    import json

    async def _list_orphans() -> list[dict]:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project, Element, Control, ControlTypeDefinition

        client = await init_db()

        # Busca projeto
        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado.[/]")
            await close_db(client)
            raise typer.Exit(1)

        # Monta query de órfãos
        query = {"is_orphan": True}

        # Se filtrar por elemento, busca o elemento primeiro
        if element:
            elem = await Element.find_one(
                Element.project_id.id == proj.id,
                Element.source_name == element
            )
            if not elem:
                console.print(f"[red]Elemento '{element}' não encontrado.[/]")
                await close_db(client)
                raise typer.Exit(1)
            query["element_id"] = elem.id
        else:
            # Busca todos os elementos do projeto para filtrar
            elements = await Element.find({"project_id.$id": proj.id}).to_list()
            element_ids = [e.id for e in elements]
            query["element_id"] = {"$in": element_ids}

        # Busca órfãos
        orphans = await Control.find(query).to_list()

        if not orphans:
            await close_db(client)
            return []

        # Cache de tipos
        type_cache: dict[str, dict] = {}

        async def get_type_info(type_def_id) -> dict:
            if type_def_id is None:
                return {"type_name": None, "inferred_name": None}

            cache_key = str(type_def_id)
            if cache_key in type_cache:
                return type_cache[cache_key]

            type_def = await ControlTypeDefinition.find_one(
                ControlTypeDefinition.id == type_def_id
            )
            if type_def:
                info = {
                    "type_name": type_def.type_name,
                    "inferred_name": type_def.inferred_name,
                }
            else:
                info = {"type_name": None, "inferred_name": None}

            type_cache[cache_key] = info
            return info

        # Cache de controles (para buscar parents)
        control_cache: dict[str, Control] = {}

        async def get_control(control_id) -> Optional[Control]:
            if control_id is None:
                return None

            cache_key = str(control_id)
            if cache_key in control_cache:
                return control_cache[cache_key]

            ctrl = await Control.find_one(Control.id == control_id)
            if ctrl:
                control_cache[cache_key] = ctrl
            return ctrl

        # Cache de elementos (para nome do elemento)
        element_cache: dict[str, str] = {}

        async def get_element_name(element_id) -> str:
            cache_key = str(element_id)
            if cache_key in element_cache:
                return element_cache[cache_key]

            elem = await Element.find_one(Element.id == element_id)
            name = elem.source_name if elem else "unknown"
            element_cache[cache_key] = name
            return name

        # Monta resultado
        result = []
        for orphan in orphans:
            # Info do tipo do órfão
            type_info = await get_type_info(orphan.type_definition_id)

            # Info do parent
            parent_info = {
                "parent_control_id": None,
                "parent_name": None,
                "parent_full_path": None,
                "parent_type_code": None,
                "parent_type_name": None,
                "parent_inferred_name": None,
            }

            if orphan.parent_control_id:
                parent = await get_control(orphan.parent_control_id)
                if parent:
                    parent_type_info = await get_type_info(parent.type_definition_id)
                    parent_info = {
                        "parent_control_id": str(parent.id),
                        "parent_name": parent.name,
                        "parent_full_path": parent.full_path,
                        "parent_type_code": parent.type_code,
                        "parent_type_name": parent_type_info["type_name"],
                        "parent_inferred_name": parent_type_info["inferred_name"],
                    }

            # Nome do elemento
            element_name = await get_element_name(orphan.element_id)

            orphan_data = {
                "_id": str(orphan.id),
                "element_id": str(orphan.element_id),
                "element_name": element_name,
                "name": orphan.name,
                "full_path": orphan.full_path,
                "type_code": orphan.type_code,
                "type_name": type_info["type_name"],
                "inferred_name": type_info["inferred_name"],
                "type_definition_id": str(orphan.type_definition_id) if orphan.type_definition_id else None,
                "depth": orphan.depth,
                "is_container": orphan.is_container,
                "has_code": orphan.has_code,
                **parent_info,
            }
            result.append(orphan_data)

        await close_db(client)
        return result

    orphans = asyncio.run(_list_orphans())

    # Valida formato
    if format not in ("json", "table"):
        console.print(f"[red]Formato inválido: {format}. Use 'json' ou 'table'.[/]")
        raise typer.Exit(1)

    # Formata saída
    if format == "json":
        output_content = json.dumps(orphans, indent=2, ensure_ascii=False)
        default_file = Path("./output/orphans.json")
    else:
        # Formato table (Markdown)
        lines = []
        lines.append(f"# Controles Órfãos - {project}")
        lines.append("")
        lines.append(f"**Total:** {len(orphans)} controles órfãos")
        lines.append("")

        # Agrupa por elemento
        by_element: dict[str, list[dict]] = {}
        for o in orphans:
            elem_name = o["element_name"]
            if elem_name not in by_element:
                by_element[elem_name] = []
            by_element[elem_name].append(o)

        # Resumo por elemento
        lines.append("## Resumo por Elemento")
        lines.append("")
        lines.append("| Elemento | Órfãos |")
        lines.append("|----------|--------|")
        for elem_name in sorted(by_element.keys()):
            count = len(by_element[elem_name])
            lines.append(f"| {elem_name} | {count} |")
        lines.append("")

        # Detalhes por elemento
        lines.append("## Detalhes")
        lines.append("")

        for elem_name in sorted(by_element.keys()):
            elem_orphans = by_element[elem_name]
            lines.append(f"### {elem_name} ({len(elem_orphans)} órfãos)")
            lines.append("")
            lines.append("| Nome | Tipo | Parent | Tipo Parent |")
            lines.append("|------|------|--------|-------------|")

            for o in elem_orphans:
                name = f"`{o['name']}`"
                tipo = o["inferred_name"] or f"code:{o['type_code']}"
                parent = f"`{o['parent_name']}`" if o["parent_name"] else "-"
                parent_tipo = o["parent_inferred_name"] or ("-" if not o["parent_type_code"] else f"code:{o['parent_type_code']}")

                lines.append(f"| {name} | {tipo} | {parent} | {parent_tipo} |")

            lines.append("")

        output_content = "\n".join(lines)
        default_file = Path("./output/orphans.md")

    # Define caminho padrão se não especificado
    if not no_file:
        if output_file is None:
            output_file = default_file

        # Cria diretório se não existir
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output_content, encoding="utf-8")
        console.print(f"[green]Salvo {len(orphans)} órfãos em {output_file}[/]")
    else:
        console.print(output_content)

    # Resumo
    if orphans:
        console.print(f"\n[dim]Total: {len(orphans)} controles órfãos[/]", highlight=False)


@app.command("parse-schema")
def parse_schema(
    project_dir: Path = typer.Argument(
        ...,
        help="Diretório do projeto WinDev/WebDev",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-P",
        help="Nome do projeto no MongoDB (sobrescreve detecção automática)",
    ),
) -> None:
    """
    Parseia o schema do banco de dados (arquivo .xdd) do projeto.

    Extrai conexões, tabelas, colunas e índices da Analysis WinDev
    e armazena no MongoDB para uso na conversão.
    """
    async def _parse_schema() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project, DatabaseSchema
        from wxcode.parser.xdd_parser import XddParser, find_analysis_file

        # Encontra arquivo do projeto
        project_file = _find_project_file(project_dir)
        if not project_file:
            console.print("[red]Arquivo de projeto não encontrado (.wwp/.wdp/.wpp)[/]")
            raise typer.Exit(1)

        # Extrai nome do projeto (ou usa o fornecido via --project)
        if project:
            project_name = project
            console.print(f"[dim]Projeto: {project_name} (fornecido via --project)[/]")
        else:
            project_name = _extract_project_name(project_file)
            if not project_name:
                project_name = project_file.stem
            console.print(f"[dim]Projeto detectado: {project_name}[/]")

        # Conecta ao banco
        client = await init_db()

        # Busca projeto no MongoDB
        proj = await Project.find_one(Project.name == project_name)
        if not proj:
            console.print(f"[red]Projeto '{project_name}' não encontrado no MongoDB.[/]")
            console.print("[dim]Execute 'wxcode import' primeiro.[/]")
            await close_db(client)
            raise typer.Exit(1)

        # Encontra arquivo .xdd
        xdd_path = find_analysis_file(project_dir, proj.analysis_path)
        if not xdd_path:
            console.print("[red]Arquivo de Analysis (.xdd) não encontrado.[/]")
            console.print("[dim]Verifique se existe um diretório *.ana com arquivo *.xdd[/]")
            await close_db(client)
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Projeto:[/] {project_name}\n"
            f"[bold]Arquivo:[/] {xdd_path.relative_to(project_dir)}",
            title="Parsing de Schema",
            border_style="blue",
        ))

        # Detecta se está em terminal interativo
        import sys
        is_interactive = sys.stdout.isatty()

        # Parseia o arquivo
        if is_interactive:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Parseando Analysis...", total=None)

                try:
                    parser = XddParser(xdd_path)
                    result = parser.parse()
                except Exception as e:
                    progress.update(task, description=f"[red]Erro: {e}[/]")
                    await close_db(client)
                    raise typer.Exit(1)

                progress.update(task, description="Salvando no MongoDB...")

                # Remove schema anterior (idempotente)
                await DatabaseSchema.find(
                    DatabaseSchema.project_id == proj.id
                ).delete()

                # Cria e salva novo schema
                schema = DatabaseSchema(
                    project_id=proj.id,
                    source_file=str(xdd_path.relative_to(project_dir)),
                    version=result.version,
                    connections=result.connections,
                    tables=result.tables,
                )
                await schema.insert()

                progress.update(task, description="Concluído!")
        else:
            print("[INFO] Parseando Analysis...", flush=True)
            try:
                parser = XddParser(xdd_path)
                result = parser.parse()
                print(f"[INFO] Schema parseado! {len(result.tables)} tabelas, {len(result.connections)} conexões", flush=True)
            except Exception as e:
                print(f"[ERROR] Erro ao parsear Analysis: {e}", flush=True)
                await close_db(client)
                raise typer.Exit(1)

            print("[INFO] Salvando no MongoDB...", flush=True)

            # Remove schema anterior (idempotente)
            await DatabaseSchema.find(
                DatabaseSchema.project_id == proj.id
            ).delete()

            # Cria e salva novo schema
            schema = DatabaseSchema(
                project_id=proj.id,
                source_file=str(xdd_path.relative_to(project_dir)),
                version=result.version,
                connections=result.connections,
                tables=result.tables,
            )
            await schema.insert()

            print("[INFO] Schema salvo no MongoDB!", flush=True)

        # Exibe resultado
        table = Table(title="Resultado do Parsing de Schema")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        table.add_row("Versão da Analysis", str(result.version))
        table.add_row("Conexões", str(result.total_connections))
        table.add_row("Tabelas", str(result.total_tables))
        table.add_row("Colunas", str(result.total_columns))

        if result.warnings:
            table.add_row("Warnings", str(len(result.warnings)))

        console.print(table)

        # Exibe warnings se houver
        if result.warnings:
            console.print("\n[yellow]Warnings:[/]")
            for warning in result.warnings[:5]:
                console.print(f"  [yellow]•[/] {warning}")
            if len(result.warnings) > 5:
                console.print(f"  [dim]... e mais {len(result.warnings) - 5} warnings[/]")

        # Exibe algumas tabelas como preview
        if result.tables:
            console.print("\n[bold]Preview das tabelas:[/]")
            for table_data in result.tables[:5]:
                pk_cols = table_data.primary_key_columns
                pk_str = f" (PK: {', '.join(pk_cols)})" if pk_cols else ""
                console.print(
                    f"  [cyan]•[/] {table_data.name}: {table_data.column_count} colunas{pk_str}"
                )
            if len(result.tables) > 5:
                console.print(f"  [dim]... e mais {len(result.tables) - 5} tabelas[/]")

        await close_db(client)

        console.print(f"\n[green]Schema salvo no MongoDB![/]")

    asyncio.run(_parse_schema())


@app.command("convert-page")
def convert_page(
    page_name: str = typer.Argument(
        ...,
        help="Nome da página a converter (ex: PAGE_Login)",
    ),
    output: Path = typer.Option(
        Path("./output/generated/app"),
        "--output",
        "-o",
        help="Diretório de saída do projeto",
    ),
    project: str = typer.Option(
        "Linkpay_ADM",
        "--project",
        "-p",
        help="Nome do projeto no MongoDB",
    ),
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-P",
        help="LLM provider (anthropic, openai, ollama)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo específico (usa default do provider se não fornecido)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Não escreve arquivos, apenas mostra o que seria gerado",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Exibe detalhes do contexto e resposta do LLM",
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        "-t",
        help="Tema Bootstrap para skills (ex: dashlite). Use 'themes list' para ver disponíveis.",
    ),
    deploy_assets: bool = typer.Option(
        False,
        "--deploy-assets",
        help="Copia assets do tema (CSS, JS, fonts, images) antes da conversão. Requer --theme.",
    ),
) -> None:
    """
    Converte uma página WinDev para FastAPI + Jinja2 usando LLM.

    Usa LLM para analisar os controles, eventos e procedures da página
    e gerar código Python (rota FastAPI) e HTML (template Jinja2).

    Providers disponíveis:
        - anthropic: Claude (claude-sonnet-4-20250514, claude-opus-4, claude-3-5-haiku)
        - openai: GPT (gpt-4o, gpt-4o-mini, gpt-4-turbo)
        - ollama: Modelos locais (llama3.1, mistral, codellama)

    Theme Skills:
        Quando um tema é especificado (--theme), o LLM recebe documentação
        específica do tema com classes CSS, estruturas HTML e padrões
        de componentes. Isso gera HTML muito mais preciso para o tema.

    Exemplos:
        wxcode convert-page PAGE_Login
        wxcode convert-page PAGE_Login --theme dashlite
        wxcode convert-page PAGE_Login --theme dashlite --deploy-assets
        wxcode convert-page PAGE_Login --provider openai --model gpt-4o-mini
        wxcode convert-page PAGE_Login --provider ollama
        wxcode convert-page PAGE_Login --dry-run
    """
    # Validar que --deploy-assets requer --theme
    if deploy_assets and not theme:
        console.print("[red]Erro: --deploy-assets requer --theme[/]")
        console.print("[dim]Exemplo: wxcode convert-page PAGE_Login --theme dashlite --deploy-assets[/]")
        raise typer.Exit(1)

    async def _convert() -> None:
        from wxcode.config import get_settings
        from wxcode.database import init_db, close_db
        from wxcode.llm_converter import PageConverter, ConversionError
        from wxcode.llm_converter.providers import create_provider

        # Resolve modelo (usa default do provider se não especificado)
        model_display = model or "(default)"
        theme_display = theme or "(nenhum)"
        deploy_display = "Sim" if deploy_assets else "Não"

        console.print(Panel(
            f"[bold]Página:[/] {page_name}\n"
            f"[bold]Projeto:[/] {project}\n"
            f"[bold]Output:[/] {output}\n"
            f"[bold]Provider:[/] {provider}\n"
            f"[bold]Modelo:[/] {model_display}\n"
            f"[bold]Tema:[/] {theme_display}\n"
            f"[bold]Deploy assets:[/] {deploy_display}\n"
            f"[bold]Dry run:[/] {'Sim' if dry_run else 'Não'}",
            title="Convertendo Página",
            border_style="blue",
        ))

        # Deploy assets do tema se solicitado
        if deploy_assets and theme:
            from wxcode.generator.theme_deployer import deploy_theme_assets, get_theme_path

            theme_path = get_theme_path(theme)
            if theme_path is None:
                console.print(f"[red]Tema '{theme}' não encontrado para deploy de assets.[/]")
                raise typer.Exit(1)

            console.print(f"[dim]Copiando assets do tema {theme_path.name}...[/]")
            deploy_result = deploy_theme_assets(theme=theme, output_dir=output)

            if deploy_result.success:
                console.print(
                    f"[green]✓[/] {deploy_result.stats.total} assets copiados "
                    f"({deploy_result.stats.css_count} CSS, {deploy_result.stats.js_count} JS, "
                    f"{deploy_result.stats.fonts_count} fonts, {deploy_result.stats.images_count} images)"
                )
            else:
                console.print(f"[yellow]Aviso: Falha ao copiar alguns assets[/]")
                for error in deploy_result.errors:
                    console.print(f"  [yellow]•[/] {error}")

        # Conecta ao banco
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando ao MongoDB...", total=None)

            settings = get_settings()
            client = await init_db()
            db = client[settings.mongodb_database]

            progress.update(task, description="Buscando página...")

            # Verifica se página existe
            element = await db.elements.find_one({"source_name": page_name})
            if not element:
                progress.update(task, description=f"[red]Página não encontrada: {page_name}[/]")
                await close_db(client)
                raise typer.Exit(1)

            progress.update(task, description=f"Criando provider {provider}...")

            try:
                # Cria provider LLM
                llm_provider = create_provider(provider, model=model)
                converter = PageConverter(
                    db,
                    output,
                    llm_provider=llm_provider,
                    theme=theme,
                    project_root=Path.cwd(),
                )

                progress.update(task, description=f"Chamando {provider} (pode demorar)...")

                # Converte
                result = await converter.convert(element["_id"], dry_run=dry_run)

                progress.update(task, description="Concluído!")

            except ValueError as e:
                # Provider desconhecido
                progress.update(task, description=f"[red]Erro: {e}[/]")
                await close_db(client)
                raise typer.Exit(1)
            except ConversionError as e:
                progress.update(task, description=f"[red]Erro: {e}[/]")
                await close_db(client)
                raise typer.Exit(1)

        # Exibe resultado
        table = Table(title="Resultado da Conversão")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        table.add_row("Página", result.page_name)
        table.add_row("Tokens (input)", str(result.tokens_used.get("input", 0)))
        table.add_row("Tokens (output)", str(result.tokens_used.get("output", 0)))
        table.add_row("Duração", f"{result.duration_seconds:.2f}s")
        table.add_row("Custo estimado", f"${result.cost_usd:.4f}")
        table.add_row("Arquivos criados", str(len(result.files_created)))

        console.print(table)

        # Lista arquivos criados
        if result.files_created:
            console.print("\n[bold]Arquivos criados:[/]")
            for f in result.files_created:
                console.print(f"  [green]✓[/] {f}")
        elif dry_run:
            console.print("\n[yellow]Dry run - nenhum arquivo foi criado[/]")

        # Exibe notas
        if result.notes:
            console.print("\n[yellow]Notas:[/]")
            for note in result.notes:
                console.print(f"  [yellow]•[/] {note}")

        await close_db(client)

        if not dry_run:
            console.print(f"\n[green]Conversão concluída![/]")
            console.print(f"[dim]Para testar: cd {output} && uvicorn app.main:app --reload[/]")

    asyncio.run(_convert())


@app.command("themes")
def themes(
    action: str = typer.Argument(
        "list",
        help="Ação: 'list' para listar temas disponíveis",
    ),
    show_assets: bool = typer.Option(
        True,
        "--assets/--no-assets",
        help="Mostra contagem de assets (CSS, JS, fonts, images)",
    ),
) -> None:
    """
    Gerencia temas de skills para conversão LLM.

    Os temas fornecem documentação específica de componentes Bootstrap
    que o LLM usa para gerar HTML mais preciso e compatível.

    Ações:
        list: Lista temas disponíveis com suas descrições e assets

    Exemplos:
        wxcode themes          # Lista temas com assets
        wxcode themes list     # Lista temas (explícito)
        wxcode themes --no-assets  # Sem contagem de assets
    """
    from wxcode.generator.theme_skill_loader import get_available_themes
    from wxcode.generator.theme_deployer import (
        list_themes as list_asset_themes,
        get_theme_path,
        get_theme_asset_stats,
    )

    if action != "list":
        console.print(f"[red]Ação desconhecida: {action}[/]")
        console.print("[dim]Ações disponíveis: list[/]")
        raise typer.Exit(1)

    # Temas de skills (para LLM)
    skill_themes = get_available_themes(project_root=Path.cwd())

    # Temas de assets (para deploy)
    asset_themes = list_asset_themes()

    if not skill_themes and not asset_themes:
        console.print("[yellow]Nenhum tema encontrado.[/]")
        console.print(
            "\n[dim]Skills devem estar em:[/] .claude/skills/themes/<nome-tema>/"
        )
        console.print("[dim]Assets devem estar em:[/] themes/<nome-tema>/")
        return

    # Combinar informações de skills e assets
    all_theme_names = set()
    skill_dict = {t["name"]: t for t in skill_themes}
    all_theme_names.update(skill_dict.keys())
    all_theme_names.update(asset_themes)

    # Tabela com ou sem assets
    if show_assets:
        table = Table(title="Temas Disponíveis")
        table.add_column("Nome", style="cyan", no_wrap=True)
        table.add_column("Skills", style="green", justify="center")
        table.add_column("CSS", justify="right")
        table.add_column("JS", justify="right")
        table.add_column("Fonts", justify="right")
        table.add_column("Images", justify="right")

        for name in sorted(all_theme_names):
            has_skills = "✓" if name in skill_dict else "✗"

            # Buscar assets (tema pode ter versão no nome)
            theme_path = get_theme_path(name)
            if theme_path:
                stats = get_theme_asset_stats(theme_path)
                css = str(stats.css_count)
                js = str(stats.js_count)
                fonts = str(stats.fonts_count)
                images = str(stats.images_count)
            else:
                css = js = fonts = images = "-"

            table.add_row(name, has_skills, css, js, fonts, images)
    else:
        table = Table(title="Temas Disponíveis")
        table.add_column("Nome", style="cyan", no_wrap=True)
        table.add_column("Descrição", style="green")

        for t in skill_themes:
            table.add_row(t["name"], t["description"])

    console.print(table)
    console.print(
        f"\n[dim]Use --theme <nome> no convert-page para usar um tema[/]"
    )
    console.print(
        f"[dim]Use deploy-theme <nome> para copiar assets para o projeto[/]"
    )


@app.command("deploy-theme")
def deploy_theme(
    theme: str = typer.Argument(
        ...,
        help="Nome do tema (ex: dashlite)",
    ),
    output: Path = typer.Option(
        Path("./output/generated"),
        "--output",
        "-o",
        help="Diretório raiz do projeto gerado",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Sobrescreve arquivos existentes",
    ),
) -> None:
    """
    Copia assets de tema (CSS, JS, fonts, images) para o projeto gerado.

    Execute este comando após 'init-project' e antes de 'convert-page'
    para garantir que os assets do tema estejam disponíveis.

    Exemplos:
        wxcode deploy-theme dashlite -o ./output/generated
        wxcode deploy-theme dashlite-v3.3.0 -o ./meu-projeto
        wxcode deploy-theme dashlite --no-overwrite
    """
    from wxcode.generator.theme_deployer import (
        deploy_theme_assets,
        list_themes,
        get_theme_path,
    )

    # Verifica se tema existe
    theme_path = get_theme_path(theme)
    if theme_path is None:
        available = list_themes()
        console.print(f"[red]Tema '{theme}' não encontrado.[/]")
        if available:
            console.print(f"[dim]Temas disponíveis: {', '.join(available)}[/]")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]Tema:[/] {theme_path.name}\n"
        f"[bold]Output:[/] {output}\n"
        f"[bold]Sobrescrever:[/] {'Sim' if overwrite else 'Não'}",
        title="Deploy de Tema",
        border_style="blue",
    ))

    # Executa deploy
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Copiando assets...", total=None)

        result = deploy_theme_assets(
            theme=theme,
            output_dir=output,
            overwrite=overwrite,
        )

        if result.success:
            progress.update(task, description="[green]Concluído![/]")
        else:
            progress.update(task, description="[red]Falhou![/]")

    # Exibe resultado
    if result.success:
        table = Table(title="Assets Copiados")
        table.add_column("Tipo", style="cyan")
        table.add_column("Quantidade", justify="right", style="green")

        table.add_row("CSS", str(result.stats.css_count))
        table.add_row("JavaScript", str(result.stats.js_count))
        table.add_row("Fonts", str(result.stats.fonts_count))
        table.add_row("Images", str(result.stats.images_count))
        table.add_row("[bold]Total[/]", f"[bold]{result.stats.total}[/]")

        console.print(table)
        console.print(f"\n[green]Deploy concluído![/]")
        console.print(
            f"[dim]Assets disponíveis em: {output}/app/static/[/]"
        )
    else:
        console.print(f"\n[red]Erros durante o deploy:[/]")
        for error in result.errors:
            console.print(f"  [red]•[/] {error}")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS NEO4J
# ============================================================================


@app.command("sync-neo4j")
def sync_neo4j(
    project: str = typer.Argument(..., help="Nome do projeto"),
    clear: bool = typer.Option(
        True,
        "--clear/--no-clear",
        help="Limpa dados existentes antes de sincronizar",
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Valida contagens após sincronização",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Mostra o que seria feito sem executar",
    ),
) -> None:
    """
    Sincroniza grafo de dependências para Neo4j.

    Exporta nós (tabelas, classes, procedures, páginas) e relacionamentos
    (INHERITS, CALLS, USES_TABLE, USES_CLASS) para análise avançada.

    Exemplos:
      wxcode sync-neo4j Linkpay_ADM
      wxcode sync-neo4j Linkpay_ADM --dry-run
      wxcode sync-neo4j Linkpay_ADM --no-clear
    """
    async def _sync() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.models import Project
        from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
        from wxcode.graph.neo4j_sync import Neo4jSyncService

        # Conecta ao MongoDB
        client = await init_db()

        # Busca projeto
        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado no MongoDB.[/]")
            await close_db(client)
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Projeto:[/] {project}\n"
            f"[bold]Limpar antes:[/] {'Sim' if clear else 'Não'}\n"
            f"[bold]Validar:[/] {'Sim' if validate else 'Não'}\n"
            f"[bold]Modo:[/] {'Dry-run' if dry_run else 'Executar'}",
            title="Sincronização Neo4j",
            border_style="blue",
        ))

        try:
            async with Neo4jConnection() as conn:
                sync_service = Neo4jSyncService(conn)

                if dry_run:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Calculando estatísticas...", total=None)
                        result = await sync_service.dry_run(proj.id)
                        progress.update(task, description="Concluído!")

                    console.print("\n[yellow]Modo dry-run - nenhum dado foi modificado[/]")
                else:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Sincronizando com Neo4j...", total=None)
                        result = await sync_service.sync_project(
                            proj.id, clear=clear, validate=validate
                        )
                        progress.update(task, description="Concluído!")

                # Exibe resultado
                table = Table(title="Resultado da Sincronização")
                table.add_column("Métrica", style="cyan")
                table.add_column("Valor", justify="right", style="green")

                table.add_row("Tabelas", str(result.tables_count))
                table.add_row("Classes", str(result.classes_count))
                table.add_row("Procedures", str(result.procedures_count))
                table.add_row("Páginas", str(result.pages_count))
                table.add_row("Windows", str(result.windows_count))
                table.add_row("Queries", str(result.queries_count))
                table.add_row("─" * 20, "─" * 10)
                table.add_row("Total de nós", str(result.nodes_created))
                table.add_row("Relacionamentos", str(result.relationships_created))

                console.print(table)

                if result.errors:
                    console.print("\n[red]Erros:[/]")
                    for error in result.errors:
                        console.print(f"  [red]•[/] {error}")
                else:
                    if not dry_run:
                        console.print("\n[green]Sincronização concluída com sucesso![/]")
                        console.print("[dim]Acesse Neo4j Browser em http://localhost:7474[/]")

        except Neo4jConnectionError as e:
            console.print(f"\n[red]Erro de conexão com Neo4j:[/]")
            console.print(f"  {e}")
            console.print("\n[dim]Verifique se o Neo4j está rodando:[/]")
            console.print("  docker run -d -p 7474:7474 -p 7687:7687 \\")
            console.print("    -e NEO4J_AUTH=neo4j/password neo4j:5")
            await close_db(client)
            raise typer.Exit(1)

        await close_db(client)

    asyncio.run(_sync())


@app.command("impact")
def impact(
    node_id: str = typer.Argument(
        ...,
        help="Identificador do nó (ex: TABLE:CLIENTE, proc:ValidaCPF, PAGE_Login)",
    ),
    depth: int = typer.Option(
        5,
        "--depth",
        "-d",
        help="Profundidade máxima de busca",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filtrar por projeto",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Formato de saída: table, json",
    ),
) -> None:
    """
    Analisa impacto de mudanças em um elemento.

    Mostra todos os elementos que seriam afetados se o elemento especificado
    fosse modificado.

    Exemplos:
      wxcode impact TABLE:CLIENTE
      wxcode impact proc:ValidaCPF --depth 3
      wxcode impact PAGE_Login --format json
    """
    async def _impact() -> None:
        from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
        from wxcode.graph.impact_analyzer import ImpactAnalyzer
        import json

        try:
            async with Neo4jConnection() as conn:
                analyzer = ImpactAnalyzer(conn)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Analisando impacto...", total=None)
                    result = await analyzer.get_impact(node_id, max_depth=depth, project=project)
                    progress.update(task, description="Concluído!")

                if result.error:
                    console.print(f"[red]Erro:[/] {result.error}")
                    raise typer.Exit(1)

                if format == "json":
                    output = {
                        "source": {"name": result.source_name, "type": result.source_type},
                        "affected": [
                            {"name": n.name, "type": n.node_type, "depth": n.depth}
                            for n in result.affected
                        ],
                        "total": result.total_affected,
                    }
                    console.print(json.dumps(output, indent=2))
                else:
                    console.print(Panel(
                        f"[bold]Elemento:[/] {result.source_name} ({result.source_type})\n"
                        f"[bold]Profundidade:[/] {depth}\n"
                        f"[bold]Afetados:[/] {result.total_affected}",
                        title="Análise de Impacto",
                        border_style="blue",
                    ))

                    if not result.affected:
                        console.print("\n[yellow]Nenhum elemento afetado[/]")
                    else:
                        # Agrupa por profundidade
                        by_depth = result.by_depth()
                        for d in sorted(by_depth.keys()):
                            console.print(f"\n[bold]Profundidade {d}:[/]")
                            for node in by_depth[d]:
                                console.print(f"  [cyan]{node.node_type}:[/] {node.name}")

        except Neo4jConnectionError as e:
            console.print(f"[red]Erro de conexão:[/] {e}")
            raise typer.Exit(1)

    asyncio.run(_impact())


@app.command("gsd-context")
def gsd_context(
    element_name: str = typer.Argument(..., help="Nome do elemento"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Nome do projeto"),
    depth: int = typer.Option(2, "--depth", "-d", help="Profundidade Neo4j"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Diretório de saída"),
    skip_gsd: bool = typer.Option(False, "--skip-gsd", help="Só coleta, não executa GSD"),
    no_branch: bool = typer.Option(False, "--no-branch", help="Não cria branch"),
) -> None:
    """
    Coleta contexto de elemento e dispara workflow GSD.

    Coleta dados completos do MongoDB + Neo4j, cria branch git,
    exporta arquivos estruturados e dispara workflow GSD via Claude Code.

    Exemplos:
      wxcode gsd-context PAGE_Login --project Linkpay_ADM
      wxcode gsd-context PAGE_Login  # Auto-detect project
      wxcode gsd-context PAGE_Login --skip-gsd --no-branch  # Debug mode
    """
    async def _inner() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
        from wxcode.services.gsd_context_collector import (
            GSDContextCollector,
            GSDContextWriter,
            create_gsd_branch,
        )
        from wxcode.services.gsd_invoker import GSDInvoker, GSDInvokerError

        # 1. Init DB
        client = await init_db()

        try:
            # 2. Determine output dir
            if output_dir is None:
                output_path = Path("./output/gsd-context") / element_name
            else:
                output_path = output_dir

            # 3. Create branch
            if not no_branch:
                branch_name = create_gsd_branch(element_name)
            else:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                branch_name = result.stdout.strip()
                console.print(f"[dim]Using current branch: {branch_name}[/]")

            # 4. Collect data (with Progress UI)
            neo4j_conn = None
            try:
                neo4j_conn = Neo4jConnection()
                await neo4j_conn.__aenter__()
            except Neo4jConnectionError as e:
                console.print(f"[yellow]Neo4j unavailable: {e}, using MongoDB only[/]")

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Collecting element data...", total=None)

                    collector = GSDContextCollector(client, neo4j_conn)
                    data = await collector.collect(element_name, project, depth)

                    progress.update(task, description="✓ Data collected")
            finally:
                if neo4j_conn:
                    await neo4j_conn.__aexit__(None, None, None)

            # 5. Write files
            console.print(f"\n[cyan]Writing context files to {output_path}...[/]")
            writer = GSDContextWriter(output_path)
            files = writer.write_all(data, branch_name)

            # 6. Display summary (Table)
            table = Table(title=f"GSD Context: {element_name}", box=box.ROUNDED)
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", justify="right", style="green")

            table.add_row("Element", data.element.source_name)
            table.add_row("Type", data.element.source_type)
            table.add_row("Project", data.project.name)
            table.add_row("Controls", str(data.stats["controls_total"]))
            table.add_row("  └─ with code", str(data.stats["controls_with_code"]))
            table.add_row("Local Procedures", str(data.stats["local_procedures_count"]))
            table.add_row("Dependencies", str(len(data.element.dependencies.uses if data.element.dependencies else [])))
            table.add_row("Bound Tables", str(len(data.bound_tables)))
            table.add_row("Output", str(output_path))
            table.add_row("Branch", branch_name)
            table.add_row("Neo4j", "✓ Available" if data.neo4j_available else "✗ Unavailable")

            console.print()
            console.print(table)

            # 7. List generated files
            console.print("\n[bold]Generated Files:[/]")
            for name, path in files.items():
                size = path.stat().st_size
                console.print(f"  [cyan]•[/] {path.name} ({size:,} bytes)")

            # 8. Invoke GSD (unless --skip-gsd)
            if not skip_gsd:
                console.print("\n[cyan]Invoking GSD workflow...[/]")

                invoker = GSDInvoker(
                    context_md_path=files["context"], working_dir=output_path
                )

                # Check if Claude Code is available
                if not invoker.check_claude_code_available():
                    console.print(
                        "[yellow]⚠ Claude Code CLI not found. Install it with:[/]\n"
                        "  npm install -g @anthropic-ai/claude-code\n"
                    )
                    console.print(f"[dim]Manual command:[/] {invoker.get_command_string()}")
                else:
                    try:
                        invoker.invoke_gsd(timeout=600)
                        console.print("[green]✓ GSD workflow started[/]")
                    except GSDInvokerError as e:
                        console.print(f"[yellow]⚠ GSD invocation failed: {e}[/]")
                        console.print(f"[dim]Manual command:[/] {invoker.get_command_string()}")
            else:
                console.print("\n[dim]Skipped GSD invocation (use --skip-gsd=False to enable)[/]")
                invoker = GSDInvoker(
                    context_md_path=files["context"], working_dir=output_path
                )
                console.print(f"[dim]To invoke manually:[/] {invoker.get_command_string()}")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/]")
            import traceback

            console.print(f"[red]{traceback.format_exc()}[/]")
            raise typer.Exit(1)
        finally:
            await close_db(client)

    asyncio.run(_inner())


@app.command("path")
def path(
    source: str = typer.Argument(..., help="Nome do nó origem"),
    target: str = typer.Argument(..., help="Nome do nó destino"),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filtrar por projeto",
    ),
) -> None:
    """
    Encontra caminhos entre dois elementos.

    Mostra o caminho mais curto e caminhos alternativos entre dois nós.

    Exemplos:
      wxcode path PAGE_Login TABLE:USUARIO
      wxcode path classCliente proc:ValidaCPF
    """
    async def _path() -> None:
        from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
        from wxcode.graph.impact_analyzer import ImpactAnalyzer

        try:
            async with Neo4jConnection() as conn:
                analyzer = ImpactAnalyzer(conn)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Buscando caminhos...", total=None)
                    result = await analyzer.get_path(source, target, project=project)
                    progress.update(task, description="Concluído!")

                if result.error:
                    console.print(f"[yellow]{result.error}[/]")
                    raise typer.Exit(0)

                console.print(Panel(
                    f"[bold]Origem:[/] {source}\n"
                    f"[bold]Destino:[/] {target}\n"
                    f"[bold]Caminhos encontrados:[/] {len(result.paths)}",
                    title="Busca de Caminhos",
                    border_style="blue",
                ))

                for i, path_nodes in enumerate(result.paths, 1):
                    path_str = " → ".join(
                        f"{n.node_type}:{n.name}" for n in path_nodes
                    )
                    console.print(f"\n[bold]{i}.[/] {path_str}")
                    console.print(f"   [dim]({len(path_nodes) - 1} hops)[/]")

        except Neo4jConnectionError as e:
            console.print(f"[red]Erro de conexão:[/] {e}")
            raise typer.Exit(1)

    asyncio.run(_path())


@app.command("hubs")
def hubs(
    min_connections: int = typer.Option(
        10,
        "--min-connections",
        "-m",
        help="Número mínimo de conexões para ser considerado hub",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filtrar por projeto",
    ),
) -> None:
    """
    Encontra nós críticos (hubs) com muitas conexões.

    Hubs são elementos centrais que muitos outros dependem.
    Mudanças neles têm alto impacto.

    Exemplos:
      wxcode hubs --min-connections 10
      wxcode hubs -m 5 -p Linkpay_ADM
    """
    async def _hubs() -> None:
        from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
        from wxcode.graph.impact_analyzer import ImpactAnalyzer

        try:
            async with Neo4jConnection() as conn:
                analyzer = ImpactAnalyzer(conn)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Buscando hubs...", total=None)
                    result = await analyzer.find_hubs(
                        min_connections=min_connections, project=project
                    )
                    progress.update(task, description="Concluído!")

                if result.error:
                    console.print(f"[red]Erro:[/] {result.error}")
                    raise typer.Exit(1)

                console.print(Panel(
                    f"[bold]Conexões mínimas:[/] {min_connections}\n"
                    f"[bold]Hubs encontrados:[/] {len(result.hubs)}",
                    title="Hubs (Nós Críticos)",
                    border_style="blue",
                ))

                if not result.hubs:
                    console.print(f"\n[yellow]Nenhum hub com {min_connections}+ conexões[/]")
                else:
                    table = Table()
                    table.add_column("#", style="dim")
                    table.add_column("Nome", style="cyan")
                    table.add_column("Tipo", style="green")
                    table.add_column("Entrada", justify="right")
                    table.add_column("Saída", justify="right")
                    table.add_column("Total", justify="right", style="bold")

                    for i, hub in enumerate(result.hubs, 1):
                        table.add_row(
                            str(i),
                            hub.name,
                            hub.node_type,
                            str(hub.incoming),
                            str(hub.outgoing),
                            str(hub.total_connections),
                        )

                    console.print(table)

        except Neo4jConnectionError as e:
            console.print(f"[red]Erro de conexão:[/] {e}")
            raise typer.Exit(1)

    asyncio.run(_hubs())


@app.command("dead-code")
def dead_code(
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filtrar por projeto",
    ),
) -> None:
    """
    Encontra código potencialmente não utilizado.

    Lista procedures e classes que não são chamadas/usadas por nenhum
    outro elemento. Entry points (APIs, Pages) são excluídos.

    Exemplos:
      wxcode dead-code
      wxcode dead-code -p Linkpay_ADM
    """
    async def _dead_code() -> None:
        from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
        from wxcode.graph.impact_analyzer import ImpactAnalyzer

        try:
            async with Neo4jConnection() as conn:
                analyzer = ImpactAnalyzer(conn)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Buscando código morto...", total=None)
                    result = await analyzer.find_dead_code(project=project)
                    progress.update(task, description="Concluído!")

                if result.error:
                    console.print(f"[red]Erro:[/] {result.error}")
                    raise typer.Exit(1)

                console.print(Panel(
                    f"[bold]Procedures órfãs:[/] {len(result.procedures)}\n"
                    f"[bold]Classes órfãs:[/] {len(result.classes)}\n"
                    f"[bold]Total:[/] {result.total}",
                    title="Código Potencialmente Não Utilizado",
                    border_style="yellow",
                ))

                if result.procedures:
                    console.print("\n[bold]Procedures sem chamadores:[/]")
                    for proc in result.procedures[:20]:
                        console.print(f"  [cyan]•[/] {proc}")
                    if len(result.procedures) > 20:
                        console.print(f"  [dim]... e mais {len(result.procedures) - 20}[/]")

                if result.classes:
                    console.print("\n[bold]Classes não utilizadas:[/]")
                    for cls in result.classes[:20]:
                        console.print(f"  [green]•[/] {cls}")
                    if len(result.classes) > 20:
                        console.print(f"  [dim]... e mais {len(result.classes) - 20}[/]")

                if result.total == 0:
                    console.print("\n[green]Nenhum código morto detectado![/]")
                else:
                    console.print("\n[dim]Nota: Estes elementos podem ser entry points não detectados.[/]")
                    console.print("[dim]Verifique manualmente antes de remover.[/]")

        except Neo4jConnectionError as e:
            console.print(f"[red]Erro de conexão:[/] {e}")
            raise typer.Exit(1)

    asyncio.run(_dead_code())


@app.command("purge")
def purge_project_cmd(
    project_name: str = typer.Argument(
        None,
        help="Nome do projeto a ser removido",
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="ID do projeto a ser removido (use quando há duplicatas)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Confirma a remoção sem perguntar",
    ),
) -> None:
    """
    Remove completamente um projeto e todos os seus dados do banco.

    Remove todas as collections dependentes:
    - elements (elementos do projeto)
    - controls (controles de UI)
    - procedures (procedures globais e locais)
    - class_definitions (classes)
    - schemas (schema do banco)
    - conversions (conversões realizadas)

    ATENÇÃO: Esta operação é irreversível!
    """
    # Valida argumentos
    if not project_name and not project_id:
        console.print("[red]Erro:[/] Informe o nome do projeto ou use --id para especificar o ID")
        raise typer.Exit(1)

    async def _purge() -> None:
        from beanie import PydanticObjectId
        from wxcode.database import init_db, close_db
        from wxcode.services import purge_project_by_name, purge_project, PurgeStats
        from wxcode.models import Project

        # Conecta ao banco
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando ao MongoDB...", total=None)
            client = await init_db()
            progress.update(task, description="Conectado ao MongoDB")

        # Busca projeto por ID ou nome
        if project_id:
            try:
                obj_id = PydanticObjectId(project_id)
                project = await Project.get(obj_id)
            except Exception:
                console.print(f"[red]Erro:[/] ID inválido: {project_id}")
                await close_db(client)
                raise typer.Exit(1)
            if not project:
                console.print(f"[red]Erro:[/] Projeto com ID '{project_id}' não encontrado")
                await close_db(client)
                raise typer.Exit(1)
        else:
            # Busca por nome - verifica se há duplicatas
            projects = await Project.find(Project.name == project_name).to_list()
            if not projects:
                console.print(f"[red]Erro:[/] Projeto '{project_name}' não encontrado")
                await close_db(client)
                raise typer.Exit(1)
            if len(projects) > 1:
                console.print(f"[yellow]Aviso:[/] Encontrados {len(projects)} projetos com nome '{project_name}':")
                table = Table(title="Projetos Duplicados")
                table.add_column("ID", style="cyan")
                table.add_column("Criado em", style="green")
                for p in sorted(projects, key=lambda x: x.created_at or ""):
                    created = p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "N/A"
                    table.add_row(str(p.id), created)
                console.print(table)
                console.print("\n[yellow]Use --id para especificar qual projeto remover[/]")
                await close_db(client)
                raise typer.Exit(1)
            project = projects[0]

        # Confirmação
        if not yes:
            console.print(Panel(
                f"[bold red]ATENÇÃO:[/] Esta operação é irreversível!\n\n"
                f"Projeto: [bold]{project_name}[/]\n"
                f"ID: {project.id}\n"
                f"Elementos: {project.total_elements}",
                title="Confirmar Purge",
                border_style="red",
            ))
            confirm = typer.confirm("Deseja continuar com a remoção?")
            if not confirm:
                console.print("[yellow]Operação cancelada.[/]")
                await close_db(client)
                raise typer.Exit(0)

        # Executa purge
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Removendo projeto...", total=None)
            stats = await purge_project(project.id)
            progress.update(task, description="Projeto removido")

        # Fecha conexão
        await close_db(client)

        # Exibe estatísticas
        table = Table(title="Resultado do Purge")
        table.add_column("Collection", style="cyan")
        table.add_column("Documentos Removidos", justify="right", style="green")

        table.add_row("projects", str(stats.projects))
        table.add_row("elements", str(stats.elements))
        table.add_row("controls", str(stats.controls))
        table.add_row("procedures", str(stats.procedures))
        table.add_row("class_definitions", str(stats.class_definitions))
        table.add_row("schemas", str(stats.schemas))
        table.add_row("conversions", str(stats.conversions))
        table.add_row("[bold]Total MongoDB[/]", f"[bold]{stats.total}[/]")

        # Neo4j stats
        if stats.neo4j_nodes > 0:
            table.add_row("[dim]neo4j_nodes[/]", f"[dim]{stats.neo4j_nodes}[/]")
        elif stats.neo4j_error:
            table.add_row("[dim]neo4j[/]", "[yellow]não disponível[/]")

        console.print(table)
        console.print(f"\n[green]Projeto '{stats.project_name}' removido com sucesso![/]")

        if stats.neo4j_error:
            console.print(f"[dim]Nota: Neo4j não estava disponível ({stats.neo4j_error})[/]")

    asyncio.run(_purge())


@app.command("check-duplicates")
def check_duplicates_cmd() -> None:
    """
    Verifica se existem projetos com nomes duplicados no banco.

    Útil para rodar antes de aplicar o índice único no campo name.
    """
    async def _check() -> None:
        from wxcode.database import init_db, close_db
        from wxcode.services import check_duplicate_projects

        # Conecta ao banco
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conectando ao MongoDB...", total=None)
            client = await init_db()
            progress.update(task, description="Conectado ao MongoDB")

        # Verifica duplicatas
        duplicates = await check_duplicate_projects()

        # Fecha conexão
        await close_db(client)

        if not duplicates:
            console.print("[green]Nenhum projeto duplicado encontrado![/]")
            console.print("[dim]O índice único pode ser aplicado com segurança.[/]")
            return

        # Exibe duplicatas
        console.print(Panel(
            f"[bold red]Encontrados {len(duplicates)} nomes duplicados![/]\n"
            f"Corrija os duplicados antes de aplicar o índice único.",
            title="Projetos Duplicados",
            border_style="red",
        ))

        table = Table(title="Nomes Duplicados")
        table.add_column("Nome", style="cyan")
        table.add_column("Ocorrências", justify="right", style="yellow")
        table.add_column("IDs", style="dim")

        for dup in duplicates:
            ids = ", ".join(dup.ids[:3])
            if len(dup.ids) > 3:
                ids += f" (+{len(dup.ids) - 3})"
            table.add_row(dup.name, str(dup.count), ids)

        console.print(table)
        console.print("\n[yellow]Use 'wxcode purge <nome>' para remover duplicados.[/]")

    asyncio.run(_check())


@app.command("test-app")
def test_app(
    app_path: Path = typer.Argument(
        ...,
        help="Caminho para a aplicação gerada (ex: ./output/generated/Producao)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    port: int = typer.Option(
        8000,
        "--port", "-p",
        help="Porta para rodar a aplicação",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Não abrir o navegador automaticamente",
    ),
) -> None:
    """Cria ambiente virtual, instala dependências e testa a aplicação gerada."""
    import subprocess
    import sys
    import platform
    import webbrowser
    import time

    app_path = app_path.resolve()
    venv_path = app_path / ".venv"
    is_windows = platform.system() == "Windows"

    console.print(Panel(
        f"[bold]Testando aplicação[/]\n"
        f"Path: {app_path}\n"
        f"Port: {port}",
        title="Test App",
        border_style="blue",
    ))

    # Check if main.py exists
    main_py = app_path / "app" / "main.py"
    if not main_py.exists():
        console.print(f"[red]Erro: {main_py} não encontrado. Verifique o caminho.[/]")
        raise typer.Exit(1)

    # Step 1: Create virtual environment if not exists
    if not venv_path.exists():
        console.print("\n[cyan]1. Criando ambiente virtual...[/]")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            cwd=app_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]Erro ao criar venv: {result.stderr}[/]")
            raise typer.Exit(1)
        console.print("[green]✓ Ambiente virtual criado[/]")
    else:
        console.print("\n[cyan]1. Ambiente virtual já existe[/]")

    # Get python and pip paths
    if is_windows:
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"

    # Step 2: Install dependencies
    console.print("\n[cyan]2. Instalando dependências...[/]")
    deps = [
        "fastapi", "uvicorn[standard]", "sqlalchemy[asyncio]",
        "aioodbc", "pyodbc", "pydantic", "pydantic-settings",
        "jinja2", "python-multipart", "httpx"
    ]
    result = subprocess.run(
        [str(pip_path), "install", "-q"] + deps,
        cwd=app_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]Erro ao instalar dependências: {result.stderr}[/]")
        raise typer.Exit(1)
    console.print("[green]✓ Dependências instaladas[/]")

    # Step 3: Create .env from .env.example if not exists
    env_file = app_path / ".env"
    env_example = app_path / ".env.example"
    if not env_file.exists() and env_example.exists():
        console.print("\n[cyan]3. Criando .env a partir de .env.example...[/]")
        import shutil
        shutil.copy(env_example, env_file)
        console.print("[green]✓ .env criado[/]")
        console.print("[yellow]⚠ Edite .env com suas credenciais de banco![/]")
    else:
        console.print("\n[cyan]3. .env já existe[/]")

    # Step 4: Run uvicorn
    console.print(f"\n[cyan]4. Iniciando aplicação na porta {port}...[/]")
    console.print(f"[bold green]URL: http://127.0.0.1:{port}[/]")
    console.print("[dim]Pressione Ctrl+C para parar[/]\n")

    # Open browser after a short delay
    if not no_browser:
        def open_browser():
            time.sleep(2)
            webbrowser.open(f"http://127.0.0.1:{port}")

        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    try:
        subprocess.run(
            [
                str(python_path), "-m", "uvicorn",
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", str(port),
            ],
            cwd=app_path,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Aplicação encerrada.[/]")


@app.command("spec-proposal")
def spec_proposal(
    project_name: str = typer.Argument(
        ...,
        help="Nome do projeto no MongoDB (ex: Linkpay_ADM)",
    ),
    output: Path = typer.Option(
        Path("output/openspec/changes"),
        "--output",
        "-o",
        help="Diretório base para proposals (default: output/openspec/changes)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Apenas mostra próximo elemento sem gerar proposal",
    ),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Modo automático: gera, aplica e arquiva sem pausa",
    ),
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-P",
        help="LLM provider (anthropic, openai, ollama)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo específico (usa default do provider se não fornecido)",
    ),
) -> None:
    """
    Conversão incremental: gera proposal OpenSpec para próximo elemento.

    Segue ordem topológica e usa specs arquivadas como contexto.
    Cada proposal documenta decisões de mapeamento para elementos futuros.

    Fluxo:
        1. Busca próximo elemento pendente (por ordem topológica)
        2. Carrega specs das dependências já convertidas
        3. Gera proposal via LLM
        4. Salva em output/openspec/changes/{element}-spec/

    Modo automático (--auto):
        Após gerar, executa automaticamente:
        - openspec validate
        - openspec apply
        - openspec archive

    Exemplos:
        wxcode spec-proposal Linkpay_ADM --dry-run
        wxcode spec-proposal Linkpay_ADM
        wxcode spec-proposal Linkpay_ADM --auto
    """
    from pathlib import Path as PathLib

    async def _spec_proposal() -> None:
        from wxcode.config import get_settings
        from wxcode.database import init_db, close_db
        from wxcode.llm_converter import (
            ConversionTracker,
            SpecContextLoader,
            ProposalGenerator,
        )
        from wxcode.llm_converter.providers import create_provider

        settings = get_settings()
        client = await init_db()
        db = client[settings.mongodb_database]

        try:
            # Inicializar componentes
            tracker = ConversionTracker(db)
            # Specs ficam em output/openspec/specs (derivado do output path)
            specs_dir = output.parent / "specs"  # output/openspec/specs
            spec_loader = SpecContextLoader(specs_dir)

            # Buscar próximo item (pode ser element, procedure, class)
            console.print(f"\n[cyan]Buscando próximo elemento pendente em {project_name}...[/]")
            item = await tracker.get_next_pending_item(project_name)

            if not item:
                stats = await tracker.get_stats(project_name)
                console.print("[green]✓ Todos os elementos já foram convertidos![/]")
                console.print(f"[dim]Stats: {stats}[/]")
                return

            # Mostrar informações do item
            console.print(Panel(
                f"[bold]Próximo elemento:[/] {item.name}\n"
                f"[bold]Tipo:[/] {item.item_type}\n"
                f"[bold]Collection:[/] {item.collection}\n"
                f"[bold]Camada:[/] {item.layer or 'não definida'}\n"
                f"[bold]Ordem topológica:[/] {item.topological_order}",
                title="🎯 Elemento a Converter",
            ))

            if dry_run:
                pending = await tracker.get_pending_count(project_name)
                console.print(f"\n[dim]Elementos pendentes: {pending}[/]")
                console.print("[yellow]Modo dry-run: nenhuma ação executada.[/]")
                return

            # Por enquanto só suporta pages (elements collection)
            if item.collection != "elements":
                console.print(f"\n[yellow]⚠ Conversão de {item.item_type} ainda não suportada.[/]")
                console.print(f"[dim]Próximo item seria: {item.name} (ordem: {item.topological_order})[/]")
                console.print("[dim]Use convert-procedure para procedures ou implemente suporte adicional.[/]")
                return

            # Carregar Element do doc
            from wxcode.models import Element
            element = Element(**item.doc)

            # Carregar specs das dependências
            console.print("\n[cyan]Carregando specs das dependências...[/]")
            specs_content, missing_deps = spec_loader.load_dependency_specs(element)
            context = spec_loader.format_context(specs_content, missing_deps)

            if specs_content:
                console.print(f"[green]✓ {len(specs_content)} specs carregadas[/]")
            if missing_deps:
                console.print(f"[yellow]⚠ {len(missing_deps)} dependências sem spec: {', '.join(missing_deps[:3])}...[/]")

            # Criar provider e gerador
            console.print(f"\n[cyan]Gerando proposal via LLM ({provider})...[/]")
            llm_provider = create_provider(provider, model=model)
            generator = ProposalGenerator(llm_provider, output)

            # Gerar proposal
            with console.status("[bold cyan]Chamando LLM..."):
                proposal, proposal_path = await generator.generate_and_save(element, context)

            console.print(f"[green]✓ Proposal gerada em: {proposal_path}[/]")

            # Marcar status
            await tracker.mark_proposal_generated(str(element.id))

            # Listar arquivos criados
            console.print("\n[bold]Arquivos criados:[/]")
            for f in proposal_path.rglob("*.md"):
                console.print(f"  - {f.relative_to(proposal_path)}")

            if auto:
                console.print("\n[cyan]Modo automático: executando validate, apply, archive...[/]")

                import subprocess

                spec_id = f"{proposal.element_name}-spec"

                # Validate
                console.print(f"[dim]$ openspec validate {spec_id}[/]")
                result = subprocess.run(["openspec", "validate", spec_id], capture_output=True, text=True)
                if result.returncode != 0:
                    console.print(f"[red]Erro na validação:[/]\n{result.stderr}")
                    return
                console.print("[green]✓ Validação OK[/]")

                # Apply (placeholder - implementar com skill)
                console.print(f"[yellow]⚠ Apply não implementado automaticamente[/]")
                console.print(f"[dim]Execute manualmente: /openspec:apply {spec_id}[/]")

            else:
                # Calcular diretório base do openspec (output/openspec ou similar)
                openspec_dir = output.parent  # output/openspec
                console.print("\n[bold]Próximos passos:[/]")
                console.print(f"  1. Revisar proposal em {proposal_path}")
                console.print(f"  2. cd {openspec_dir.parent} && openspec validate {proposal.element_name}-spec")
                console.print(f"  3. Implementar código conforme tasks.md")
                console.print(f"  4. cd {openspec_dir.parent} && openspec archive {proposal.element_name}-spec")

        finally:
            await close_db(client)

    asyncio.run(_spec_proposal())


@app.command("conversion-skip")
def conversion_skip(
    project_name: str = typer.Argument(
        ...,
        help="Nome do projeto no MongoDB",
    ),
    types: list[str] = typer.Option(
        ["class", "procedure"],
        "--type",
        "-t",
        help="Tipos a pular: class, procedure, page",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Reseta status para pending ao invés de skip",
    ),
) -> None:
    """
    Pula tipos de elementos na conversão incremental.

    Útil para testar spec-proposal com pages sem converter classes/procedures primeiro.

    Exemplos:
        wxcode conversion-skip Linkpay_ADM                    # Pula classes e procedures
        wxcode conversion-skip Linkpay_ADM -t class           # Pula só classes
        wxcode conversion-skip Linkpay_ADM -t procedure       # Pula só procedures
        wxcode conversion-skip Linkpay_ADM --reset            # Reseta classes e procedures
    """
    async def _skip() -> None:
        from wxcode.config import get_settings
        from wxcode.database import init_db, close_db
        from wxcode.llm_converter import ConversionTracker

        settings = get_settings()
        client = await init_db()
        db = client[settings.mongodb_database]

        try:
            tracker = ConversionTracker(db)

            if reset:
                console.print(f"[cyan]Resetando status de {types} para pending...[/]")
                counts = await tracker.reset_by_type(project_name, types)
                action = "resetados"
            else:
                console.print(f"[cyan]Marcando {types} como skipped...[/]")
                counts = await tracker.skip_by_type(project_name, types)
                action = "pulados"

            if not counts:
                console.print("[yellow]Projeto não encontrado ou nenhum item atualizado.[/]")
                return

            console.print(f"[green]✓ Items {action}:[/]")
            for item_type, count in counts.items():
                console.print(f"  - {item_type}: {count}")

            # Mostrar próximo item
            item = await tracker.get_next_pending_item(project_name)
            if item:
                console.print(f"\n[bold]Próximo item:[/] {item.name} ({item.item_type}, ordem: {item.topological_order})")

        finally:
            await close_db(client)

    asyncio.run(_skip())


@app.command("seed-stacks")
def seed_stacks_command(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Re-seed all stacks even if unchanged",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
) -> None:
    """
    Seed stack configurations from YAML files to MongoDB.

    Reads all YAML files from src/wxcode/data/stacks/ and upserts
    them to the MongoDB stacks collection. Run this after modifying
    stack YAML files to update the database.

    Note: Stacks are also seeded automatically on application startup.

    Examples:
        wxcode seed-stacks
        wxcode seed-stacks --force
        wxcode seed-stacks -v
    """
    from wxcode.database import init_db, close_db
    from wxcode.services import seed_stacks

    async def _seed() -> None:
        client = await init_db()
        try:
            count = await seed_stacks(force=force)
            if verbose:
                console.print(f"[green]Seeded {count} stacks from YAML files[/]")
            else:
                console.print(f"[green]{count} stacks seeded[/]")
        finally:
            await close_db(client)

    asyncio.run(_seed())


@app.command("list-elements")
def list_elements(
    project_name: str = typer.Argument(
        ...,
        help="Nome do projeto no MongoDB",
    ),
    layer: Optional[str] = typer.Option(
        None,
        "--layer",
        "-l",
        help="Filtrar por camada: schema, domain, business, ui",
    ),
    item_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filtrar por tipo: table, class, procedure, page",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filtrar por status: pending, converted, skipped",
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-n",
        help="Número máximo de elementos",
    ),
    with_order_only: bool = typer.Option(
        False,
        "--with-order",
        help="Apenas elementos com ordem topológica definida",
    ),
) -> None:
    """
    Lista elementos em ordem topológica (saída JSON).

    Consulta todas as collections (elements, procedures, classes)
    e retorna ordenado por topological_order.

    Exemplos:
        wxcode list-elements Linkpay_ADM
        wxcode list-elements Linkpay_ADM --layer business
        wxcode list-elements Linkpay_ADM --type procedure --limit 50
        wxcode list-elements Linkpay_ADM --status pending
        wxcode list-elements Linkpay_ADM --with-order
    """
    import json

    async def _list() -> None:
        from wxcode.config import get_settings
        from wxcode.database import init_db, close_db

        settings = get_settings()
        client = await init_db()
        db = client[settings.mongodb_database]

        try:
            project = await db.projects.find_one({"name": project_name})
            if not project:
                console.print(json.dumps({"error": "Projeto não encontrado"}))
                return

            project_id = project["_id"]
            all_items: list[dict] = []

            # Construir filtros
            def build_filter(use_dbref: bool = False) -> dict:
                f: dict = {}
                if use_dbref:
                    f["project_id.$id"] = project_id
                else:
                    f["project_id"] = project_id

                if layer:
                    f["layer"] = layer

                if status:
                    if status == "pending":
                        f["$or"] = [
                            {"conversion.status": "pending"},
                            {"conversion.status": {"$exists": False}},
                            {"conversion": {"$exists": False}},
                        ]
                    else:
                        f["conversion.status"] = status

                if with_order_only:
                    f["topological_order"] = {"$ne": None}

                return f

            # 1. Elements (pages) - usa DBRef
            if item_type is None or item_type == "page":
                cursor = db.elements.find(build_filter(use_dbref=True))
                async for doc in cursor:
                    all_items.append({
                        "name": doc.get("source_name"),
                        "type": "page",
                        "layer": doc.get("layer"),
                        "topological_order": doc.get("topological_order"),
                        "status": doc.get("conversion", {}).get("status", "pending"),
                        "source_file": doc.get("source_file"),
                    })

            # 2. Procedures - usa project_id direto
            if item_type is None or item_type == "procedure":
                cursor = db.procedures.find(build_filter(use_dbref=False))
                async for doc in cursor:
                    all_items.append({
                        "name": doc.get("name"),
                        "type": "procedure",
                        "layer": doc.get("layer"),
                        "topological_order": doc.get("topological_order"),
                        "status": doc.get("conversion", {}).get("status", "pending"),
                        "source_file": doc.get("source_file"),
                    })

            # 3. Classes - usa project_id direto
            if item_type is None or item_type == "class":
                cursor = db.class_definitions.find(build_filter(use_dbref=False))
                async for doc in cursor:
                    all_items.append({
                        "name": doc.get("name"),
                        "type": "class",
                        "layer": doc.get("layer"),
                        "topological_order": doc.get("topological_order"),
                        "status": doc.get("conversion", {}).get("status", "pending"),
                        "source_file": doc.get("source_file"),
                    })

            # 4. Tables (embedded no DatabaseSchema)
            if item_type is None or item_type == "table":
                schema_doc = await db.schemas.find_one({"project_id": project_id})
                if schema_doc and "tables" in schema_doc:
                    for table in schema_doc["tables"]:
                        table_layer = table.get("layer")
                        table_order = table.get("topological_order")
                        table_status = table.get("conversion_status", "pending")

                        # Aplicar filtros
                        if layer and table_layer != layer:
                            continue
                        if status:
                            if status == "pending" and table_status not in (None, "pending"):
                                continue
                            elif status != "pending" and table_status != status:
                                continue
                        if with_order_only and table_order is None:
                            continue

                        all_items.append({
                            "name": table.get("name"),
                            "type": "table",
                            "layer": table_layer,
                            "topological_order": table_order,
                            "status": table_status or "pending",
                            "source_file": schema_doc.get("source_file"),
                        })

            # Ordenar por topological_order (None vai pro final)
            all_items.sort(key=lambda x: (
                x["topological_order"] is None,
                x["topological_order"] or 0
            ))

            # Aplicar limite
            all_items = all_items[:limit]

            # Output JSON
            result = {
                "project": project_name,
                "total": len(all_items),
                "filters": {
                    "layer": layer,
                    "type": item_type,
                    "status": status,
                    "with_order_only": with_order_only,
                },
                "items": all_items,
            }

            console.print(json.dumps(result, indent=2, ensure_ascii=False))

        finally:
            await close_db(client)

    asyncio.run(_list())


if __name__ == "__main__":
    app()
