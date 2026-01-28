---
name: dashlite-navigation-breadcrumb
description: Breadcrumbs DashLite - navegação hierárquica
depends-on: [dashlite-_index]
---

# DashLite: Breadcrumbs

## Basic Breadcrumb

```html
<nav>
    <ul class="breadcrumb breadcrumb-arrow">
        <li class="breadcrumb-item"><a href="/">Dashboard</a></li>
        <li class="breadcrumb-item"><a href="/clientes">Clientes</a></li>
        <li class="breadcrumb-item active">Detalhes</li>
    </ul>
</nav>
```

## Breadcrumb Styles

### Arrow Style (Default)

```html
<ul class="breadcrumb breadcrumb-arrow">
    <li class="breadcrumb-item"><a href="/">Home</a></li>
    <li class="breadcrumb-item"><a href="/produtos">Produtos</a></li>
    <li class="breadcrumb-item active">Editar</li>
</ul>
```

### Pipe Style

```html
<ul class="breadcrumb breadcrumb-pipe">
    <li class="breadcrumb-item"><a href="/">Home</a></li>
    <li class="breadcrumb-item"><a href="/produtos">Produtos</a></li>
    <li class="breadcrumb-item active">Editar</li>
</ul>
```

### Simple Style

```html
<ul class="breadcrumb">
    <li class="breadcrumb-item"><a href="/">Home</a></li>
    <li class="breadcrumb-item"><a href="/produtos">Produtos</a></li>
    <li class="breadcrumb-item active">Editar</li>
</ul>
```

## In Page Header

DashLite breadcrumbs are typically placed in the page header:

```html
<div class="nk-block-head nk-block-head-sm">
    <div class="nk-block-between">
        <div class="nk-block-head-content">
            <nav>
                <ul class="breadcrumb breadcrumb-arrow">
                    <li class="breadcrumb-item"><a href="/">Dashboard</a></li>
                    <li class="breadcrumb-item"><a href="/clientes">Clientes</a></li>
                    <li class="breadcrumb-item active">{{ cliente.nome }}</li>
                </ul>
            </nav>
            <h3 class="nk-block-title page-title">Detalhes do Cliente</h3>
        </div>
        <div class="nk-block-head-content">
            <div class="toggle-wrap nk-block-tools-toggle">
                <a href="/clientes/{{ cliente.id }}/editar" class="btn btn-primary">
                    <em class="icon ni ni-edit"></em>
                    <span>Editar</span>
                </a>
            </div>
        </div>
    </div>
</div>
```

## With Jinja2 Loop

```html
<nav>
    <ul class="breadcrumb breadcrumb-arrow">
        {% for crumb in breadcrumbs %}
        {% if loop.last %}
        <li class="breadcrumb-item active">{{ crumb.label }}</li>
        {% else %}
        <li class="breadcrumb-item"><a href="{{ crumb.url }}">{{ crumb.label }}</a></li>
        {% endif %}
        {% endfor %}
    </ul>
</nav>
```

## With Home Icon

```html
<nav>
    <ul class="breadcrumb breadcrumb-arrow">
        <li class="breadcrumb-item">
            <a href="/">
                <em class="icon ni ni-home"></em>
            </a>
        </li>
        <li class="breadcrumb-item"><a href="/clientes">Clientes</a></li>
        <li class="breadcrumb-item active">Detalhes</li>
    </ul>
</nav>
```

## Complete Page Header with Breadcrumb

```html
<div class="nk-content">
    <div class="container-fluid">
        <div class="nk-content-inner">
            <div class="nk-content-body">
                <!-- Page Header -->
                <div class="nk-block-head nk-block-head-sm">
                    <div class="nk-block-between g-3">
                        <div class="nk-block-head-content">
                            <nav>
                                <ul class="breadcrumb breadcrumb-arrow">
                                    <li class="breadcrumb-item">
                                        <a href="/"><em class="icon ni ni-home"></em></a>
                                    </li>
                                    <li class="breadcrumb-item"><a href="/clientes">Clientes</a></li>
                                    <li class="breadcrumb-item active">{{ cliente.nome }}</li>
                                </ul>
                            </nav>
                            <h3 class="nk-block-title page-title">
                                Detalhes do Cliente <span class="text-primary small">/ {{ cliente.codigo }}</span>
                            </h3>
                            <div class="nk-block-des text-soft">
                                <p>Visualize e gerencie as informações do cliente.</p>
                            </div>
                        </div>
                        <div class="nk-block-head-content">
                            <a href="/clientes" class="btn btn-outline-light bg-white d-none d-sm-inline-flex">
                                <em class="icon ni ni-arrow-left"></em>
                                <span>Voltar</span>
                            </a>
                            <a href="/clientes" class="btn btn-icon btn-outline-light bg-white d-inline-flex d-sm-none">
                                <em class="icon ni ni-arrow-left"></em>
                            </a>
                        </div>
                    </div>
                </div>
                <!-- Page Content -->
                <div class="nk-block">
                    <!-- content here -->
                </div>
            </div>
        </div>
    </div>
</div>
```

## Breadcrumb Macro (Jinja2)

```html
{% macro breadcrumb(items) %}
<nav>
    <ul class="breadcrumb breadcrumb-arrow">
        <li class="breadcrumb-item">
            <a href="/"><em class="icon ni ni-home"></em></a>
        </li>
        {% for item in items %}
        {% if loop.last %}
        <li class="breadcrumb-item active">{{ item.label }}</li>
        {% else %}
        <li class="breadcrumb-item"><a href="{{ item.url }}">{{ item.label }}</a></li>
        {% endif %}
        {% endfor %}
    </ul>
</nav>
{% endmacro %}

<!-- Usage -->
{{ breadcrumb([
    {'url': '/clientes', 'label': 'Clientes'},
    {'url': '', 'label': 'Detalhes'}
]) }}
```

## DO NOT

- Don't use Bootstrap standard breadcrumb without DashLite classes
- Don't add links to the active (last) item
- Don't forget the `active` class on the last item
- Don't omit the `<nav>` wrapper element
