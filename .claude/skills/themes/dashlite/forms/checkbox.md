---
name: dashlite-forms-checkbox
description: Checkboxes, switches, e radio buttons DashLite
depends-on: [dashlite-forms-_index]
---

# DashLite: Checkboxes, Switches & Radios

## Custom Checkbox

### Basic

```html
<div class="custom-control custom-checkbox">
    <input type="checkbox" class="custom-control-input" id="accept" name="accept">
    <label class="custom-control-label" for="accept">Aceito os termos</label>
</div>
```

### Checked

```html
<div class="custom-control custom-checkbox">
    <input type="checkbox" class="custom-control-input" id="rememberMe" name="rememberMe" checked>
    <label class="custom-control-label" for="rememberMe">Lembrar de mim</label>
</div>
```

### With Jinja2

```html
<div class="custom-control custom-checkbox">
    <input type="checkbox" class="custom-control-input" id="active" name="active"
           {% if form.active %}checked{% endif %}>
    <label class="custom-control-label" for="active">Ativo</label>
</div>
```

### Disabled

```html
<div class="custom-control custom-checkbox">
    <input type="checkbox" class="custom-control-input" id="locked" disabled checked>
    <label class="custom-control-label" for="locked">Bloqueado</label>
</div>
```

## Checkbox Group (Stacked)

```html
<div class="form-group">
    <label class="form-label">Permissões</label>
    <div class="g-3">
        <div class="custom-control custom-checkbox">
            <input type="checkbox" class="custom-control-input" id="perm_read" name="permissions[]" value="read">
            <label class="custom-control-label" for="perm_read">Leitura</label>
        </div>
        <div class="custom-control custom-checkbox">
            <input type="checkbox" class="custom-control-input" id="perm_write" name="permissions[]" value="write">
            <label class="custom-control-label" for="perm_write">Escrita</label>
        </div>
        <div class="custom-control custom-checkbox">
            <input type="checkbox" class="custom-control-input" id="perm_delete" name="permissions[]" value="delete">
            <label class="custom-control-label" for="perm_delete">Exclusão</label>
        </div>
    </div>
</div>
```

## Checkbox Group (Inline)

```html
<div class="form-group">
    <label class="form-label">Dias da Semana</label>
    <div class="d-flex flex-wrap g-3">
        <div class="custom-control custom-checkbox me-3">
            <input type="checkbox" class="custom-control-input" id="mon" name="days[]" value="mon">
            <label class="custom-control-label" for="mon">Seg</label>
        </div>
        <div class="custom-control custom-checkbox me-3">
            <input type="checkbox" class="custom-control-input" id="tue" name="days[]" value="tue">
            <label class="custom-control-label" for="tue">Ter</label>
        </div>
        <div class="custom-control custom-checkbox me-3">
            <input type="checkbox" class="custom-control-input" id="wed" name="days[]" value="wed">
            <label class="custom-control-label" for="wed">Qua</label>
        </div>
        <!-- ... -->
    </div>
</div>
```

## Switch Toggle

### Basic Switch

```html
<div class="custom-control custom-switch">
    <input type="checkbox" class="custom-control-input" id="notifications" name="notifications">
    <label class="custom-control-label" for="notifications">Receber notificações</label>
</div>
```

### Checked Switch

```html
<div class="custom-control custom-switch">
    <input type="checkbox" class="custom-control-input" id="enabled" name="enabled" checked>
    <label class="custom-control-label" for="enabled">Habilitado</label>
</div>
```

### Switch Group

```html
<div class="form-group">
    <label class="form-label">Configurações</label>
    <ul class="custom-control-group g-3 align-center">
        <li>
            <div class="custom-control custom-switch">
                <input type="checkbox" class="custom-control-input" id="email_notify" name="email_notify" checked>
                <label class="custom-control-label" for="email_notify">Email</label>
            </div>
        </li>
        <li>
            <div class="custom-control custom-switch">
                <input type="checkbox" class="custom-control-input" id="sms_notify" name="sms_notify">
                <label class="custom-control-label" for="sms_notify">SMS</label>
            </div>
        </li>
        <li>
            <div class="custom-control custom-switch">
                <input type="checkbox" class="custom-control-input" id="push_notify" name="push_notify" checked>
                <label class="custom-control-label" for="push_notify">Push</label>
            </div>
        </li>
    </ul>
</div>
```

## Radio Buttons

### Basic Radio Group

