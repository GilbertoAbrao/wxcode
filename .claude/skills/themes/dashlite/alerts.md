---
name: dashlite-alerts
description: Alerts e toasts DashLite - notificações inline e popup
depends-on: [dashlite-_index]
---

# DashLite: Alerts & Notifications

## Inline Alerts

### Basic Alert

```html
<div class="alert alert-primary" role="alert">
    Mensagem informativa primária.
</div>
```

### Alert Variants

```html
<div class="alert alert-primary">Primary alert</div>
<div class="alert alert-secondary">Secondary alert</div>
<div class="alert alert-success">Success alert</div>
<div class="alert alert-danger">Danger alert</div>
<div class="alert alert-warning">Warning alert</div>
<div class="alert alert-info">Info alert</div>
<div class="alert alert-light">Light alert</div>
<div class="alert alert-dark">Dark alert</div>
```

### Dismissible Alert

```html
<div class="alert alert-success alert-dismissible fade show" role="alert">
    <strong>Sucesso!</strong> Registro salvo com sucesso.
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
```

### Alert with Icon

```html
<div class="alert alert-success alert-icon">
    <em class="icon ni ni-check-circle"></em>
    <strong>Sucesso!</strong> Operação realizada com sucesso.
</div>

<div class="alert alert-danger alert-icon">
    <em class="icon ni ni-cross-circle"></em>
    <strong>Erro!</strong> Ocorreu um erro ao processar sua solicitação.
</div>

<div class="alert alert-warning alert-icon">
    <em class="icon ni ni-alert-circle"></em>
    <strong>Atenção!</strong> Verifique os campos obrigatórios.
</div>

<div class="alert alert-info alert-icon">
    <em class="icon ni ni-info"></em>
    <strong>Informação:</strong> Este processo pode levar alguns minutos.
</div>
```

### Alert Pro (DashLite Special)

```html
<div class="alert alert-pro alert-primary">
    <div class="alert-text">
        <h6>Atenção</h6>
        <p>Mensagem detalhada com título destacado.</p>
    </div>
</div>

<div class="alert alert-pro alert-danger">
    <div class="alert-text">
        <h6>Erro Crítico</h6>
        <p>Não foi possível processar sua solicitação. Tente novamente mais tarde.</p>
    </div>
</div>
```

### Fill Alerts

```html
<div class="alert alert-fill alert-primary">
    Alert com fundo sólido primary.
</div>

<div class="alert alert-fill alert-success alert-icon">
    <em class="icon ni ni-check-circle"></em>
    Alert com fundo sólido e ícone.
</div>

<div class="alert alert-fill alert-danger alert-dismissible fade show">
    Alert com fundo sólido e dismiss.
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
```

## Flash Messages (Jinja2)

### Template Pattern

```html
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}
<div class="nk-block">
    {% for category, message in messages %}
    <div class="alert alert-{{ category }} alert-icon alert-dismissible fade show" role="alert">
        {% if category == 'success' %}
        <em class="icon ni ni-check-circle"></em>
        {% elif category == 'danger' or category == 'error' %}
        <em class="icon ni ni-cross-circle"></em>
        {% elif category == 'warning' %}
        <em class="icon ni ni-alert-circle"></em>
        {% else %}
        <em class="icon ni ni-info"></em>
        {% endif %}
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
{% endwith %}
```

### Macro for Flash Messages

```html
{% macro flash_messages() %}
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}
{% for category, message in messages %}
<div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-icon alert-dismissible fade show">
    {% if category == 'success' %}
    <em class="icon ni ni-check-circle"></em>
    {% elif category in ['danger', 'error'] %}
    <em class="icon ni ni-cross-circle"></em>
    {% elif category == 'warning' %}
    <em class="icon ni ni-alert-circle"></em>
    {% else %}
    <em class="icon ni ni-info"></em>
    {% endif %}
    {{ message }}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
{% endfor %}
{% endif %}
{% endwith %}
{% endmacro %}

<!-- Usage -->
{{ flash_messages() }}
```

## Toast Notifications

### Toast Container

```html
<div class="toast-container position-fixed top-0 end-0 p-3">
    <!-- Toasts will be added here -->
</div>
```

### Basic Toast

```html
<div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
    <div class="toast-header">
        <em class="icon ni ni-bell text-primary me-2"></em>
        <strong class="me-auto">Notificação</strong>
        <small class="text-muted">agora</small>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
    <div class="toast-body">
        Mensagem da notificação aqui.
    </div>
</div>
```

### Success Toast

```html
<div class="toast align-items-center text-white bg-success border-0" role="alert">
    <div class="d-flex">
        <div class="toast-body">
            <em class="icon ni ni-check me-2"></em>
            Registro salvo com sucesso!
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
</div>
```

### Error Toast

```html
<div class="toast align-items-center text-white bg-danger border-0" role="alert">
    <div class="d-flex">
        <div class="toast-body">
            <em class="icon ni ni-cross me-2"></em>
            Erro ao processar solicitação.
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
</div>
```

### JavaScript Toast Control

```html
<script>
// Show toast
function showToast(message, type = 'primary') {
    const toastContainer = document.querySelector('.toast-container');
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// Usage
showToast('Sucesso!', 'success');
showToast('Erro!', 'danger');
showToast('Atenção!', 'warning');
</script>
```

## NioApp Toaster (DashLite Built-in)

DashLite includes NioApp.Toast for notifications:

```html
<script>
// Success notification
NioApp.Toast('Registro salvo com sucesso!', 'success', {
    position: 'top-right'
});

// Error notification
NioApp.Toast('Erro ao processar!', 'error', {
    position: 'top-right'
});

// Warning notification
NioApp.Toast('Atenção!', 'warning', {
    position: 'top-right'
});

// Info notification
NioApp.Toast('Informação', 'info', {
    position: 'top-right'
});
</script>
```

## Alert Placement

### At Top of Page

```html
<div class="nk-content">
    <div class="container-fluid">
        <div class="nk-content-inner">
            <div class="nk-content-body">
                <!-- Alerts first -->
                {% if error %}
                <div class="alert alert-danger alert-icon alert-dismissible fade show">
                    <em class="icon ni ni-cross-circle"></em>
                    {{ error }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
                {% endif %}

                <!-- Then page content -->
                <div class="nk-block-head">...</div>
            </div>
        </div>
    </div>
</div>
```

### Inside Card

```html
<div class="card card-bordered">
    <div class="card-inner">
        {% if form_errors %}
        <div class="alert alert-danger alert-icon mb-4">
            <em class="icon ni ni-cross-circle"></em>
            <strong>Erro!</strong> Por favor, corrija os campos abaixo.
        </div>
        {% endif %}

        <form>
            <!-- form content -->
        </form>
    </div>
</div>
```

## Icon Reference for Alerts

| Type | Icon | Class |
|------|------|-------|
| Success | Check Circle | `ni-check-circle` |
| Error | Cross Circle | `ni-cross-circle` |
| Warning | Alert Circle | `ni-alert-circle` |
| Info | Info | `ni-info` |
| Bell | Bell | `ni-bell` |

## DO NOT

- Don't use alerts without proper contrast (accessibility)
- Don't forget `role="alert"` for accessibility
- Don't stack too many alerts - use toast for transient messages
- Don't use alerts for form validation - use `.invalid-feedback` instead
