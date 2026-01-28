"""
Contexto de estado global (IR stack-agnostic).

Este módulo define o IR (Intermediate Representation) para estado global
extraído de projetos WinDev/WebDev. O contexto mantém tipos WLanguage originais
e é completamente independente do stack target.
"""

from dataclasses import dataclass, field

from wxcode.parser.global_state_extractor import (
    GlobalVariable,
    InitializationBlock,
    Scope,
)


@dataclass
class GlobalStateContext:
    """
    IR (Intermediate Representation) para estado global de um projeto.

    Este contexto é 100% stack-agnostic, contendo apenas:
    - Variáveis globais com tipos WLanguage originais
    - Blocos de inicialização em código WLanguage original
    - Métodos de consulta e filtragem

    IMPORTANTE: NÃO contém nenhum tipo ou código específico de Python, Node, Go, etc.
    O mapeamento para stack target é responsabilidade dos generators.
    """

    variables: list[GlobalVariable] = field(default_factory=list)
    """Lista de todas as variáveis globais extraídas"""

    initialization_blocks: list[InitializationBlock] = field(default_factory=list)
    """Lista de blocos de código de inicialização"""

    def get_by_scope(self, scope: Scope) -> list[GlobalVariable]:
        """
        Filtra variáveis por escopo.

        Args:
            scope: Escopo desejado (APP, MODULE, REQUEST)

        Returns:
            Lista de variáveis do escopo especificado
        """
        return [v for v in self.variables if v.scope == scope]

    def get_by_source(self, source: str) -> list[GlobalVariable]:
        """
        Filtra variáveis por elemento fonte.

        Args:
            source: Nome do elemento fonte (ex: 'Linkpay_ADM.wwp')

        Returns:
            Lista de variáveis declaradas no elemento especificado
        """
        return [v for v in self.variables if v.source_element == source]

    def get_variable(self, name: str) -> GlobalVariable | None:
        """
        Busca variável por nome.

        Args:
            name: Nome da variável (ex: 'gCnn')

        Returns:
            GlobalVariable se encontrada, None caso contrário
        """
        for var in self.variables:
            if var.name == name:
                return var
        return None

    def has_variable(self, name: str) -> bool:
        """
        Verifica se uma variável existe no contexto.

        Args:
            name: Nome da variável

        Returns:
            True se variável existe, False caso contrário
        """
        return self.get_variable(name) is not None

    @classmethod
    def from_extractor_results(
        cls,
        variables: list[GlobalVariable],
        initialization_blocks: list[InitializationBlock],
    ) -> "GlobalStateContext":
        """
        Cria contexto a partir de resultados do GlobalStateExtractor.

        Args:
            variables: Lista de variáveis extraídas
            initialization_blocks: Lista de blocos de inicialização

        Returns:
            Novo GlobalStateContext
        """
        return cls(variables=variables, initialization_blocks=initialization_blocks)

    def merge(self, other: "GlobalStateContext") -> "GlobalStateContext":
        """
        Mescla outro contexto neste contexto.

        Útil para combinar variáveis de múltiplos elementos (Project Code + WDGs).

        Args:
            other: Outro contexto a ser mesclado

        Returns:
            Novo contexto contendo variáveis de ambos
        """
        return GlobalStateContext(
            variables=self.variables + other.variables,
            initialization_blocks=self.initialization_blocks
            + other.initialization_blocks,
        )

    def __len__(self) -> int:
        """Retorna número de variáveis no contexto."""
        return len(self.variables)

    def __bool__(self) -> bool:
        """Contexto é truthy se contém variáveis."""
        return len(self.variables) > 0
