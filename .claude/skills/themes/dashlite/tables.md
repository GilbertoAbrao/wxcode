---
name: dashlite-tables
description: Tabelas DashLite - nk-tb, DataTables, actions, pagination
depends-on: [dashlite-_index]
---

# DashLite: Tables

DashLite has two table systems: the custom `.nk-tb` classes and standard Bootstrap tables with DataTables.

## NioTable (nk-tb) - Recommended

### Basic Structure

```html
<div class="nk-tb-list nk-tb-ulist">
    <div class="nk-tb-item nk-tb-head">
        <div class="nk-tb-col"><span class="sub-text">Nome</span></div>
        <div class="nk-tb-col tb-col-md"><span class="sub-text">Email</span></div>
        <div class="nk-tb-col tb-col-lg"><span class="sub-text">Telefone</span></div>
        <div class="nk-tb-col tb-col-md"><span class="sub-text">Status</span></div>
        <div class="nk-tb-col nk-tb-col-tools text-end"></div>
    </div>
    {% for item in items %}
    <div class="nk-tb-item">
        <div class="nk-tb-col">
            <span class="tb-lead">{{ item.name }}</span>
        </div>
        <div class="nk-tb-col tb-col-md">
            <span>{{ item.email }}</span>
        </div>
        <div class="nk-tb-col tb-col-lg">
            <span>{{ item.phone }}</span>
        </div>
        <div class="nk-tb-col tb-col-md">
            <span class="badge badge-dot bg-success">Ativo</span>
        </div>
        <div class="nk-tb-col nk-tb-col-tools">
            <ul class="nk-tb-actions gx-1">
                <li>
                    <a href="#" class="btn btn-trigger btn-icon" title="Editar">
                        <em class="icon ni ni-edit"></em>
                    </a>
                </li>
                <li>
                    <a href="#" class="btn btn-trigger btn-icon" title="Excluir">
                        <em class="icon ni ni-trash"></em>
                    </a>
                </li>
            </ul>
        </div>
    </div>
    {% endfor %}
</div>
```

### Responsive Column Classes

| Class | Visible |
|-------|---------|
| (none) | Always visible |
| `.tb-col-sm` | Hidden on XS, visible SM+ |
| `.tb-col-md` | Hidden on XS/SM, visible MD+ |
| `.tb-col-lg` | Hidden below LG, visible LG+ |
| `.tb-col-xl` | Hidden below XL, visible XL+ |

### With Checkbox Selection

```html
<div class="nk-tb-list nk-tb-ulist">
    <div class="nk-tb-item nk-tb-head">
        <div class="nk-tb-col nk-tb-col-check">
            <div class="custom-control custom-control-sm custom-checkbox notext">
                <input type="checkbox" class="custom-control-input" id="selectAll">
                <label class="custom-control-label" for="selectAll"></label>
            </div>
        </div>
        <div class="nk-tb-col"><span class="sub-text">Nome</span></div>
        <!-- more columns -->
    </div>
    {% for item in items %}
    <div class="nk-tb-item">
        <div class="nk-tb-col nk-tb-col-check">
            <div class="custom-control custom-control-sm custom-checkbox notext">
                <input type="checkbox" class="custom-control-input" id="item{{ item.id }}">
                <label class="custom-control-label" for="item{{ item.id }}"></label>
            </div>
        </div>
        <div class="nk-tb-col">
            <span class="tb-lead">{{ item.name }}</span>
        </div>
        <!-- more columns -->
    </div>
    {% endfor %}
</div>
```

### With User Avatar

```html
<div class="nk-tb-col">
    <div class="user-card">
        <div class="user-avatar bg-primary">
            <span>{{ item.name[:2]|upper }}</span>
        </div>
        <div class="user-info">
            <span class="tb-lead">{{ item.name }}</span>
            <span class="text-soft">{{ item.role }}</span>
        </div>
    </div>
</div>
```

### Action Dropdown

```html
<div class="nk-tb-col nk-tb-col-tools">
    <ul class="nk-tb-actions gx-1">
        <li>
            <div class="drodown">
                <a href="#" class="dropdown-toggle btn btn-icon btn-trigger" data-bs-toggle="dropdown">
                    <em class="icon ni ni-more-h"></em>
                </a>
                <div class="dropdown-menu dropdown-menu-end">
                    <ul class="link-list-opt no-bdr">
                        <li>
                            <a href="#">
                                <em class="icon ni ni-eye"></em>
                                <span>Ver Detalhes</span>
                            </a>
                        </li>
                        <li>
                            <a href="#">
                                <em class="icon ni ni-edit"></em>
                                <span>Editar</span>
                            </a>
                        </li>
                        <li class="divider"></li>
                        <li>
                            <a href="#" class="text-danger">
                                <em class="icon ni ni-trash"></em>
                                <span>Excluir</span>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </li>
    </ul>
</div>
```

## Bootstrap Table with DataTables

### Basic DataTable

