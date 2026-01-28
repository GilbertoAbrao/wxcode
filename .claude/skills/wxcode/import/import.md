---
name: wx:import
description: Importa projeto WinDev/WebDev para MongoDB com streaming para arquivos grandes.
allowed-tools: Bash
---

# wx:import - Importar Projeto

Importa um projeto WinDev (.wdp) ou WebDev (.wwp) para o MongoDB, mapeando todos os elementos.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_path` | path | Sim | Caminho para o arquivo .wwp ou .wdp |
| `--batch-size` | int | Não | Tamanho do batch MongoDB (default: 100) |

## Uso

```bash
wxcode import <project_path> [--batch-size N]
```

## Exemplos

```bash
# Importar projeto WebDev
wxcode import ./Linkpay_ADM.wwp

# Importar com batch maior (para projetos muito grandes)
wxcode import ./Projeto.wwp --batch-size 200
```

## O que acontece

1. Lê o arquivo .wwp/.wdp em streaming (não carrega tudo na memória)
2. Parseia cada elemento encontrado
3. Insere em batches no MongoDB (collection `elements`)
4. Cria registro na collection `projects`

## Saída esperada

```
Importing project: Linkpay_ADM
Found 150 elements
Batch 1/2 inserted (100 elements)
Batch 2/2 inserted (50 elements)
Project imported successfully!
```

## Próximos Passos

Após importar:
- `/wx:split-pdf` - Dividir PDF de documentação (se disponível)
- `/wx:enrich` - Enriquecer elementos com controles e eventos
- `/wx:status` - Verificar status do projeto

## Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| File not found | Caminho incorreto | Verificar se o arquivo existe |
| MongoDB connection failed | MongoDB não está rodando | Iniciar MongoDB |
| Project already exists | Projeto já foi importado | Usar `/wx:purge` primeiro |
