# fix-theme-assets

## Problema

Ao executar `wxcode convert-page PAGE_Login --theme dashlite`, o HTML gerado referencia assets do tema DashLite que não existem no diretório static da aplicação gerada:

```
[GET] /static/css/dashlite.css => 404 Not Found
[GET] /static/js/bundle.js => 404 Not Found
[GET] /static/js/scripts.js => 404 Not Found
[GET] /static/images/logo-principal.png => 404 Not Found
```

### Análise de Fidelidade (PAGE_Login)

**Controles no código legado:**
| Controle | Tipo | Função |
|----------|------|--------|
| EDT_LOGIN | Edit (2) | Campo de login |
| EDT_Senha | Edit (2) | Campo de senha |
| BTN_Entrar | Button (4) | Botão com `Local_Login()` |
| IMG_LOGO_PRINCIPAL_MENU | Image (22) | Logo principal |
| RTA_PAINEL_ADMINISTRATIVO | RichText (109) | Título "PAINEL ADMINISTRATIVO" |
| stc_Ip | Static (3) | Exibe IP do cliente |
| CELL_NoName1 | Cell (39) | Container dos controles |

**HTML gerado:**
- ✅ Campo login com placeholder
- ✅ Campo senha com toggle visibility
- ✅ Botão "Entrar"
- ✅ Logo (referência correta, arquivo faltando)
- ✅ Título "PAINEL ADMINISTRATIVO"
- ✅ IP do cliente via `request.client.host`

**Conclusão:** A fidelidade da conversão está correta. O problema é exclusivamente a falta de assets do tema.

## Causa Raiz

1. Os assets do tema DashLite existem em `themes/dashlite-v3.3.0/` mas não são copiados para `output/generated/app/static/`

2. O comando `convert-page` gera HTML com referências a assets que assume existirem, mas não há mecanismo para deployar os assets

3. O comando `init-project` cria a estrutura básica mas não inclui assets de tema

## Solução Proposta

Adicionar comando `wxcode deploy-theme` que:

1. Copia assets do tema (CSS, JS, fonts, images) para o diretório static do projeto gerado
2. Valida que todos os arquivos necessários existem
3. Pode ser executado standalone ou integrado ao `convert-page`

### Fluxo Atualizado

```bash
# Antes (falha)
wxcode convert-page PAGE_Login --theme dashlite -o ./output/generated

# Depois (funciona)
wxcode deploy-theme dashlite -o ./output/generated
wxcode convert-page PAGE_Login --theme dashlite -o ./output/generated

# Ou com flag integrada
wxcode convert-page PAGE_Login --theme dashlite --deploy-assets -o ./output/generated
```

## Escopo

- **IN:** Comando `deploy-theme` para copiar assets
- **IN:** Flag `--deploy-assets` no `convert-page`
- **IN:** Validação de existência de assets
- **OUT:** Minificação ou bundling de assets
- **OUT:** Customização de tema em runtime

## Impacto

- CLI: Novo comando + nova flag
- Nenhuma mudança em models ou database
- Baixo risco - apenas cópia de arquivos
