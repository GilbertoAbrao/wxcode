---
name: dashlite-forms-select
description: Select dropdowns DashLite - nativo, Select2, multiselect
depends-on: [dashlite-forms-_index]
---

# DashLite: Select Dropdowns

## Native Select

### Basic

```html
<div class="form-group">
    <label class="form-label" for="status">Status</label>
    <select class="form-select" id="status" name="status">
        <option value="">Selecione...</option>
        <option value="active">Ativo</option>
        <option value="inactive">Inativo</option>
        <option value="pending">Pendente</option>
    </select>
</div>
```

### With Default Value (Jinja2)

```html
<select class="form-select" id="status" name="status">
    <option value="">Selecione...</option>
    <option value="active" {% if form.status == 'active' %}selected{% endif %}>Ativo</option>
    <option value="inactive" {% if form.status == 'inactive' %}selected{% endif %}>Inativo</option>
</select>
```

### Sizes

```html
<select class="form-select form-select-sm">...</select>
<select class="form-select">...</select>
<select class="form-select form-select-lg">...</select>
```

### Disabled

```html
<select class="form-select" disabled>
    <option selected>Não editável</option>
</select>
```

## Select2 Enhanced Select

DashLite uses Select2 for enhanced dropdowns. Add class `js-select2` to enable.

### Basic Select2

```html
<div class="form-group">
    <label class="form-label">Estado</label>
    <select class="form-select js-select2" data-placeholder="Selecione o estado">
        <option value="">Selecione...</option>
        <option value="SP">São Paulo</option>
        <option value="RJ">Rio de Janeiro</option>
        <option value="MG">Minas Gerais</option>
    </select>
</div>
```

### Searchable

```html
<select class="form-select js-select2" data-search="on">
    <option value="">Buscar...</option>
    {% for item in items %}
    <option value="{{ item.id }}">{{ item.name }}</option>
    {% endfor %}
</select>
```

### Clear Button

```html
<select class="form-select js-select2" data-placeholder="Selecione" data-allow-clear="true">
    <option></option>
    <option value="1">Opção 1</option>
    <option value="2">Opção 2</option>
</select>
```

## Multiple Select

### Basic Multiple

```html
<div class="form-group">
    <label class="form-label">Categorias</label>
    <select class="form-select js-select2" multiple="multiple" data-placeholder="Selecione categorias">
        <option value="1">Categoria 1</option>
        <option value="2">Categoria 2</option>
        <option value="3">Categoria 3</option>
        <option value="4">Categoria 4</option>
    </select>
</div>
```

### With Preselected Values (Jinja2)

```html
<select class="form-select js-select2" multiple="multiple">
    {% for category in categories %}
    <option value="{{ category.id }}" {% if category.id in selected_ids %}selected{% endif %}>
        {{ category.name }}
    </option>
    {% endfor %}
</select>
```

### Tags Mode (Custom Values)

```html
<select class="form-select js-select2" multiple="multiple" data-tags="true" data-placeholder="Digite para adicionar">
    <option value="tag1">Tag 1</option>
    <option value="tag2">Tag 2</option>
</select>
```

## Option Groups

```html
<select class="form-select js-select2">
    <option value="">Selecione...</option>
    <optgroup label="Região Sul">
        <option value="PR">Paraná</option>
        <option value="SC">Santa Catarina</option>
        <option value="RS">Rio Grande do Sul</option>
    </optgroup>
    <optgroup label="Região Sudeste">
        <option value="SP">São Paulo</option>
        <option value="RJ">Rio de Janeiro</option>
        <option value="MG">Minas Gerais</option>
        <option value="ES">Espírito Santo</option>
    </optgroup>
</select>
```

## Select in Input Group

```html
<div class="form-group">
    <label class="form-label">Filtrar</label>
    <div class="input-group">
        <select class="form-select" style="max-width: 150px;">
            <option value="all">Todos</option>
            <option value="name">Nome</option>
            <option value="email">Email</option>
        </select>
        <input type="text" class="form-control" placeholder="Buscar...">
        <button class="btn btn-outline-primary" type="button">
            <em class="icon ni ni-search"></em>
        </button>
    </div>
</div>
```

## Data Attributes

| Attribute | Purpose |
|-----------|---------|
| `data-placeholder` | Placeholder text |
| `data-search="on"` | Enable search |
| `data-allow-clear="true"` | Show clear button |
| `data-tags="true"` | Allow custom tags |
| `data-dropdown-parent` | Set dropdown container |

## Select with Icon (Custom)

```html
<div class="form-group">
    <label class="form-label">País</label>
    <div class="form-control-wrap">
        <span class="form-icon form-icon-left">
            <em class="icon ni ni-globe"></em>
        </span>
        <select class="form-select ps-5">
            <option value="">Selecione o país</option>
            <option value="BR">Brasil</option>
            <option value="US">Estados Unidos</option>
        </select>
    </div>
</div>
```

## Common Patterns

### Status Filter

```html
<div class="form-group">
    <label class="form-label">Status</label>
    <select class="form-select js-select2" data-placeholder="Todos">
        <option value="">Todos</option>
        <option value="active">Ativo</option>
        <option value="inactive">Inativo</option>
        <option value="pending">Pendente</option>
    </select>
</div>
```

### Dependent Selects (State/City)

```html
<div class="row g-4">
    <div class="col-md-6">
        <div class="form-group">
            <label class="form-label">Estado</label>
            <select class="form-select js-select2" id="state" name="state">
                <option value="">Selecione o estado</option>
                {% for state in states %}
                <option value="{{ state.uf }}">{{ state.name }}</option>
                {% endfor %}
            </select>
        </div>
    </div>
    <div class="col-md-6">
        <div class="form-group">
            <label class="form-label">Cidade</label>
            <select class="form-select js-select2" id="city" name="city" data-search="on" disabled>
                <option value="">Selecione o estado primeiro</option>
            </select>
        </div>
    </div>
</div>
```

## Validation

```html
<div class="form-group">
    <label class="form-label">Tipo <span class="text-danger">*</span></label>
    <select class="form-select {% if errors.type %}is-invalid{% endif %}" name="type" required>
        <option value="">Selecione...</option>
        <option value="A">Tipo A</option>
        <option value="B">Tipo B</option>
    </select>
    {% if errors.type %}
    <div class="invalid-feedback">{{ errors.type }}</div>
    {% endif %}
</div>
```

## DO NOT

- Don't use `<select>` without `.form-select` class
- Don't forget empty `<option></option>` for Select2 with allow-clear
- Don't use complex dropdowns without `js-select2`
- Don't forget `data-placeholder` for Select2
