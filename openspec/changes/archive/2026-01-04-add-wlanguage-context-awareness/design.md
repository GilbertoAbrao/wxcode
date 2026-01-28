# Design: add-wlanguage-context-awareness

## Overview

Este documento detalha a arquitetura para adicionar consciência de contexto WLanguage ao wxcode, focando em três aspectos críticos: DataBinding, Buffer Global e Funções H*.

## Architectural Context

### Problema: Paradigma Incompatível

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WLANGUAGE (WinDev/WebDev)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐     FileToScreen()      ┌──────────────────┐       │
│  │ BUFFER GLOBAL   │ ───────────────────────▶│ UI Controls      │       │
│  │ (por tabela)    │                         │ com Binding      │       │
│  │                 │ ◀───────────────────────│                  │       │
│  │ CLIENTE.nome    │     ScreenToFile()      │ EDT_Nome         │       │
│  │ CLIENTE.cpf     │                         │ EDT_CPF          │       │
│  └─────────────────┘                         └──────────────────┘       │
│         ▲                                                               │
│         │ HReadSeekFirst / HModify / etc.                               │
│         ▼                                                               │
│  ┌─────────────────┐                                                    │
│  │ HYPERFILE DB    │                                                    │
│  └─────────────────┘                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          PYTHON (FastAPI + Jinja2)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  @router.get("/cliente/{id}")                                           │
│  async def get_cliente(id: int):                                        │
│      cliente = await db.find_one({"_id": id})  # Query explícita        │
│      return templates.TemplateResponse(                                  │
│          "form.html",                                                    │
│          {"cliente": cliente}  # Contexto explícito                      │
│      )                                                                   │
│                                                                          │
│  # NÃO existe buffer global - cada request é independente               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. DataBindingInfo Model

```python
# models/control.py - Adições

class DataBindingType(str, Enum):
    """Tipos de binding suportados."""
    SIMPLE = "simple"       # TABLE.FIELD direto
    COMPLEX = "complex"     # TABLE1.FIELD via TABLE2.FK
    VARIABLE = "variable"   # Binding com variável WLanguage


class DataBindingInfo(BaseModel):
    """Informação de binding entre controle e dados."""

    binding_type: DataBindingType = Field(
        default=DataBindingType.SIMPLE,
        description="Tipo de binding"
    )

    # Binding simples: TABLE.FIELD
    table_name: Optional[str] = Field(
        default=None,
        description="Nome da tabela vinculada (ex: CLIENTE)"
    )
    field_name: Optional[str] = Field(
        default=None,
        description="Nome do campo vinculado (ex: nome)"
    )

    # Binding complexo: caminho através de FKs
    binding_path: Optional[list[str]] = Field(
        default=None,
        description="Caminho de binding complexo (ex: ['PEDIDO', 'cliente_id', 'CLIENTE', 'nome'])"
    )

    # Binding com variável
    variable_name: Optional[str] = Field(
        default=None,
        description="Nome da variável vinculada"
    )

    # Metadados
    source: str = Field(
        default="pdf",
        description="Fonte da informação: 'pdf' ou 'wwh'"
    )
    raw_value: Optional[str] = Field(
        default=None,
        description="Valor bruto extraído (para debug)"
    )

    @property
    def full_binding(self) -> str:
        """Retorna binding completo como string."""
        if self.binding_type == DataBindingType.VARIABLE:
            return f":{self.variable_name}"
        elif self.table_name and self.field_name:
            return f"{self.table_name}.{self.field_name}"
        elif self.binding_path:
            return " -> ".join(self.binding_path)
        return ""
```

### 2. Extração de Binding do PDF

O binding aparece no PDF de documentação como "Linked item" ou "File link":

```
┌─────────────────────────────────────────────────────────────┐
│  Control: EDT_Nome                                          │
│  Type: Edit control                                         │
│  ─────────────────────────────────────────────────────────  │
│  Linked item: CLIENTE.nome                                  │
│  Input type: Text                                           │
│  Width: 200                                                 │
│  Height: 24                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Parser atualizado**:

```python
# parser/pdf_element_parser.py - Adições

