---
name: dashlite-forms-textarea
description: Textareas DashLite - básico, autosize, character counter
depends-on: [dashlite-forms-_index]
---

# DashLite: Textareas

## Basic Textarea

```html
<div class="form-group">
    <label class="form-label" for="description">Descrição</label>
    <textarea class="form-control" id="description" name="description" rows="4" placeholder="Digite a descrição..."></textarea>
</div>
```

## With Default Rows

| Rows | Usage |
|------|-------|
| `rows="2"` | Short notes |
| `rows="4"` | Default description |
| `rows="6"` | Longer content |
| `rows="10"` | Large text blocks |

```html
<textarea class="form-control" rows="2">Short</textarea>
<textarea class="form-control" rows="4">Medium</textarea>
<textarea class="form-control" rows="6">Large</textarea>
```

## Textarea with Auto-resize

```html
<div class="form-group">
    <label class="form-label">Observações</label>
    <textarea class="form-control no-resize" id="notes" name="notes" rows="3" placeholder="Texto com auto-expansão..."></textarea>
</div>
```

## Textarea Sizes

```html
<textarea class="form-control form-control-sm" rows="3">Small</textarea>
<textarea class="form-control" rows="3">Default</textarea>
<textarea class="form-control form-control-lg" rows="3">Large</textarea>
```

## With Character Counter

```html
<div class="form-group">
    <label class="form-label">Mensagem (máx. 500 caracteres)</label>
    <div class="form-control-wrap">
        <textarea class="form-control"
                  id="message"
                  name="message"
                  rows="4"
                  maxlength="500"
                  placeholder="Digite sua mensagem..."></textarea>
        <div class="form-note d-flex justify-content-end">
            <span class="text-soft"><span id="charCount">0</span>/500</span>
        </div>
    </div>
</div>
```

## Disabled & Readonly

### Disabled

```html
<textarea class="form-control" rows="3" disabled>Texto não editável</textarea>
```

### Readonly

```html
<textarea class="form-control" rows="3" readonly>Somente leitura</textarea>
```

## Textarea with Placeholder

```html
<div class="form-group">
    <label class="form-label">Endereço Completo</label>
    <textarea class="form-control"
              id="address"
              name="address"
              rows="3"
              placeholder="Rua, número, complemento..."></textarea>
</div>
```

## Validation States

### Invalid

```html
<div class="form-group">
    <label class="form-label">Descrição <span class="text-danger">*</span></label>
    <textarea class="form-control is-invalid" id="desc" name="description" rows="4" required></textarea>
    <div class="invalid-feedback">A descrição é obrigatória.</div>
</div>
```

### Valid

```html
<div class="form-group">
    <label class="form-label">Descrição</label>
    <textarea class="form-control is-valid" id="desc" rows="4">Conteúdo válido</textarea>
    <div class="valid-feedback">Perfeito!</div>
</div>
```

### With Jinja2

```html
<div class="form-group">
    <label class="form-label">Observações</label>
    <textarea class="form-control {% if errors.notes %}is-invalid{% endif %}"
              id="notes"
              name="notes"
              rows="4">{{ form.notes or '' }}</textarea>
    {% if errors.notes %}
    <div class="invalid-feedback">{{ errors.notes }}</div>
    {% endif %}
</div>
```

## Textarea for Code

```html
<div class="form-group">
    <label class="form-label">Código SQL</label>
    <textarea class="form-control"
              id="sqlCode"
              name="sql_code"
              rows="8"
              style="font-family: monospace;"
              placeholder="SELECT * FROM ..."></textarea>
</div>
```

## Textarea for JSON

```html
<div class="form-group">
    <label class="form-label">Configuração JSON</label>
    <textarea class="form-control"
              id="jsonConfig"
              name="json_config"
              rows="10"
              style="font-family: monospace;"
              placeholder='{"key": "value"}'></textarea>
    <span class="form-note">Cole o JSON de configuração</span>
</div>
```

## Full Width in Card

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="form-group">
            <label class="form-label">Detalhes</label>
            <textarea class="form-control form-control-lg"
                      id="details"
                      name="details"
                      rows="6"
                      placeholder="Descreva em detalhes..."></textarea>
        </div>
    </div>
</div>
```

## With Help Text

```html
<div class="form-group">
    <label class="form-label">Biografia</label>
    <textarea class="form-control" id="bio" name="bio" rows="4" placeholder="Conte um pouco sobre você..."></textarea>
    <span class="form-note">Será exibido no seu perfil público.</span>
</div>
```

## Horizontal Layout

```html
<div class="row g-3">
    <div class="col-md-3">
        <label class="form-label">Comentário</label>
    </div>
    <div class="col-md-9">
        <textarea class="form-control" rows="4" name="comment"></textarea>
    </div>
</div>
```

## Complete Example

```html
<form>
    <div class="row g-4">
        <div class="col-12">
            <div class="form-group">
                <label class="form-label" for="title">Título <span class="text-danger">*</span></label>
                <input type="text"
                       class="form-control"
                       id="title"
                       name="title"
                       required>
            </div>
        </div>
        <div class="col-12">
            <div class="form-group">
                <label class="form-label" for="content">Conteúdo <span class="text-danger">*</span></label>
                <textarea class="form-control {% if errors.content %}is-invalid{% endif %}"
                          id="content"
                          name="content"
                          rows="8"
                          placeholder="Digite o conteúdo do post..."
                          required>{{ form.content or '' }}</textarea>
                {% if errors.content %}
                <div class="invalid-feedback">{{ errors.content }}</div>
                {% endif %}
                <span class="form-note">Use markdown para formatação.</span>
            </div>
        </div>
        <div class="col-12">
            <div class="form-group">
                <label class="form-label" for="excerpt">Resumo</label>
                <textarea class="form-control"
                          id="excerpt"
                          name="excerpt"
                          rows="2"
                          maxlength="200"
                          placeholder="Breve descrição (opcional)">{{ form.excerpt or '' }}</textarea>
            </div>
        </div>
    </div>
</form>
```

## DO NOT

- Don't use `resize: none` unless absolutely necessary
- Don't set `rows` too small for the expected content
- Don't forget `name` attribute for form submission
- Don't use `<input type="text">` when multiline text is expected