```html
<div class="form-group">
    <label class="form-label">Tipo de Pessoa</label>
    <div class="g-3">
        <div class="custom-control custom-radio">
            <input type="radio" class="custom-control-input" id="pf" name="person_type" value="PF">
            <label class="custom-control-label" for="pf">Pessoa Física</label>
        </div>
        <div class="custom-control custom-radio">
            <input type="radio" class="custom-control-input" id="pj" name="person_type" value="PJ">
            <label class="custom-control-label" for="pj">Pessoa Jurídica</label>
        </div>
    </div>
</div>
```

### With Default Selection

```html
<div class="custom-control custom-radio">
    <input type="radio" class="custom-control-input" id="active" name="status" value="active" checked>
    <label class="custom-control-label" for="active">Ativo</label>
</div>
<div class="custom-control custom-radio">
    <input type="radio" class="custom-control-input" id="inactive" name="status" value="inactive">
    <label class="custom-control-label" for="inactive">Inativo</label>
</div>
```

### Inline Radio

```html
<div class="form-group">
    <label class="form-label">Gênero</label>
    <div class="d-flex flex-wrap g-3">
        <div class="custom-control custom-radio me-3">
            <input type="radio" class="custom-control-input" id="male" name="gender" value="M">
            <label class="custom-control-label" for="male">Masculino</label>
        </div>
        <div class="custom-control custom-radio me-3">
            <input type="radio" class="custom-control-input" id="female" name="gender" value="F">
            <label class="custom-control-label" for="female">Feminino</label>
        </div>
        <div class="custom-control custom-radio">
            <input type="radio" class="custom-control-input" id="other" name="gender" value="O">
            <label class="custom-control-label" for="other">Outro</label>
        </div>
    </div>
</div>
```

### With Jinja2 Loop

```html
<div class="form-group">
    <label class="form-label">Categoria</label>
    <div class="g-3">
        {% for category in categories %}
        <div class="custom-control custom-radio">
            <input type="radio" class="custom-control-input"
                   id="cat_{{ category.id }}"
                   name="category_id"
                   value="{{ category.id }}"
                   {% if form.category_id == category.id %}checked{% endif %}>
            <label class="custom-control-label" for="cat_{{ category.id }}">{{ category.name }}</label>
        </div>
        {% endfor %}
    </div>
</div>
```

## Checkbox Cards

For more prominent selection:

```html
<ul class="custom-control-group g-3">
    <li>
        <div class="custom-control custom-control-pro custom-checkbox">
            <input type="checkbox" class="custom-control-input" id="plan_basic" name="plans[]" value="basic">
            <label class="custom-control-label" for="plan_basic">
                <span class="d-block fw-bold">Básico</span>
                <span class="d-block text-soft">R$ 29,90/mês</span>
            </label>
        </div>
    </li>
    <li>
        <div class="custom-control custom-control-pro custom-checkbox">
            <input type="checkbox" class="custom-control-input" id="plan_pro" name="plans[]" value="pro">
            <label class="custom-control-label" for="plan_pro">
                <span class="d-block fw-bold">Profissional</span>
                <span class="d-block text-soft">R$ 59,90/mês</span>
            </label>
        </div>
    </li>
</ul>
```

## Radio Cards

```html
<ul class="custom-control-group g-3">
    <li>
        <div class="custom-control custom-control-pro custom-radio">
            <input type="radio" class="custom-control-input" id="ship_standard" name="shipping" value="standard" checked>
            <label class="custom-control-label" for="ship_standard">
                <span class="d-block fw-bold">Padrão</span>
                <span class="d-block text-soft">5-7 dias úteis</span>
            </label>
        </div>
    </li>
    <li>
        <div class="custom-control custom-control-pro custom-radio">
            <input type="radio" class="custom-control-input" id="ship_express" name="shipping" value="express">
            <label class="custom-control-label" for="ship_express">
                <span class="d-block fw-bold">Expresso</span>
                <span class="d-block text-soft">1-2 dias úteis</span>
            </label>
        </div>
    </li>
</ul>
```

## Validation

```html
<div class="form-group">
    <div class="custom-control custom-checkbox">
        <input type="checkbox"
               class="custom-control-input {% if errors.terms %}is-invalid{% endif %}"
               id="terms"
               name="terms"
               required>
        <label class="custom-control-label" for="terms">
            Aceito os <a href="#">termos de uso</a> <span class="text-danger">*</span>
        </label>
    </div>
    {% if errors.terms %}
    <div class="invalid-feedback d-block">{{ errors.terms }}</div>
    {% endif %}
</div>
```

## DO NOT

- Don't use native checkbox/radio - use `.custom-control`
- Don't forget matching `for` and `id` attributes
- Don't use the same `id` for multiple elements
- Don't forget `name` attribute for form submission
