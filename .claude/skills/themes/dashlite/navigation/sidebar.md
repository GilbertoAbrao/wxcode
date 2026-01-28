---
name: dashlite-navigation-sidebar
description: Sidebar/menu lateral DashLite - estrutura, menus, submenus
depends-on: [dashlite-_index]
---

# DashLite: Sidebar Navigation

## Basic Structure

```html
<div class="nk-sidebar nk-sidebar-fixed is-light" data-content="sidebarMenu">
    <div class="nk-sidebar-element nk-sidebar-head">
        <div class="nk-sidebar-brand">
            <a href="/" class="logo-link nk-sidebar-logo">
                <img class="logo-light logo-img" src="/static/img/logo.png" alt="logo">
                <img class="logo-dark logo-img" src="/static/img/logo-dark.png" alt="logo-dark">
                <span class="nio-version">Admin</span>
            </a>
        </div>
        <div class="nk-menu-trigger me-n2">
            <a href="#" class="nk-nav-toggle nk-quick-nav-icon d-xl-none" data-target="sidebarMenu">
                <em class="icon ni ni-arrow-left"></em>
            </a>
        </div>
    </div>
    <div class="nk-sidebar-element">
        <div class="nk-sidebar-content">
            <div class="nk-sidebar-menu" data-simplebar>
                <ul class="nk-menu">
                    <!-- Menu items here -->
                </ul>
            </div>
        </div>
    </div>
</div>
```

## Sidebar Variants

| Class | Effect |
|-------|--------|
| `.is-light` | Light background |
| `.is-dark` | Dark background |
| `.is-theme` | Theme color background |

## Menu Items

### Simple Menu Item

```html
<li class="nk-menu-item">
    <a href="/dashboard" class="nk-menu-link">
        <span class="nk-menu-icon">
            <em class="icon ni ni-dashboard"></em>
        </span>
        <span class="nk-menu-text">Dashboard</span>
    </a>
</li>
```

### Active Menu Item

```html
<li class="nk-menu-item active current-page">
    <a href="/dashboard" class="nk-menu-link">
        <span class="nk-menu-icon">
            <em class="icon ni ni-dashboard"></em>
        </span>
        <span class="nk-menu-text">Dashboard</span>
    </a>
</li>
```

### With Jinja2 Active State

```html
<li class="nk-menu-item {% if request.url.path == '/dashboard' %}active current-page{% endif %}">
    <a href="/dashboard" class="nk-menu-link">
        <span class="nk-menu-icon">
            <em class="icon ni ni-dashboard"></em>
        </span>
        <span class="nk-menu-text">Dashboard</span>
    </a>
</li>
```

## Submenus

### Submenu with Toggle

```html
<li class="nk-menu-item has-sub">
    <a href="#" class="nk-menu-link nk-menu-toggle">
        <span class="nk-menu-icon">
            <em class="icon ni ni-users"></em>
        </span>
        <span class="nk-menu-text">Usuários</span>
    </a>
    <ul class="nk-menu-sub">
        <li class="nk-menu-item">
            <a href="/usuarios" class="nk-menu-link">
                <span class="nk-menu-text">Listar</span>
            </a>
        </li>
        <li class="nk-menu-item">
            <a href="/usuarios/novo" class="nk-menu-link">
                <span class="nk-menu-text">Novo Usuário</span>
            </a>
        </li>
        <li class="nk-menu-item">
            <a href="/usuarios/grupos" class="nk-menu-link">
                <span class="nk-menu-text">Grupos</span>
            </a>
        </li>
    </ul>
</li>
```

### Active Submenu (Expanded)

```html
<li class="nk-menu-item has-sub active">
    <a href="#" class="nk-menu-link nk-menu-toggle">
        <span class="nk-menu-icon">
            <em class="icon ni ni-users"></em>
        </span>
        <span class="nk-menu-text">Usuários</span>
    </a>
    <ul class="nk-menu-sub" style="display: block;">
        <li class="nk-menu-item active current-page">
            <a href="/usuarios" class="nk-menu-link">
                <span class="nk-menu-text">Listar</span>
            </a>
        </li>
        <!-- more items -->
    </ul>
</li>
```

### With Jinja2 Loop

```html
{% for menu in sidebar_menu %}
<li class="nk-menu-item {% if menu.children %}has-sub{% endif %} {% if menu.is_active %}active{% endif %}">
    {% if menu.children %}
    <a href="#" class="nk-menu-link nk-menu-toggle">
        <span class="nk-menu-icon">
            <em class="icon ni ni-{{ menu.icon }}"></em>
        </span>
        <span class="nk-menu-text">{{ menu.label }}</span>
    </a>
    <ul class="nk-menu-sub" {% if menu.is_active %}style="display: block;"{% endif %}>
        {% for child in menu.children %}
        <li class="nk-menu-item {% if child.is_active %}active current-page{% endif %}">
            <a href="{{ child.url }}" class="nk-menu-link">
                <span class="nk-menu-text">{{ child.label }}</span>
            </a>
        </li>
        {% endfor %}
    </ul>
    {% else %}
    <a href="{{ menu.url }}" class="nk-menu-link">
        <span class="nk-menu-icon">
            <em class="icon ni ni-{{ menu.icon }}"></em>
        </span>
        <span class="nk-menu-text">{{ menu.label }}</span>
    </a>
    {% endif %}
</li>
{% endfor %}
```

## Menu Heading

```html
<li class="nk-menu-heading">
    <h6 class="overline-title text-primary-alt">Administração</h6>
</li>
```

## Menu with Badge

