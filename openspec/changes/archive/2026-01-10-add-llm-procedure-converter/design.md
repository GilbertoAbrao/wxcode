# Design: LLM Procedure Converter

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Command                               │
│         wxcode convert PROJECT --layer service                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ProcedureConverter                           │
│  (Orquestra conversão de um procedure group para service)        │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ProcedureContext│    │   LLMProvider   │    │ ServiceOutput   │
│    Builder      │    │  (reutilizado)  │    │    Writer       │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
   MongoDB:              Anthropic API          app/services/
   - elements            Claude Sonnet          - {group}_service.py
   - procedures                                 - __init__.py
```

## Component Design

### 1. ProcedureContextBuilder

Responsável por montar o contexto do procedure group para o LLM.

```python
class ProcedureContextBuilder:
    async def build(self, element_id: ObjectId) -> ProcedureContext:
        # 1. Carregar element (procedure_group)
        # 2. Carregar todas procedures do grupo
        # 3. Carregar dependências (outras procedures chamadas)
        # 4. Estimar tokens e priorizar se necessário
        return ProcedureContext(...)
```

**Contexto inclui:**
- Nome do grupo e arquivo fonte
- Lista de procedures com código completo
- Procedures de outros grupos referenciadas
- Schema das tabelas acessadas (resumido)

### 2. LLMProvider (Reutilizado)

Mesmo provider usado pelo PageConverter. Apenas com prompt diferente.

**System Prompt para Procedures:**
```
Você é um conversor de WLanguage para Python.
Converta o grupo de procedures para uma classe de service FastAPI.

Regras:
- Gerar classe async com métodos para cada procedure
- Converter H* functions para MongoDB (motor)
- Preservar lógica de negócio e tratamento de erros
- Usar type hints Python
- Manter nomes de variáveis em snake_case
```

### 3. ServiceResponseParser

Parseia resposta JSON do LLM para estrutura de service.

```python
@dataclass
class ServiceConversionResult:
    class_name: str
    filename: str
    imports: list[str]
    methods: list[ServiceMethod]
    dependencies: list[str]  # Outros services necessários
    notes: list[str]
```

### 4. ServiceOutputWriter

Escreve arquivos de service no projeto.

```
app/services/
├── __init__.py           # Atualizado com novos exports
├── server_service.py     # Gerado do ServerProcedures.wdg
├── util_service.py       # Gerado do UtilProcedures.wdg
└── api_fitbank_service.py
```

## Data Flow

```
1. CLI recebe: convert Linkpay_ADM --layer service
                      │
2. Busca elements:    ▼
   db.elements.find({source_type: "procedure_group"})
                      │
3. Para cada group:   ▼
   ┌──────────────────────────────────────┐
   │ a. ProcedureContextBuilder.build()   │
   │ b. LLMProvider.convert(context)      │
   │ c. ServiceResponseParser.parse()     │
   │ d. ServiceOutputWriter.write()       │
   └──────────────────────────────────────┘
                      │
4. Atualiza status:   ▼
   element.conversion.status = "converted"
```

## Token Budget Strategy

| Grupo pequeno (< 5 procs) | Grupo médio (5-20 procs) | Grupo grande (> 20 procs) |
|---------------------------|--------------------------|---------------------------|
| Converter tudo de uma vez | Converter tudo de uma vez | Dividir em batches de 10 |
| ~2K tokens input          | ~10K tokens input        | ~5K tokens por batch     |

## Integration Points

### Com PageConverter

O PageConverter já inclui `referenced_procedures` no contexto. Os services gerados serão importados automaticamente nas rotas:

```python
# app/routers/login.py (gerado por PageConverter)
from app.services.server_service import ServerService

@router.post("/login")
async def login(service: ServerService = Depends()):
    return await service.global_faz_login_usuario_interno(login, senha)
```

### Com CLI

Integrar ao comando `convert` existente:

```bash
# Converter páginas (atual)
wxcode convert PROJECT -o ./output

# Converter services
wxcode convert PROJECT --layer service -o ./output

# Converter tudo
wxcode convert PROJECT --layer all -o ./output
```

## Error Handling

| Erro | Tratamento |
|------|------------|
| Procedure muito grande | Dividir por procedure individual |
| Dependência circular | Gerar stub e warning |
| Código incompreensível | Manter original como comentário |
| Rate limit LLM | Retry com backoff |
