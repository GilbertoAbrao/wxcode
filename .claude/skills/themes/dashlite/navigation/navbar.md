---
name: dashlite-navigation-navbar
description: Top navbar DashLite - header, dropdowns, notifications
depends-on: [dashlite-_index]
---

# DashLite: Top Navbar

## Basic Structure

```html
<div class="nk-header nk-header-fixed is-light">
    <div class="container-fluid">
        <div class="nk-header-wrap">
            <div class="nk-menu-trigger d-xl-none ms-n1">
                <a href="#" class="nk-nav-toggle nk-quick-nav-icon" data-target="sidebarMenu">
                    <em class="icon ni ni-menu"></em>
                </a>
            </div>
            <div class="nk-header-brand d-xl-none">
                <a href="/" class="logo-link">
                    <img class="logo-light logo-img" src="/static/img/logo.png" alt="logo">
                    <img class="logo-dark logo-img" src="/static/img/logo-dark.png" alt="logo-dark">
                </a>
            </div>
            <div class="nk-header-tools">
                <ul class="nk-quick-nav">
                    <!-- Quick nav items here -->
                </ul>
            </div>
        </div>
    </div>
</div>
```

## Header Variants

| Class | Effect |
|-------|--------|
| `.is-light` | Light background |
| `.is-dark` | Dark background |
| `.is-theme` | Theme color background |

## Quick Nav Items

### Notifications

```html
<li class="dropdown notification-dropdown">
    <a href="#" class="dropdown-toggle nk-quick-nav-icon" data-bs-toggle="dropdown">
        <div class="icon-status icon-status-info">
            <em class="icon ni ni-bell"></em>
        </div>
    </a>
    <div class="dropdown-menu dropdown-menu-xl dropdown-menu-end">
        <div class="dropdown-head">
            <span class="sub-title nk-dropdown-title">Notificações</span>
            <a href="#">Marcar todas como lidas</a>
        </div>
        <div class="dropdown-body">
            <div class="nk-notification">
                <div class="nk-notification-item dropdown-inner">
                    <div class="nk-notification-icon">
                        <em class="icon icon-circle bg-warning-dim ni ni-curve-down-right"></em>
                    </div>
                    <div class="nk-notification-content">
                        <div class="nk-notification-text">
                            Você recebeu uma nova mensagem
                        </div>
                        <div class="nk-notification-time">2 horas atrás</div>
                    </div>
                </div>
                <!-- more notifications -->
            </div>
        </div>
        <div class="dropdown-foot center">
            <a href="#">Ver todas</a>
        </div>
    </div>
</li>
```

### User Dropdown

```html
<li class="dropdown user-dropdown">
    <a href="#" class="dropdown-toggle me-n1" data-bs-toggle="dropdown">
        <div class="user-toggle">
            <div class="user-avatar sm">
                <em class="icon ni ni-user-alt"></em>
            </div>
            <div class="user-info d-none d-xl-block">
                <div class="user-status user-status-active">{{ current_user.role }}</div>
                <div class="user-name dropdown-indicator">{{ current_user.name }}</div>
            </div>
        </div>
    </a>
    <div class="dropdown-menu dropdown-menu-md dropdown-menu-end">
        <div class="dropdown-inner user-card-wrap bg-lighter d-none d-md-block">
            <div class="user-card">
                <div class="user-avatar">
                    <span>{{ current_user.name[:2]|upper }}</span>
                </div>
                <div class="user-info">
                    <span class="lead-text">{{ current_user.name }}</span>
                    <span class="sub-text">{{ current_user.email }}</span>
                </div>
            </div>
        </div>
        <div class="dropdown-inner">
            <ul class="link-list">
                <li>
                    <a href="/perfil">
                        <em class="icon ni ni-user-alt"></em>
                        <span>Meu Perfil</span>
                    </a>
                </li>
                <li>
                    <a href="/configuracoes">
                        <em class="icon ni ni-setting-alt"></em>
                        <span>Configurações</span>
                    </a>
                </li>
            </ul>
        </div>
        <div class="dropdown-inner">
            <ul class="link-list">
                <li>
                    <a href="/logout">
                        <em class="icon ni ni-signout"></em>
                        <span>Sair</span>
                    </a>
                </li>
            </ul>
        </div>
    </div>
</li>
```

### Dark Mode Toggle

```html
<li class="dropdown">
    <a class="dropdown-toggle nk-quick-nav-icon" data-bs-toggle="dropdown">
        <div class="icon-status icon-status-na">
            <em class="icon ni ni-moon"></em>
        </div>
    </a>
    <div class="dropdown-menu dropdown-menu-end">
        <ul class="link-list-opt no-bdr">
            <li>
                <a class="dark-switch" href="#">
                    <span>Modo Escuro</span>
                </a>
            </li>
        </ul>
    </div>
</li>
```

### Search Toggle

```html
<li class="dropdown">
    <a href="#" class="dropdown-toggle nk-quick-nav-icon" data-bs-toggle="dropdown">
        <em class="icon ni ni-search"></em>
    </a>
    <div class="dropdown-menu dropdown-menu-xl dropdown-menu-end">
        <div class="dropdown-head">
            <span class="sub-title nk-dropdown-title">Busca Rápida</span>
        </div>
        <div class="dropdown-body">
            <div class="form-group">
                <div class="form-control-wrap">
                    <input type="text" class="form-control form-control-lg" placeholder="Buscar...">
                </div>
            </div>
        </div>
    </div>
</li>
```

## Header with Search Bar

