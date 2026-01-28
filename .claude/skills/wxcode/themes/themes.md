---
name: wx:themes
description: Gerencia temas disponíveis (list, add, remove).
allowed-tools: Bash
---

# wx:themes - Gerenciar Temas

Lista, adiciona ou remove temas disponíveis para projetos convertidos.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `action` | string | Sim | list, add, remove, info |
| `theme` | string | Cond. | Nome do tema (para add/remove/info) |
| `--path` | path | Cond. | Caminho do tema (para add) |

## Uso

```bash
wxcode themes <action> [theme] [--path PATH]
```

## Exemplos

```bash
# Listar temas disponíveis
wxcode themes list

# Info sobre tema
wxcode themes info dashlite

# Adicionar tema customizado
wxcode themes add meu-tema --path ./themes/meu-tema

# Remover tema
wxcode themes remove meu-tema
```

## Temas Incluídos

| Tema | Descrição |
|------|-----------|
| dashlite | Admin dashboard moderno (padrão) |
| bootstrap | Bootstrap 5 básico |
| tailwind | Tailwind CSS |

## Saída esperada (list)

```
Available themes:

  dashlite (default)
    Modern admin dashboard
    Components: 45
    Path: .claude/skills/themes/dashlite

  bootstrap
    Clean Bootstrap 5
    Components: 30
    Path: built-in

  tailwind
    Utility-first CSS
    Components: 25
    Path: built-in
```

## Estrutura de Tema

```
themes/meu-tema/
├── _index.md          # Metadados do tema
├── layout.md          # Layout base
├── buttons.md         # Componente botões
├── forms/
│   ├── _index.md
│   ├── input.md
│   └── select.md
└── tables.md
```

## Próximos Passos

Após gerenciar temas:
- `/wx:deploy-theme` - Aplicar tema ao projeto
