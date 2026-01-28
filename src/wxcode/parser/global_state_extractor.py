"""
Extrator de declarações de estado global em projetos WinDev/WebDev.

Este módulo parseia declarações GLOBAL em diferentes contextos (Project Code,
Set of Procedures, Pages) e extrai variáveis globais mantendo tipos WLanguage
originais (stack-agnostic).
"""

from dataclasses import dataclass
from enum import Enum


class Scope(Enum):
    """Escopo de uma variável global."""

    APP = "app"  # Project Code (type_code: 0)
    MODULE = "module"  # Set of Procedures (type_code: 31)
    REQUEST = "request"  # Page (type_code: 38, 60)


@dataclass
class GlobalVariable:
    """
    Variável global extraída de código WLanguage.

    IMPORTANTE: Esta classe mantém tipos WLanguage originais, sem mapeamento
    para nenhum stack específico (stack-agnostic IR).
    """

    name: str
    """Nome da variável (ex: 'gCnn', 'gjsonParametros')"""

    wlanguage_type: str
    """Tipo WLanguage original (ex: 'Connection', 'JSON', 'string')"""

    default_value: str | None
    """Valor default em sintaxe WLanguage (ex: '20', 'True', None)"""

    scope: Scope
    """Escopo da variável (APP, MODULE, REQUEST)"""

    source_element: str
    """Elemento onde foi declarada (ex: 'Linkpay_ADM.wwp', 'ServerProcedures.wdg')"""

    source_type_code: int
    """Tipo do elemento fonte (0=Project, 31=WDG, 38=Page)"""


@dataclass
class InitializationBlock:
    """
    Bloco de código de inicialização em WLanguage.

    Contém código executado após declarações GLOBAL (ex: HOpenConnection,
    inicialização de variáveis, configurações).
    """

    code: str
    """Código WLanguage original do bloco de inicialização"""

    dependencies: list[str]
    """Nomes das variáveis globais referenciadas neste bloco"""

    order: int
    """Ordem de execução (0=primeiro, 1=segundo, etc.)"""