BINDING_PATTERNS = [
    r"Linked item\s*:\s*(.+)",
    r"File link\s*:\s*(.+)",
    r"Rubrique fichier\s*:\s*(.+)",  # Francês
    r"Binding\s*:\s*(.+)",
]

def extract_binding(self, text: str) -> Optional[DataBindingInfo]:
    """Extrai informação de binding do texto do PDF."""
    for pattern in BINDING_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_value = match.group(1).strip()
            return self._parse_binding_value(raw_value)
    return None

def _parse_binding_value(self, value: str) -> DataBindingInfo:
    """Parseia o valor de binding."""
    # Binding com variável: :VariableName
    if value.startswith(':'):
        return DataBindingInfo(
            binding_type=DataBindingType.VARIABLE,
            variable_name=value[1:],
            raw_value=value
        )

    # Binding simples: TABLE.FIELD
    if '.' in value and ' ' not in value:
        parts = value.split('.', 1)
        return DataBindingInfo(
            binding_type=DataBindingType.SIMPLE,
            table_name=parts[0],
            field_name=parts[1],
            raw_value=value
        )

    # Binding complexo: analisar caminho
    # Formato: TABLE1.FIELD1 via TABLE2
    # TODO: implementar parsing complexo
    return DataBindingInfo(
        binding_type=DataBindingType.COMPLEX,
        binding_path=value.split(),
        raw_value=value
    )
```

### 3. Categorização de Funções H*

```python
# transpiler/hyperfile_categories.py

from enum import Enum
from dataclasses import dataclass

class BufferBehavior(Enum):
    """Comportamento da função em relação ao buffer."""
    MODIFIES_BUFFER = "modifies"     # Carrega dados no buffer
    READS_BUFFER = "reads"           # Usa dados já no buffer
    PERSISTS_BUFFER = "persists"     # Salva buffer no banco
    INDEPENDENT = "independent"       # Não afeta buffer


@dataclass
class HFunctionInfo:
    """Informação sobre uma função H*."""
    name: str
    behavior: BufferBehavior
    description: str
    mongodb_equivalent: str
    needs_llm: bool = False
    notes: Optional[str] = None


# Catálogo completo de funções H*
HFUNCTION_CATALOG = {
    # === Funções que MODIFICAM o buffer ===
    'HReadFirst': HFunctionInfo(
        name='HReadFirst',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Carrega primeiro registro no buffer',
        mongodb_equivalent='find().limit(1)',
    ),
    'HReadNext': HFunctionInfo(
        name='HReadNext',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Carrega próximo registro no buffer',
        mongodb_equivalent='cursor.__next__()',
        needs_llm=True,
        notes='Requer contexto de iteração'
    ),
    'HReadSeekFirst': HFunctionInfo(
        name='HReadSeekFirst',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Busca por chave e carrega no buffer',
        mongodb_equivalent='find_one({"field": value})',
    ),
    'HReset': HFunctionInfo(
        name='HReset',
        behavior=BufferBehavior.MODIFIES_BUFFER,
        description='Limpa buffer para novo registro',
        mongodb_equivalent='{}  # dict vazio',
    ),

    # === Funções que LEEM do buffer ===
    'HFound': HFunctionInfo(
        name='HFound',
        behavior=BufferBehavior.READS_BUFFER,
        description='Verifica se último read encontrou registro',
        mongodb_equivalent='result is not None',
    ),
    'HOut': HFunctionInfo(
        name='HOut',
        behavior=BufferBehavior.READS_BUFFER,
        description='Verifica se ponteiro saiu dos limites',
        mongodb_equivalent='result is None',
    ),

    # === Funções que PERSISTEM o buffer ===
    'HAdd': HFunctionInfo(
        name='HAdd',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Insere buffer como novo registro',
        mongodb_equivalent='insert_one(data)',
    ),
    'HModify': HFunctionInfo(
        name='HModify',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Atualiza registro atual com buffer',
        mongodb_equivalent='update_one({"_id": id}, {"$set": data})',
    ),
    'HDelete': HFunctionInfo(
        name='HDelete',
        behavior=BufferBehavior.PERSISTS_BUFFER,
        description='Deleta registro atual',
        mongodb_equivalent='delete_one({"_id": id})',
    ),

    # === Funções INDEPENDENTES do buffer ===
    'HExecuteQuery': HFunctionInfo(
        name='HExecuteQuery',
        behavior=BufferBehavior.INDEPENDENT,
        description='Executa query SQL',
        mongodb_equivalent='aggregate() ou find()',
        needs_llm=True,
        notes='Requer análise da query SQL'
    ),
    'HNbRec': HFunctionInfo(
        name='HNbRec',
        behavior=BufferBehavior.INDEPENDENT,
        description='Conta registros',
        mongodb_equivalent='count_documents({})',
    ),
}
```

### 4. Atualização do Dependency Extractor

```python
# parser/dependency_extractor.py - Adições