```html
<li class="nk-menu-item">
    <a href="/mensagens" class="nk-menu-link">
        <span class="nk-menu-icon">
            <em class="icon ni ni-mail"></em>
        </span>
        <span class="nk-menu-text">Mensagens</span>
        <span class="nk-menu-badge badge badge-primary">5</span>
    </a>
</li>
```

## Complete Sidebar Example

```html
<div class="nk-sidebar nk-sidebar-fixed is-light" data-content="sidebarMenu">
    <div class="nk-sidebar-element nk-sidebar-head">
        <div class="nk-sidebar-brand">
            <a href="/" class="logo-link nk-sidebar-logo">
                <img class="logo-light logo-img" src="{{ url_for('static', path='img/logo.png') }}" alt="logo">
                <img class="logo-dark logo-img" src="{{ url_for('static', path='img/logo-dark.png') }}" alt="logo-dark">
            </a>
        </div>
        <div class="nk-menu-trigger me-n2">
            <a href="#" class="nk-nav-toggle nk-quick-nav-icon d-xl-none" data-target="sidebarMenu">
                <em class="icon ni ni-arrow-left"></em>
            </a>
        </div>
    </div>
    <div class="nk-sidebar-element">
        <div class="nk-sidebar-content">
            <div class="nk-sidebar-menu" data-simplebar>
                <ul class="nk-menu">
                    <!-- Dashboard -->
                    <li class="nk-menu-item {% if request.url.path == '/' %}active current-page{% endif %}">
                        <a href="/" class="nk-menu-link">
                            <span class="nk-menu-icon"><em class="icon ni ni-dashboard"></em></span>
                            <span class="nk-menu-text">Dashboard</span>
                        </a>
                    </li>

                    <!-- Heading -->
                    <li class="nk-menu-heading">
                        <h6 class="overline-title text-primary-alt">Cadastros</h6>
                    </li>

                    <!-- Clientes -->
                    <li class="nk-menu-item has-sub {% if '/clientes' in request.url.path %}active{% endif %}">
                        <a href="#" class="nk-menu-link nk-menu-toggle">
                            <span class="nk-menu-icon"><em class="icon ni ni-users"></em></span>
                            <span class="nk-menu-text">Clientes</span>
                        </a>
                        <ul class="nk-menu-sub" {% if '/clientes' in request.url.path %}style="display: block;"{% endif %}>
                            <li class="nk-menu-item {% if request.url.path == '/clientes' %}active current-page{% endif %}">
                                <a href="/clientes" class="nk-menu-link">
                                    <span class="nk-menu-text">Listar</span>
                                </a>
                            </li>
                            <li class="nk-menu-item {% if request.url.path == '/clientes/novo' %}active current-page{% endif %}">
                                <a href="/clientes/novo" class="nk-menu-link">
                                    <span class="nk-menu-text">Novo Cliente</span>
                                </a>
                            </li>
                        </ul>
                    </li>

                    <!-- Produtos -->
                    <li class="nk-menu-item {% if request.url.path == '/produtos' %}active current-page{% endif %}">
                        <a href="/produtos" class="nk-menu-link">
                            <span class="nk-menu-icon"><em class="icon ni ni-package"></em></span>
                            <span class="nk-menu-text">Produtos</span>
                        </a>
                    </li>

                    <!-- Heading -->
                    <li class="nk-menu-heading">
                        <h6 class="overline-title text-primary-alt">Operações</h6>
                    </li>

                    <!-- Vendas -->
                    <li class="nk-menu-item has-sub {% if '/vendas' in request.url.path %}active{% endif %}">
                        <a href="#" class="nk-menu-link nk-menu-toggle">
                            <span class="nk-menu-icon"><em class="icon ni ni-cart"></em></span>
                            <span class="nk-menu-text">Vendas</span>
                        </a>
                        <ul class="nk-menu-sub" {% if '/vendas' in request.url.path %}style="display: block;"{% endif %}>
                            <li class="nk-menu-item">
                                <a href="/vendas" class="nk-menu-link">
                                    <span class="nk-menu-text">Listar</span>
                                </a>
                            </li>
                            <li class="nk-menu-item">
                                <a href="/vendas/nova" class="nk-menu-link">
                                    <span class="nk-menu-text">Nova Venda</span>
                                </a>
                            </li>
                        </ul>
                    </li>

                    <!-- Heading -->
                    <li class="nk-menu-heading">
                        <h6 class="overline-title text-primary-alt">Sistema</h6>
                    </li>

                    <!-- Configurações -->
                    <li class="nk-menu-item {% if request.url.path == '/configuracoes' %}active current-page{% endif %}">
                        <a href="/configuracoes" class="nk-menu-link">
                            <span class="nk-menu-icon"><em class="icon ni ni-setting"></em></span>
                            <span class="nk-menu-text">Configurações</span>
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>
```

## Common Menu Icons

| Icon | Class | Usage |
|------|-------|-------|
| Dashboard | `ni-dashboard` | Home/Dashboard |
| Users | `ni-users` | Clientes/Usuários |
| User | `ni-user` | Perfil |
| Package | `ni-package` | Produtos |
| Cart | `ni-cart` | Vendas/Pedidos |
| Wallet | `ni-wallet` | Financeiro |
| Report | `ni-reports` | Relatórios |
| Setting | `ni-setting` | Configurações |
| File | `ni-file-docs` | Documentos |
| Calendar | `ni-calendar` | Agenda |
| Mail | `ni-mail` | Mensagens |
| Help | `ni-help` | Ajuda |
| Signout | `ni-signout` | Sair |

## DO NOT

- Don't use standard `<nav>` - use `.nk-sidebar` structure
- Don't forget `data-simplebar` for scrollable content
- Don't forget `.has-sub` class for parent menus
- Don't hardcode active state - use Jinja2 conditions
