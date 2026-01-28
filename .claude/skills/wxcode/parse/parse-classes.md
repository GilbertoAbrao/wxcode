---
name: wx:parse-classes
description: Parseia classes de arquivos .wdc com herança e métodos.
allowed-tools: Bash
---

# wx:parse-classes - Parsear Classes

Parseia arquivos .wdc para extrair classes, herança, propriedades e métodos.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_dir` | path | Sim | Diretório do projeto WinDev |
| `--batch-size` | int | Não | Tamanho do batch (default: 100) |

## Uso

```bash
wxcode parse-classes <project_dir> [--batch-size N]
```

## Exemplos

```bash
# Parsear classes
wxcode parse-classes ./project-refs/Linkpay_ADM
```

## O que é extraído

- **Nome da classe**: classUsuario, classBoleto, etc.
- **Herança**: Classe base (se houver)
- **Propriedades**: Membros da classe com tipos
- **Métodos**: Procedures da classe
- **Construtores/Destrutores**: Constructor, Destructor

## Saída esperada

```
Parsing classes in: Linkpay_ADM
Processing classUsuario.wdc...
  Inherits from: classBase
  Properties: 8
  Methods: 12
Processing classBoleto.wdc...
...
Total: 25 classes parsed
```

## Próximos Passos

Após parsear classes:
- `/wx:parse-schema` - Parsear schema do banco
- `/wx:analyze` - Analisar dependências

## Collection Atualizada

- `elements`: Atualiza documentos de tipo "class" com AST completo