@dataclass
class TableUsage:
    """Uso de uma tabela em código."""
    table_name: str
    usage_type: str  # 'read', 'write', 'binding'
    context: str     # Onde é usado (procedure, event, binding)


class DependencyExtractor:
    # ... código existente ...

    def extract_table_bindings(
        self,
        controls: list[Control]
    ) -> list[TableUsage]:
        """Extrai uso de tabelas via binding de controles."""
        usages = []
        for control in controls:
            if control.data_binding and control.data_binding.table_name:
                usages.append(TableUsage(
                    table_name=control.data_binding.table_name,
                    usage_type='binding',
                    context=f"control:{control.name}"
                ))
        return usages
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE DE ENRIQUECIMENTO                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. PDF Parser                                                           │
│     │                                                                    │
│     ├─▶ Extrai "Linked item" do texto do controle                       │
│     │                                                                    │
│     └─▶ DataBindingInfo { table: "CLIENTE", field: "nome" }             │
│                                                                          │
│  2. Element Enricher                                                     │
│     │                                                                    │
│     ├─▶ Combina binding do PDF com dados do .wwh                        │
│     │                                                                    │
│     └─▶ Control.data_binding = DataBindingInfo(...)                     │
│                                                                          │
│  3. Dependency Extractor                                                 │
│     │                                                                    │
│     ├─▶ Coleta tabelas usadas via binding                               │
│     │                                                                    │
│     └─▶ Element.dependencies.data_files += ["CLIENTE"]                  │
│                                                                          │
│  4. Analyzer                                                             │
│     │                                                                    │
│     └─▶ Adiciona arestas UI → Table no grafo de dependências            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Trade-offs

| Decisão | Alternativas | Justificativa |
|---------|--------------|---------------|
| PDF como fonte primária de binding | Decodificar internal_properties | PDF é texto legível, internal_properties é base64 proprietário |
| Modelo separado DataBindingInfo | Campos soltos no Control | Encapsulamento, tipagem forte, extensibilidade |
| Catálogo estático de funções H* | Detecção dinâmica | Funções são finitas e documentadas, catálogo é mais confiável |
| Marcar needs_llm por função | Tentar converter tudo | Algumas conversões são contextualmente ambíguas |

## Migration Strategy

1. **Fase 1**: Adicionar models sem quebrar existente
2. **Fase 2**: Atualizar PDF parser para extrair binding
3. **Fase 3**: Atualizar enricher para popular data_binding
4. **Fase 4**: Atualizar dependency extractor
5. **Fase 5**: Criar catálogo de funções H*

Todas as fases são aditivas e não quebram funcionalidade existente.

## References

- [DataBinding Property - PC SOFT](https://doc.windev.com/en-US/?2510060)
- [FileToScreen Function - PC SOFT](https://doc.windev.com/en-US/?3044210)
- [HReadSeekFirst Function - PC SOFT](https://doc.windev.com/en-US/?3044036)
- [Using HAlias - wxBlog](https://blog.wxperts.com/2018/10/28/using-halias-to-have-2-active-record-buffers-for-the-same-file/)
