---
name: wx:split-pdf
description: Divide PDF de documentação WinDev em arquivos individuais por elemento.
allowed-tools: Bash
---

# wx:split-pdf - Dividir PDF de Documentação

Divide o PDF de documentação técnica gerado pelo WinDev/WebDev em arquivos individuais por elemento.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `pdf_path` | path | Sim | Caminho para o PDF de documentação |
| `--output` | path | Não | Diretório de saída (default: ./output/pdf_docs) |
| `--project` | string | Não | Nome do projeto para matching de elementos |

## Uso

```bash
wxcode split-pdf <pdf_path> [--output DIR] [--project NAME]
```

## Exemplos

```bash
# Dividir PDF básico
wxcode split-pdf ./Documentation_Projeto.pdf

# Especificar output e projeto (reduz órfãos em ~82%)
wxcode split-pdf ./Documentation_Projeto.pdf \
  --output ./output/pdf_docs \
  --project Linkpay_ADM
```

## O que acontece

1. Extrai texto e estrutura do PDF
2. Identifica seções por elemento (PAGE_, PROC_, CLASS_, etc.)
3. Cria PDF individual para cada elemento
4. Gera manifest.json com mapeamento

## Saída esperada

```
Processing: Documentation_Projeto.pdf
Found 150 sections
Extracted: PAGE_Login.pdf
Extracted: PAGE_PRINCIPAL.pdf
...
Created 150 PDFs in ./output/pdf_docs
Orphan sections: 12 (8%)
Manifest saved to manifest.json
```

## Próximos Passos

Após dividir PDF:
- `/wx:enrich` - Usar PDFs para enriquecer elementos com propriedades visuais

## Estrutura de Saída

```
output/pdf_docs/
├── manifest.json
├── PAGE_Login.pdf
├── PAGE_PRINCIPAL.pdf
├── PROC_ServerProcedures.pdf
└── orphans/
    └── unknown_section_1.pdf
```
