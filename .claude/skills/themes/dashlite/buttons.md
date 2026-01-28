---
name: dashlite-buttons
description: Botões DashLite - variants, states, icons, groups
depends-on: [dashlite-_index]
---

# DashLite: Buttons

## Base Structure

```html
<button type="button" class="btn btn-{variant}">Button Text</button>
<a href="#" class="btn btn-{variant}">Link Button</a>
```

## Variants

### Solid Buttons

| Context | Classes | Usage |
|---------|---------|-------|
| Primary action | `btn btn-primary` | Main actions (Save, Submit) |
| Secondary | `btn btn-secondary` | Secondary actions |
| Success | `btn btn-success` | Positive actions (Confirm) |
| Danger | `btn btn-danger` | Destructive (Delete) |
| Warning | `btn btn-warning` | Caution actions |
| Info | `btn btn-info` | Informational |
| Light | `btn btn-light` | Subtle actions |
| Dark | `btn btn-dark` | High contrast |

```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-success">Success</button>
<button class="btn btn-danger">Danger</button>
```

### Outline Buttons

For less emphasis, use outline variants:

```html
<button class="btn btn-outline-primary">Outline Primary</button>
<button class="btn btn-outline-secondary">Outline Secondary</button>
<button class="btn btn-outline-danger">Outline Danger</button>
```

### Dim (Soft) Buttons

DashLite's signature soft-style buttons:

```html
<button class="btn btn-dim btn-primary">Dim Primary</button>
<button class="btn btn-dim btn-secondary">Dim Secondary</button>
<button class="btn btn-dim btn-success">Dim Success</button>
<button class="btn btn-dim btn-danger">Dim Danger</button>
```

Use `.btn-dim` for toolbar buttons and less prominent actions.

## Sizes

| Size | Class | Usage |
|------|-------|-------|
| Extra Small | `btn-xs` | Inline, table actions |
| Small | `btn-sm` | Compact areas |
| Default | (none) | Standard buttons |
| Large | `btn-lg` | Hero sections, prominent CTAs |

```html
<button class="btn btn-primary btn-xs">Extra Small</button>
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-primary btn-lg">Large</button>
```

## Buttons with Icons

### Icon + Text

```html
<button class="btn btn-primary">
    <em class="icon ni ni-plus"></em>
    <span>Add New</span>
</button>

<button class="btn btn-dim btn-secondary">
    <em class="icon ni ni-edit"></em>
    <span>Edit</span>
</button>

<button class="btn btn-danger">
    <em class="icon ni ni-trash"></em>
    <span>Delete</span>
</button>
```

### Icon Only

Use `.btn-icon` for icon-only buttons:

```html
<button class="btn btn-icon btn-primary">
    <em class="icon ni ni-plus"></em>
</button>

<button class="btn btn-icon btn-dim btn-secondary">
    <em class="icon ni ni-edit"></em>
</button>
```

### Round Icon Buttons

```html
<button class="btn btn-round btn-icon btn-primary">
    <em class="icon ni ni-plus"></em>
</button>
```

## Button States

### Disabled

```html
<button class="btn btn-primary" disabled>Disabled</button>
<a href="#" class="btn btn-primary disabled">Disabled Link</a>
```

### Loading

```html
<button class="btn btn-primary" disabled>
    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
    <span>Loading...</span>
</button>
```

### Active

```html
<button class="btn btn-primary active">Active</button>
```

## Button Groups

### Horizontal Group

```html
<div class="btn-group">
    <button class="btn btn-outline-primary">Left</button>
    <button class="btn btn-outline-primary">Middle</button>
    <button class="btn btn-outline-primary">Right</button>
</div>
```

### With Dropdown

```html
<div class="btn-group">
    <button class="btn btn-primary">Action</button>
    <button class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown">
        <span class="visually-hidden">Toggle Dropdown</span>
    </button>
    <div class="dropdown-menu">
        <a class="dropdown-item" href="#">Option 1</a>
        <a class="dropdown-item" href="#">Option 2</a>
        <div class="dropdown-divider"></div>
        <a class="dropdown-item" href="#">Option 3</a>
    </div>
</div>
```

## Trigger Buttons

For toggling elements (sidebars, modals):

```html
<button class="btn btn-trigger btn-icon" data-target="sideNav">
    <em class="icon ni ni-menu"></em>
</button>
```

## Block Buttons

Full-width buttons:

```html
<button class="btn btn-primary btn-block">Full Width Button</button>

<!-- Or using d-grid -->
<div class="d-grid gap-2">
    <button class="btn btn-primary">Full Width</button>
    <button class="btn btn-secondary">Another Full Width</button>
</div>
```

## Common Action Patterns

### CRUD Actions

```html
<!-- Create -->
<button class="btn btn-primary">
    <em class="icon ni ni-plus"></em>
    <span>Adicionar</span>
</button>

<!-- Edit -->
<button class="btn btn-dim btn-secondary">
    <em class="icon ni ni-edit"></em>
    <span>Editar</span>
</button>

<!-- Delete -->
<button class="btn btn-dim btn-danger">
    <em class="icon ni ni-trash"></em>
    <span>Excluir</span>
</button>

<!-- View -->
<button class="btn btn-dim btn-info">
    <em class="icon ni ni-eye"></em>
    <span>Visualizar</span>
</button>
```

### Form Actions

```html
<div class="form-group">
    <button type="submit" class="btn btn-primary">
        <em class="icon ni ni-check"></em>
        <span>Salvar</span>
    </button>
    <button type="button" class="btn btn-outline-secondary">
        <em class="icon ni ni-cross"></em>
        <span>Cancelar</span>
    </button>
</div>
```

### Table Row Actions

```html
<ul class="nk-tb-actions gx-1">
    <li>
        <a href="#" class="btn btn-trigger btn-icon" data-bs-toggle="tooltip" title="Editar">
            <em class="icon ni ni-edit"></em>
        </a>
    </li>
    <li>
        <a href="#" class="btn btn-trigger btn-icon" data-bs-toggle="tooltip" title="Excluir">
            <em class="icon ni ni-trash"></em>
        </a>
    </li>
    <li>
        <div class="drodown">
            <a href="#" class="dropdown-toggle btn btn-icon btn-trigger" data-bs-toggle="dropdown">
                <em class="icon ni ni-more-h"></em>
            </a>
            <div class="dropdown-menu dropdown-menu-end">
                <ul class="link-list-opt no-bdr">
                    <li><a href="#"><em class="icon ni ni-eye"></em><span>Ver Detalhes</span></a></li>
                    <li><a href="#"><em class="icon ni ni-download"></em><span>Download</span></a></li>
                </ul>
            </div>
        </div>
    </li>
</ul>
```

## DO NOT

- Don't use `btn-link` without styling - prefer outline or dim variants
- Don't use FontAwesome icons - use NioIcon (`ni ni-*`)
- Don't put icons after text - icons go before text
- Don't use `<input type="button">` - use `<button>` elements
