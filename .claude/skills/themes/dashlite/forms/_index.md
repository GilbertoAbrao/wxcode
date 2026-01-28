---
name: dashlite-forms-_index
description: Forms DashLite - estrutura base, validação, padrões
depends-on: [dashlite-_index]
---

# DashLite: Forms Overview

## Form Container

```html
<form action="#" method="POST" class="form-validate">
    <!-- Form content -->
</form>
```

## Form Group Pattern

Every form field should be wrapped in a `.form-group`:

```html
<div class="form-group">
    <label class="form-label" for="fieldId">Label</label>
    <input type="text" class="form-control" id="fieldId" name="fieldName">
</div>
```

### With Help Text

```html
<div class="form-group">
    <label class="form-label" for="email">Email</label>
    <input type="email" class="form-control" id="email" name="email">
    <span class="form-note">Seu email não será compartilhado.</span>
</div>
```

### Required Fields

```html
<div class="form-group">
    <label class="form-label" for="name">Nome <span class="text-danger">*</span></label>
    <input type="text" class="form-control" id="name" name="name" required>
</div>
```

## Form Control Classes

| Class | Usage |
|-------|-------|
| `.form-control` | Standard inputs, textareas |
| `.form-control-lg` | Large inputs |
| `.form-control-sm` | Small inputs |
| `.form-select` | Select dropdowns |
| `.form-label` | Field labels |
| `.form-note` | Help text below field |

## Form Layouts

### Vertical (Default)

```html
<div class="row g-4">
    <div class="col-12">
        <div class="form-group">
            <label class="form-label">Campo 1</label>
            <input type="text" class="form-control">
        </div>
    </div>
    <div class="col-12">
        <div class="form-group">
            <label class="form-label">Campo 2</label>
            <input type="text" class="form-control">
        </div>
    </div>
</div>
```

### Horizontal

```html
<div class="row g-3 align-items-center">
    <div class="col-md-3">
        <label class="form-label">Nome</label>
    </div>
    <div class="col-md-9">
        <input type="text" class="form-control">
    </div>
</div>
```

### Inline

```html
<div class="row g-3 align-items-center">
    <div class="col-auto">
        <label class="form-label">Buscar</label>
    </div>
    <div class="col-auto">
        <input type="text" class="form-control">
    </div>
    <div class="col-auto">
        <button class="btn btn-primary">Buscar</button>
    </div>
</div>
```

### Multi-Column

```html
<div class="row g-4">
    <div class="col-lg-6">
        <div class="form-group">
            <label class="form-label">Nome</label>
            <input type="text" class="form-control">
        </div>
    </div>
    <div class="col-lg-6">
        <div class="form-group">
            <label class="form-label">Sobrenome</label>
            <input type="text" class="form-control">
        </div>
    </div>
    <div class="col-12">
        <div class="form-group">
            <label class="form-label">Email</label>
            <input type="email" class="form-control">
        </div>
    </div>
</div>
```

## Validation States

### Invalid State

```html
<div class="form-group">
    <label class="form-label" for="email">Email</label>
    <input type="email" class="form-control is-invalid" id="email" value="invalid-email">
    <div class="invalid-feedback">Por favor, insira um email válido.</div>
</div>
```

### Valid State

```html
<div class="form-group">
    <label class="form-label" for="name">Nome</label>
    <input type="text" class="form-control is-valid" id="name" value="João Silva">
    <div class="valid-feedback">Perfeito!</div>
</div>
```

### Server-Side Validation (Jinja2)

```html
<div class="form-group">
    <label class="form-label" for="email">Email</label>
    <input type="email"
           class="form-control {% if errors.email %}is-invalid{% endif %}"
           id="email"
           name="email"
           value="{{ form.email or '' }}">
    {% if errors.email %}
    <div class="invalid-feedback">{{ errors.email }}</div>
    {% endif %}
</div>
```

## Form Sections

### With Divider

```html
<div class="nk-block-head nk-block-head-sm">
    <div class="nk-block-head-content">
        <h6 class="nk-block-title">Informações Pessoais</h6>
    </div>
</div>
<div class="nk-block">
    <div class="row g-4">
        <!-- Form fields -->
    </div>
</div>

<div class="nk-divider divider md"></div>

<div class="nk-block-head nk-block-head-sm">
    <div class="nk-block-head-content">
        <h6 class="nk-block-title">Endereço</h6>
    </div>
</div>
<div class="nk-block">
    <div class="row g-4">
        <!-- Address fields -->
    </div>
</div>
```

## Form Actions

```html
<div class="form-group">
    <button type="submit" class="btn btn-lg btn-primary">
        <em class="icon ni ni-check"></em>
        <span>Salvar</span>
    </button>
    <a href="#" class="btn btn-lg btn-outline-secondary ms-2">
        <em class="icon ni ni-cross"></em>
        <span>Cancelar</span>
    </a>
</div>
```

### Sticky Actions

```html
<div class="nk-block">
    <div class="row g-4">
        <!-- Form fields -->
    </div>
    <div class="row g-4 mt-3">
        <div class="col-12">
            <div class="d-flex justify-content-end gap-2">
                <button type="button" class="btn btn-outline-secondary">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </div>
    </div>
</div>
```

## Form in Card

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="card-head">
            <h5 class="card-title">Formulário</h5>
        </div>
        <form>
            <div class="row g-4">
                <!-- Form fields -->
            </div>
        </form>
    </div>
</div>
```

## Fieldset with Legend

```html
<fieldset>
    <legend class="overline-title overline-title-alt">Dados Bancários</legend>
    <div class="row g-4">
        <!-- Banking fields -->
    </div>
</fieldset>
```

## Disabled Form

```html
<fieldset disabled>
    <div class="row g-4">
        <div class="col-12">
            <div class="form-group">
                <label class="form-label">Campo Desabilitado</label>
                <input type="text" class="form-control" value="Não editável">
            </div>
        </div>
    </div>
</fieldset>
```

## DO NOT

- Don't use `<label>` without `.form-label` class
- Don't forget `.form-group` wrapper
- Don't use `placeholder` as the only label (accessibility)
- Don't mix `.form-control` with non-DashLite styles
