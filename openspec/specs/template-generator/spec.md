# template-generator Specification

## Purpose
TBD - created by archiving change generate-fastapi-jinja2. Update Purpose after archive.
## Requirements
### Requirement: Generate base template with common structure

O sistema MUST gerar template base com estrutura HTML comum.

#### Scenario: Base template

**When** TemplateGenerator.generate() é executado

**Then** deve gerar `templates/base.html` com:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ project_name }}{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    {% block head %}{% endblock %}
</head>
<body>
    {% include "components/navbar.html" %}

    <main class="container">
        {% block content %}{% endblock %}
    </main>

    <script src="/static/js/main.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

---

### Requirement: Generate page templates from Element and Controls

O sistema MUST gerar templates para cada página baseado nos controles.

#### Scenario: Página de formulário

**Given** uma página PAGE_FORM_Cliente com controles:
- EDT_Nome (Edit, binding: CLIENTE.nome)
- EDT_Email (Edit, binding: CLIENTE.email)
- BTN_Salvar (Button, evento OnClick)

**When** o template é gerado

**Then** deve gerar `templates/pages/form_cliente.html`:
```html
{% extends "base.html" %}

{% block title %}Cadastro de Cliente{% endblock %}

{% block content %}
<form method="post" action="/form/cliente">
    <div class="form-group">
        <label for="nome">Nome</label>
        <input type="text" id="nome" name="nome"
               value="{{ cliente.nome if cliente else '' }}"
               class="form-control">
    </div>

    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email"
               value="{{ cliente.email if cliente else '' }}"
               class="form-control">
    </div>

    <button type="submit" class="btn btn-primary">Salvar</button>
</form>
{% endblock %}
```

#### Scenario: Página de listagem

**Given** uma página PAGE_LIST_Clientes com controles:
- TABLE_Clientes (Table, binding: CLIENTE)
- BTN_Novo (Button)
- BTN_Editar (Button)

**When** o template é gerado

**Then** deve gerar `templates/pages/list_clientes.html`:
```html
{% extends "base.html" %}

{% block title %}Lista de Clientes{% endblock %}

{% block content %}
<div class="toolbar">
    <a href="/form/cliente" class="btn btn-primary">Novo</a>
</div>

<table class="table">
    <thead>
        <tr>
            <th>Nome</th>
            <th>Email</th>
            <th>Ações</th>
        </tr>
    </thead>
    <tbody>
        {% for cliente in clientes %}
        <tr>
            <td>{{ cliente.nome }}</td>
            <td>{{ cliente.email }}</td>
            <td>
                <a href="/form/cliente/{{ cliente.id }}" class="btn btn-sm">Editar</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

---

### Requirement: Map control types to HTML elements

O sistema MUST mapear tipos de controle para elementos HTML apropriados.

#### Scenario: Edit control

**Given** um controle do tipo Edit (type_code=8)

**When** o HTML é gerado

**Then** deve gerar `<input type="text">`

#### Scenario: Edit com input_type numérico

**Given** um controle Edit com properties.input_type = "Numeric"

**When** o HTML é gerado

**Then** deve gerar `<input type="number">`

#### Scenario: Combo/Select

**Given** um controle do tipo Combo

**When** o HTML é gerado

**Then** deve gerar:
```html
<select name="campo" class="form-control">
    {% for option in options %}
    <option value="{{ option.value }}">{{ option.label }}</option>
    {% endfor %}
</select>
```

#### Scenario: Check (Checkbox)

**Given** um controle do tipo Check

**When** o HTML é gerado

**Then** deve gerar `<input type="checkbox">`

#### Scenario: Table

**Given** um controle do tipo Table

**When** o HTML é gerado

**Then** deve gerar estrutura `<table>` com colunas baseadas em bindings

---

### Requirement: Use data_binding for form field names

O sistema MUST usar data_binding para definir names dos campos.

#### Scenario: Campo com binding simples

**Given** um controle EDT_Nome com data_binding:
- table_name: CLIENTE
- field_name: nome

**When** o HTML é gerado

**Then** deve usar: `name="nome"` e `value="{{ cliente.nome }}"`

#### Scenario: Campo com binding de variável

**Given** um controle com data_binding:
- binding_type: VARIABLE
- variable_name: gsFilter

**When** o HTML é gerado

**Then** deve usar: `name="gs_filter"` e `value="{{ gs_filter }}"`

---

### Requirement: Preserve control hierarchy

O sistema MUST preservar hierarquia de controles (containers).

#### Scenario: Controles dentro de CELL

**Given** uma página com:
- CELL_Form (container)
  - EDT_Nome
  - EDT_Email
- CELL_Buttons
  - BTN_Salvar

**When** o template é gerado

**Then** deve gerar:
```html
<div class="cell" id="cell_form">
    <input type="text" name="nome" ...>
    <input type="email" name="email" ...>
</div>
<div class="cell" id="cell_buttons">
    <button type="submit">Salvar</button>
</div>
```

---

### Requirement: Detect page type automatically

O sistema MUST detectar automaticamente o tipo de página.

#### Scenario: Página de formulário

**Given** uma página com maioria de controles Edit e botão Submit

**When** o tipo é detectado

**Then** deve retornar "form"

#### Scenario: Página de listagem

**Given** uma página com controle Table principal

**When** o tipo é detectado

**Then** deve retornar "list"

#### Scenario: Página de dashboard

**Given** uma página com múltiplos containers e gráficos

**When** o tipo é detectado

**Then** deve retornar "dashboard"

---

### Requirement: Generate reusable components

O sistema MUST gerar componentes reutilizáveis.

#### Scenario: Navbar component

**When** a geração é concluída

**Then** deve gerar `templates/components/navbar.html`

#### Scenario: Form field component

**When** a geração é concluída

**Then** deve gerar `templates/components/form_field.html`:
```html
{% macro form_field(name, label, type="text", value="", required=false) %}
<div class="form-group">
    <label for="{{ name }}">{{ label }}</label>
    <input type="{{ type }}" id="{{ name }}" name="{{ name }}"
           value="{{ value }}" class="form-control"
           {% if required %}required{% endif %}>
</div>
{% endmacro %}
```