```html
<table class="datatable-init table" data-auto-responsive="false">
    <thead>
        <tr>
            <th>Nome</th>
            <th>Email</th>
            <th>Status</th>
            <th class="nk-tb-col-tools text-end">Ações</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.name }}</td>
            <td>{{ item.email }}</td>
            <td>
                <span class="badge badge-dot bg-success">Ativo</span>
            </td>
            <td class="nk-tb-col-tools text-end">
                <a href="#" class="btn btn-sm btn-icon btn-trigger">
                    <em class="icon ni ni-edit"></em>
                </a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### DataTable Options

```html
<table class="datatable-init-export nowrap table"
       data-export-title="Relatório"
       data-auto-responsive="false">
    <!-- Export buttons will be added automatically -->
</table>
```

### Table with Search and Filter

```html
<div class="card card-bordered card-preview">
    <div class="card-inner">
        <table class="datatable-init table"
               data-auto-responsive="false"
               data-search="true">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome</th>
                    <th>Categoria</th>
                    <th>Valor</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <!-- rows -->
            </tbody>
        </table>
    </div>
</div>
```

## Status Badges

```html
<!-- Success -->
<span class="badge badge-dot bg-success">Ativo</span>

<!-- Warning -->
<span class="badge badge-dot bg-warning">Pendente</span>

<!-- Danger -->
<span class="badge badge-dot bg-danger">Inativo</span>

<!-- Info -->
<span class="badge badge-dot bg-info">Processando</span>

<!-- Secondary -->
<span class="badge badge-dot bg-secondary">Rascunho</span>
```

### Badge with Status Text (Jinja2)

```html
{% if item.status == 'active' %}
<span class="badge badge-dot bg-success">Ativo</span>
{% elif item.status == 'pending' %}
<span class="badge badge-dot bg-warning">Pendente</span>
{% elif item.status == 'inactive' %}
<span class="badge badge-dot bg-danger">Inativo</span>
{% else %}
<span class="badge badge-dot bg-secondary">{{ item.status }}</span>
{% endif %}
```

## Pagination

### Standard Pagination

```html
<div class="card-inner">
    <div class="nk-block-between-md g-3">
        <div class="g">
            <p class="text-soft">Mostrando {{ start }} a {{ end }} de {{ total }} registros</p>
        </div>
        <div class="g">
            <ul class="pagination justify-content-center justify-content-md-end">
                <li class="page-item {% if page == 1 %}disabled{% endif %}">
                    <a class="page-link" href="?page={{ page - 1 }}">Anterior</a>
                </li>
                {% for p in range(1, total_pages + 1) %}
                <li class="page-item {% if p == page %}active{% endif %}">
                    <a class="page-link" href="?page={{ p }}">{{ p }}</a>
                </li>
                {% endfor %}
                <li class="page-item {% if page == total_pages %}disabled{% endif %}">
                    <a class="page-link" href="?page={{ page + 1 }}">Próximo</a>
                </li>
            </ul>
        </div>
    </div>
</div>
```

### Compact Pagination

```html
<ul class="pagination pagination-sm">
    <li class="page-item"><a class="page-link" href="#">«</a></li>
    <li class="page-item active"><a class="page-link" href="#">1</a></li>
    <li class="page-item"><a class="page-link" href="#">2</a></li>
    <li class="page-item"><a class="page-link" href="#">»</a></li>
</ul>
```

## Table Toolbar

```html
<div class="card-inner position-relative card-tools-toggle">
    <div class="card-title-group">
        <div class="card-tools">
            <div class="form-inline flex-nowrap gx-3">
                <div class="form-wrap w-150px">
                    <select class="form-select form-select-sm js-select2" data-placeholder="Status">
                        <option value="">Todos</option>
                        <option value="active">Ativos</option>
                        <option value="inactive">Inativos</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="card-tools me-n1">
            <ul class="btn-toolbar gx-1">
                <li>
                    <div class="form-control-wrap">
                        <div class="form-icon form-icon-left">
                            <em class="icon ni ni-search"></em>
                        </div>
                        <input type="text" class="form-control form-control-sm" placeholder="Buscar...">
                    </div>
                </li>
                <li>
                    <a href="#" class="btn btn-icon btn-trigger" title="Exportar">
                        <em class="icon ni ni-download-cloud"></em>
                    </a>
                </li>
            </ul>
        </div>
    </div>
</div>
```

## Empty State

```html
{% if not items %}
<div class="nk-tb-item">
    <div class="nk-tb-col text-center py-4">
        <em class="icon ni ni-inbox icon-lg text-soft mb-2"></em>
        <p class="text-soft">Nenhum registro encontrado</p>
    </div>