class GlobalStateExtractor:
    """
    Extrator de declarações GLOBAL e código de inicialização.

    Este extrator parseia código WLanguage e identifica:
    - Declarações GLOBAL de variáveis
    - Código de inicialização após blocos GLOBAL
    - Dependências entre blocos de inicialização

    IMPORTANTE: Mantém tipos WLanguage originais (stack-agnostic).
    """

    # Padrões regex para parsing de código WLanguage
    import re

    # Detecta bloco GLOBAL completo
    GLOBAL_BLOCK_PATTERN = re.compile(
        r"^\s*GLOBAL\s*$\s*(.*?)(?=^(?:PROCEDURE|CONSTANT|END|$))",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )

    # Parseia declaração individual: "gCnn is Connection"
    # Permite tipos compostos como "array of string"
    SINGLE_DECLARATION_PATTERN = re.compile(
        r"^\s*(\w+)\s+(?:is|est)\s+(.+?)(?:\s*=\s*(.+?))?$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Parseia declaração com default value: "gnTimeout is int = 20"
    # Permite tipos compostos como "array of string"
    DECLARATION_WITH_DEFAULT_PATTERN = re.compile(
        r"^\s*(\w+)\s+(?:is|est)\s+(.+?)\s*=\s*(.+?)$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Parseia múltiplas variáveis: "a, b, c are string"
    # Permite tipos compostos como "array of string"
    MULTI_DECLARATION_PATTERN = re.compile(
        r"^\s*([\w\s,]+)\s+(?:are|sont)\s+(.+?)$",
        re.MULTILINE | re.IGNORECASE,
    )

    @staticmethod
    def _determine_scope(type_code: int) -> Scope:
        """
        Determina escopo baseado no type_code do elemento.

        Args:
            type_code: Código do tipo do elemento WinDev

        Returns:
            Scope apropriado para o elemento
        """
        if type_code == 0:  # Project Code
            return Scope.APP
        elif type_code == 31:  # Set of Procedures (WDG)
            return Scope.MODULE
        elif type_code in (38, 60):  # Page events, Cell events
            return Scope.REQUEST
        else:
            # Default: REQUEST para elementos desconhecidos
            return Scope.REQUEST

    def extract_variables(
        self, code: str, type_code: int, source: str
    ) -> list[GlobalVariable]:
        """
        Extrai declarações de variáveis globais do código WLanguage.

        Args:
            code: Código WLanguage contendo declarações GLOBAL
            type_code: Tipo do elemento fonte (0, 31, 38, etc.)
            source: Nome do elemento fonte (ex: 'Linkpay_ADM.wwp')

        Returns:
            Lista de GlobalVariable extraídas

        Examples:
            >>> extractor = GlobalStateExtractor()
            >>> code = '''
            ... GLOBAL
            ...     gCnn is Connection
            ...     gnTimeout is int = 20
            ...     a, b, c are string
            ... '''
            >>> variables = extractor.extract_variables(code, 0, "Project.wwp")
            >>> len(variables)
            5
        """
        variables = []
        scope = self._determine_scope(type_code)

        # Encontra bloco GLOBAL
        global_match = self.GLOBAL_BLOCK_PATTERN.search(code)
        if not global_match:
            return variables

        global_block = global_match.group(1)

        # Processa cada linha do bloco GLOBAL
        for line in global_block.split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Tenta múltiplas declarações primeiro: "a, b, c are string"
            multi_match = self.MULTI_DECLARATION_PATTERN.match(line)
            if multi_match:
                names_str = multi_match.group(1)
                wl_type = multi_match.group(2).strip()

                # Divide nomes separados por vírgula
                names = [n.strip() for n in names_str.split(",")]
                for name in names:
                    variables.append(
                        GlobalVariable(
                            name=name,
                            wlanguage_type=wl_type,
                            default_value=None,
                            scope=scope,
                            source_element=source,
                            source_type_code=type_code,
                        )
                    )
                continue

            # Tenta declaração com default value: "gnTimeout is int = 20"
            default_match = self.DECLARATION_WITH_DEFAULT_PATTERN.match(line)
            if default_match:
                name = default_match.group(1).strip()
                wl_type = default_match.group(2).strip()
                default_value = default_match.group(3).strip()

                variables.append(
                    GlobalVariable(
                        name=name,
                        wlanguage_type=wl_type,
                        default_value=default_value,
                        scope=scope,
                        source_element=source,
                        source_type_code=type_code,
                    )
                )
                continue

            # Tenta declaração simples: "gCnn is Connection"
            single_match = self.SINGLE_DECLARATION_PATTERN.match(line)
            if single_match:
                name = single_match.group(1).strip()
                wl_type = single_match.group(2).strip()
                default_value = (
                    single_match.group(3).strip() if single_match.group(3) else None
                )

                variables.append(
                    GlobalVariable(
                        name=name,
                        wlanguage_type=wl_type,
                        default_value=default_value,
                        scope=scope,
                        source_element=source,
                        source_type_code=type_code,
                    )
                )

        return variables

    def extract_initialization(self, code: str) -> list[InitializationBlock]:
        """
        Extrai blocos de código de inicialização após declarações GLOBAL.

        Identifica código executado após o bloco GLOBAL (ex: HOpenConnection,
        configurações, inicialização de variáveis).

        Args:
            code: Código WLanguage contendo declarações GLOBAL e inicialização

        Returns:
            Lista de InitializationBlock extraídos

        Examples:
            >>> extractor = GlobalStateExtractor()
            >>> code = '''
            ... GLOBAL
            ...     gCnn is Connection
            ...
            ... IF HOpenConnection(gCnn) = False THEN
            ...     EndProgram("Erro")
            ... END
            ... '''
            >>> blocks = extractor.extract_initialization(code)
            >>> len(blocks)
            1
            >>> 'gCnn' in blocks[0].dependencies
            True
        """
        initialization_blocks = []

        # Encontra fim do bloco GLOBAL
        global_match = self.GLOBAL_BLOCK_PATTERN.search(code)
        if not global_match:
            return initialization_blocks

        # Código após bloco GLOBAL
        global_end_pos = global_match.end()
        init_code = code[global_end_pos:].strip()

        if not init_code:
            return initialization_blocks

        # Detecta blocos de inicialização (IF, SWITCH, atribuições, chamadas de função)
        # Por simplicidade, extrai todo o código após GLOBAL como um único bloco
        # TODO: Futuramente, parsear blocos individuais (IF, SWITCH, etc.)

        # Extrai variáveis globais referenciadas (nomes começando com 'g')
        import re

        var_pattern = re.compile(r"\b(g[A-Z]\w*)\b")
        dependencies = list(set(var_pattern.findall(init_code)))

        initialization_blocks.append(
            InitializationBlock(code=init_code, dependencies=dependencies, order=0)
        )

        return initialization_blocks
