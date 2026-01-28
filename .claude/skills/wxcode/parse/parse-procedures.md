---
name: wx:parse-procedures
description: Parseia procedures globais de arquivos .wdg (procedure groups).
allowed-tools: Bash
---

# wx:parse-procedures - Parsear Procedures Globais

Parseia arquivos .wdg para extrair procedures globais do servidor.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_dir` | path | Sim | Diretório do projeto WinDev |
| `--batch-size` | int | Não | Tamanho do batch (default: 100) |

## Uso

```bash
wxcode parse-procedures <project_dir> [--batch-size N]
```

## Exemplos

```bash
# Parsear procedures
wxcode parse-procedures ./project-refs/Linkpay_ADM

# Com batch maior
wxcode parse-procedures ./project-refs/Linkpay_ADM --batch-size 200
```

## O que é extraído

- **Nome da procedure**: Identificador único
- **Parâmetros**: Nome, tipo, valor default
- **Tipo de retorno**: Quando declarado
- **Corpo**: Código WLanguage completo
- **Dependências**: Chamadas a outras procedures/classes

## Formato .wdg

```yaml
Procedure|Name:
  Nom visible=NomeProcedure
  |1+
    // Código WLanguage aqui
    RESULT valor
  -1|
```

## Saída esperada

```
Parsing procedures in: Linkpay_ADM
Processing ServerProcedures.wdg...
  Found 25 procedures
Processing UtilProcedures.wdg...
  Found 18 procedures
...
Total: 80 procedures parsed
```

## Próximos Passos

Após parsear procedures:
- `/wx:parse-classes` - Parsear classes
- `/wx:analyze` - Analisar dependências

## Collection Atualizada

- `procedures`: Novos documentos para cada procedure
- `elements`: Atualiza referências em `ast.procedures`