```html
<div class="nk-header nk-header-fixed is-light">
    <div class="container-fluid">
        <div class="nk-header-wrap">
            <div class="nk-menu-trigger d-xl-none ms-n1">
                <a href="#" class="nk-nav-toggle nk-quick-nav-icon" data-target="sidebarMenu">
                    <em class="icon ni ni-menu"></em>
                </a>
            </div>
            <div class="nk-header-search ms-3 ms-xl-0">
                <em class="icon ni ni-search"></em>
                <input type="text" class="form-control border-transparent form-focus-none" placeholder="Buscar...">
            </div>
            <div class="nk-header-tools">
                <ul class="nk-quick-nav">
                    <!-- items -->
                </ul>
            </div>
        </div>
    </div>
</div>
```

## Complete Header Example

```html
<div class="nk-header nk-header-fixed is-light">
    <div class="container-fluid">
        <div class="nk-header-wrap">
            <!-- Mobile Menu Toggle -->
            <div class="nk-menu-trigger d-xl-none ms-n1">
                <a href="#" class="nk-nav-toggle nk-quick-nav-icon" data-target="sidebarMenu">
                    <em class="icon ni ni-menu"></em>
                </a>
            </div>

            <!-- Mobile Logo -->
            <div class="nk-header-brand d-xl-none">
                <a href="/" class="logo-link">
                    <img class="logo-light logo-img" src="{{ url_for('static', path='img/logo.png') }}" alt="logo">
                </a>
            </div>

            <!-- Header Tools -->
            <div class="nk-header-tools">
                <ul class="nk-quick-nav">
                    <!-- Search -->
                    <li class="dropdown d-none d-md-block">
                        <a href="#" class="dropdown-toggle nk-quick-nav-icon" data-bs-toggle="dropdown">
                            <em class="icon ni ni-search"></em>
                        </a>
                        <div class="dropdown-menu dropdown-menu-xl dropdown-menu-end">
                            <div class="dropdown-body">
                                <div class="form-group">
                                    <div class="form-control-wrap">
                                        <input type="text" class="form-control form-control-lg" placeholder="Buscar...">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </li>

                    <!-- Notifications -->
                    <li class="dropdown notification-dropdown">
                        <a href="#" class="dropdown-toggle nk-quick-nav-icon" data-bs-toggle="dropdown">
                            <div class="icon-status icon-status-info">
                                <em class="icon ni ni-bell"></em>
                            </div>
                        </a>
                        <div class="dropdown-menu dropdown-menu-xl dropdown-menu-end">
                            <div class="dropdown-head">
                                <span class="sub-title nk-dropdown-title">Notificações</span>
                                <a href="#">Marcar como lidas</a>
                            </div>
                            <div class="dropdown-body">
                                <div class="nk-notification">
                                    {% for notif in notifications %}
                                    <div class="nk-notification-item dropdown-inner">
                                        <div class="nk-notification-icon">
                                            <em class="icon icon-circle bg-{{ notif.type }}-dim ni ni-{{ notif.icon }}"></em>
                                        </div>
                                        <div class="nk-notification-content">
                                            <div class="nk-notification-text">{{ notif.message }}</div>
                                            <div class="nk-notification-time">{{ notif.time }}</div>
                                        </div>
                                    </div>
                                    {% else %}
                                    <div class="nk-notification-item dropdown-inner">
                                        <div class="nk-notification-content text-center py-3">
                                            <p class="text-soft">Sem notificações</p>
                                        </div>
                                    </div>
                                    {% endfor %}
                                </div>
                            </div>
                            <div class="dropdown-foot center">
                                <a href="/notificacoes">Ver todas</a>
                            </div>
                        </div>
                    </li>

                    <!-- User Dropdown -->
                    <li class="dropdown user-dropdown">
                        <a href="#" class="dropdown-toggle me-n1" data-bs-toggle="dropdown">
                            <div class="user-toggle">
                                <div class="user-avatar sm">
                                    <span>{{ current_user.name[:2]|upper }}</span>
                                </div>
                                <div class="user-info d-none d-xl-block">
                                    <div class="user-status user-status-active">{{ current_user.role }}</div>
                                    <div class="user-name dropdown-indicator">{{ current_user.name }}</div>
                                </div>
                            </div>
                        </a>
                        <div class="dropdown-menu dropdown-menu-md dropdown-menu-end">
                            <div class="dropdown-inner user-card-wrap bg-lighter d-none d-md-block">
                                <div class="user-card">
                                    <div class="user-avatar">
                                        <span>{{ current_user.name[:2]|upper }}</span>
                                    </div>
                                    <div class="user-info">
                                        <span class="lead-text">{{ current_user.name }}</span>
                                        <span class="sub-text">{{ current_user.email }}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="dropdown-inner">
                                <ul class="link-list">
                                    <li>
                                        <a href="/perfil">
                                            <em class="icon ni ni-user-alt"></em>
                                            <span>Meu Perfil</span>
                                        </a>
                                    </li>
                                    <li>
                                        <a href="/configuracoes">
                                            <em class="icon ni ni-setting-alt"></em>
                                            <span>Configurações</span>
                                        </a>
                                    </li>
                                </ul>
                            </div>
                            <div class="dropdown-inner">
                                <ul class="link-list">
                                    <li>
                                        <a href="/logout">
                                            <em class="icon ni ni-signout"></em>
                                            <span>Sair</span>
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>
```

## DO NOT

- Don't forget mobile menu toggle (`d-xl-none`)
- Don't use standard Bootstrap navbar - use DashLite structure
- Don't forget `dropdown-menu-end` for right-aligned dropdowns
- Don't hardcode user info - use Jinja2 context