</div>
{% endif %}
```

## Complete Example with Card

```html
<div class="card card-bordered card-preview">
    <div class="card-inner-group">
        <!-- Header -->
        <div class="card-inner position-relative card-tools-toggle">
            <div class="card-title-group">
                <div class="card-title">
                    <h5 class="title">Lista de Usuários</h5>
                </div>
                <div class="card-tools me-n1">
                    <ul class="btn-toolbar gx-1">
                        <li>
                            <a href="#" class="btn btn-icon btn-trigger" title="Filtros">
                                <em class="icon ni ni-filter-alt"></em>
                            </a>
                        </li>
                        <li>
                            <div class="form-control-wrap">
                                <div class="form-icon form-icon-left">
                                    <em class="icon ni ni-search"></em>
                                </div>
                                <input type="text" class="form-control form-control-sm" placeholder="Buscar">
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Table -->
        <div class="card-inner p-0">
            <div class="nk-tb-list nk-tb-ulist">
                <div class="nk-tb-item nk-tb-head">
                    <div class="nk-tb-col nk-tb-col-check">
                        <div class="custom-control custom-control-sm custom-checkbox notext">
                            <input type="checkbox" class="custom-control-input" id="selectAll">
                            <label class="custom-control-label" for="selectAll"></label>
                        </div>
                    </div>
                    <div class="nk-tb-col"><span class="sub-text">Usuário</span></div>
                    <div class="nk-tb-col tb-col-md"><span class="sub-text">Email</span></div>
                    <div class="nk-tb-col tb-col-lg"><span class="sub-text">Telefone</span></div>
                    <div class="nk-tb-col tb-col-md"><span class="sub-text">Status</span></div>
                    <div class="nk-tb-col nk-tb-col-tools text-end"></div>
                </div>

                {% for user in users %}
                <div class="nk-tb-item">
                    <div class="nk-tb-col nk-tb-col-check">
                        <div class="custom-control custom-control-sm custom-checkbox notext">
                            <input type="checkbox" class="custom-control-input" id="user{{ user.id }}">
                            <label class="custom-control-label" for="user{{ user.id }}"></label>
                        </div>
                    </div>
                    <div class="nk-tb-col">
                        <div class="user-card">
                            <div class="user-avatar bg-primary">
                                <span>{{ user.name[:2]|upper }}</span>
                            </div>
                            <div class="user-info">
                                <span class="tb-lead">{{ user.name }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="nk-tb-col tb-col-md">
                        <span>{{ user.email }}</span>
                    </div>
                    <div class="nk-tb-col tb-col-lg">
                        <span>{{ user.phone or '-' }}</span>
                    </div>
                    <div class="nk-tb-col tb-col-md">
                        {% if user.is_active %}
                        <span class="badge badge-dot bg-success">Ativo</span>
                        {% else %}
                        <span class="badge badge-dot bg-danger">Inativo</span>
                        {% endif %}
                    </div>
                    <div class="nk-tb-col nk-tb-col-tools">
                        <ul class="nk-tb-actions gx-1">
                            <li>
                                <div class="drodown">
                                    <a href="#" class="dropdown-toggle btn btn-icon btn-trigger" data-bs-toggle="dropdown">
                                        <em class="icon ni ni-more-h"></em>
                                    </a>
                                    <div class="dropdown-menu dropdown-menu-end">
                                        <ul class="link-list-opt no-bdr">
                                            <li>
                                                <a href="{{ url_for('users.edit', user_id=user.id) }}">
                                                    <em class="icon ni ni-edit"></em>
                                                    <span>Editar</span>
                                                </a>
                                            </li>
                                            <li class="divider"></li>
                                            <li>
                                                <a href="#" class="text-danger" onclick="confirmDelete({{ user.id }})">
                                                    <em class="icon ni ni-trash"></em>
                                                    <span>Excluir</span>
                                                </a>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
                {% else %}
                <div class="nk-tb-item">
                    <div class="nk-tb-col text-center py-4" colspan="6">
                        <p class="text-soft">Nenhum usuário encontrado</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Pagination -->
        <div class="card-inner">
            <div class="nk-block-between-md g-3">
                <div class="g">
                    <p class="text-soft">Mostrando {{ pagination.start }} a {{ pagination.end }} de {{ pagination.total }}</p>
                </div>
                <div class="g">
                    <ul class="pagination justify-content-center justify-content-md-end">
                        <li class="page-item {% if pagination.page == 1 %}disabled{% endif %}">
                            <a class="page-link" href="?page={{ pagination.page - 1 }}">Anterior</a>
                        </li>
                        {% for p in pagination.pages %}
                        <li class="page-item {% if p == pagination.page %}active{% endif %}">
                            <a class="page-link" href="?page={{ p }}">{{ p }}</a>
                        </li>
                        {% endfor %}
                        <li class="page-item {% if pagination.page >= pagination.total_pages %}disabled{% endif %}">
                            <a class="page-link" href="?page={{ pagination.page + 1 }}">Próximo</a>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
```

## DO NOT

- Don't use standard `<table>` for complex lists - use `.nk-tb-list`
- Don't forget responsive column classes (`.tb-col-md`, etc.)
- Don't inline action buttons - use dropdown for 3+ actions
- Don't forget empty state when list is empty
