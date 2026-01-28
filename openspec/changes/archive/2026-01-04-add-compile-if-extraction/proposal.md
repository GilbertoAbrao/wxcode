# Proposal: add-compile-if-extraction

## Problem Statement

Projetos WinDev/WebDev têm múltiplas **configurations** que geram outputs diferentes:

| Configuration | Type | Output |
|---------------|------|--------|
| Producao | 2 (Site WEBDEV) | Site completo com UI |
| Homolog | 2 (Site WEBDEV) | Site completo com UI |
| API_Producao | 23 (REST Webservice) | API REST only |
| API_Homolog | 23 (REST Webservice) | API REST only |

Além disso, usam diretivas `<COMPILE IF Configuration="...">` para código condicional:

```wlanguage
<COMPILE IF Configuration="Homolog" OR Configuration="API_Homolog">
    CONSTANT URL_API = "https://hmlapi.linkpay.com.br"
<END>

<COMPILE IF Configuration="Producao" OR Configuration="API_Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
<END>
```

**Problemas atuais:**
1. Blocos `COMPILE IF` são ignorados → código incompleto
2. Não há como converter por configuration específica
3. Não diferenciamos type=2 (Site) de type=23 (API only)
4. Output path é manual em vez de automático

## Proposed Solution

### 1. COMPILE IF Extraction (3 camadas)

```
Código WLanguage → Extractor → ConfigurationContext (IR) → ConfigGenerator → config/
```

### 2. CLI com conversão por configuration

```bash
# Converter uma configuration específica
wxcode convert Linkpay_ADM --config Producao
# Output: ./output/Producao/

# Converter com output base diferente
wxcode convert Linkpay_ADM --config Producao --output ./deploy
# Output: ./deploy/Producao/

# Converter todas as configurations
wxcode convert Linkpay_ADM --all-configs
# Output: ./output/Producao/
#         ./output/Homolog/
#         ./output/API_Producao/
#         ./output/API_Homolog/
```

### 3. Stack diferenciada por tipo de configuration

| Type Code | Descrição | Stack Gerada |
|-----------|-----------|--------------|
| 2 | Site WEBDEV | FastAPI + Jinja2 (templates) |
| 23 | REST Webservice | FastAPI only (sem templates) |

### Benefícios

- **Código limpo**: Sem condicionais de ambiente, configuração externalizada
- **12-factor compliant**: Configuração separada do código
- **Output automático**: Nome da config vira pasta de output
- **Stack correta**: API gera só rotas, Site gera templates também
- **Extensível**: Novo stack = novo ConfigGenerator

## Scope

### IN SCOPE
- Parser para blocos `<COMPILE IF Configuration=...>`
- Model `ConfigurationContext` para IR
- Interface `BaseConfigGenerator` + `PythonConfigGenerator`
- CLI `--config` e `--all-configs` para conversão por configuration
- Output automático usando nome da configuration
- Diferenciação de stack por type code (2 vs 23)
- Filtro de elementos por configuration (usa `excluded_from`)
- Integração com `WLanguageConverter` e generators existentes

### OUT OF SCOPE
- ConfigGenerators para outros stacks (Node, Go) - changes futuros
- UI para visualização de diferenças entre configs

## Dependencies

- `add-element-configuration-tracking`: Popula `excluded_from` nos elementos
- Specs existentes: `service-generator`, `route-generator`, `template-generator`

## Acceptance Criteria

1. Blocos `<COMPILE IF>` são detectados e parseados corretamente
2. Variáveis condicionais são extraídas para `ConfigurationContext`
3. `PythonConfigGenerator` gera `config/settings.py` e `.env.{config}`
4. CLI `--config Producao` gera em `./output/Producao/`
5. CLI `--all-configs` gera todas as configurations
6. type=2 gera FastAPI + Jinja2, type=23 gera FastAPI only
7. Elementos excluídos da configuration são filtrados
8. Código convertido usa `settings.VAR` em vez de valores hard-coded
