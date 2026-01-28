# ADR-003: Pipeline de Conversão em Camadas

## Status

Aceito

## Contexto

A conversão de um projeto WinDev completo não pode ser feita elemento a elemento de forma isolada, pois:
- Elementos dependem uns dos outros
- Converter uma página sem ter convertido as classes que ela usa resulta em erros
- A arquitetura final precisa ser coerente

## Decisão

Adotamos um **pipeline de conversão em camadas**, seguindo ordem topológica:

### Camadas (em ordem)

```
1. SCHEMA      → Modelo de dados (HyperFile → SQLAlchemy)
2. DOMAIN      → Entidades de domínio (Classes → Python classes)
3. BUSINESS    → Lógica de negócio (Procedures → Services)
4. API         → Endpoints REST (wdrest → FastAPI routes)
5. UI          → Interface (Pages → Jinja2 templates)
```

### Fluxo de Conversão

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 1: ANÁLISE                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ Parse all   │───▶│ Build       │───▶│ Calculate           │ │
│  │ elements    │    │ dependency  │    │ topological         │ │
│  │             │    │ graph       │    │ order               │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 2: CONVERSÃO                            │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ SCHEMA   │──▶│ DOMAIN   │──▶│ BUSINESS │──▶│ API      │    │
│  │ (ordem 1)│   │ (ordem 2)│   │ (ordem 3)│   │ (ordem 4)│    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│        │              │              │              │          │
│        ▼              ▼              ▼              ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    CONTEXT WINDOW                         │  │
│  │  Ao converter elemento N, incluir no contexto:           │  │
│  │  - Elementos já convertidos que N depende                │  │
│  │  - Interfaces/tipos exportados                           │  │
│  │  - Padrões similares já validados (RAG)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────┐                                                  │
│  │ UI       │  (última camada, todas dependências prontas)    │
│  │ (ordem 5)│                                                  │
│  └──────────┘                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Context Window Inteligente

Ao converter um elemento, o contexto enviado ao LLM inclui:

```python
context = {
    "element": current_element,
    "converted_dependencies": [
        # Elementos já convertidos que este usa
        {"name": "classUsuario", "python_code": "...", "exports": ["Usuario"]}
    ],
    "similar_patterns": [
        # Exemplos de conversões similares já validadas (RAG)
    ],
    "target_architecture": {
        # Blueprint da arquitetura alvo
        "project_structure": "...",
        "naming_conventions": "...",
        "import_patterns": "..."
    }
}
```

## Alternativas Consideradas

| Abordagem | Prós | Contras |
|-----------|------|---------|
| Elemento a elemento | Simples | Perde contexto, código inconsistente |
| Tudo de uma vez | Contexto completo | Não cabe na janela do LLM |
| Por arquivo | Natural | Ignora dependências entre arquivos |

## Consequências

### Positivas
- Código convertido é coerente
- Dependências são respeitadas
- LLM tem contexto adequado para cada conversão
- Permite retomar conversão de onde parou

### Negativas
- Mais complexo de implementar
- Requer análise prévia de dependências
- Conversão é mais lenta (sequencial por necessidade)

## Notas

O chunking semântico é aplicado dentro de cada elemento quando necessário, mas a ordem de processamento segue as camadas.
