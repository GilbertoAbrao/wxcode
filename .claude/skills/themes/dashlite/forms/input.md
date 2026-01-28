---
name: dashlite-forms-input
description: Inputs DashLite - text, email, password, number, input groups
depends-on: [dashlite-forms-_index]
---

# DashLite: Text Inputs

## Basic Input

```html
<div class="form-group">
    <label class="form-label" for="name">Nome</label>
    <input type="text" class="form-control" id="name" name="name" placeholder="Digite seu nome">
</div>
```

## Input Types

### Text

```html
<input type="text" class="form-control" id="name" name="name">
```

### Email

```html
<input type="email" class="form-control" id="email" name="email" placeholder="email@exemplo.com">
```

### Password

```html
<div class="form-group">
    <label class="form-label" for="password">Senha</label>
    <div class="form-control-wrap">
        <a href="#" class="form-icon form-icon-right passcode-switch lg" data-target="password">
            <em class="passcode-icon icon-show icon ni ni-eye"></em>
            <em class="passcode-icon icon-hide icon ni ni-eye-off"></em>
        </a>
        <input type="password" class="form-control form-control-lg" id="password" name="password" placeholder="Senha">
    </div>
</div>
```

### Number

```html
<input type="number" class="form-control" id="quantity" name="quantity" min="0" max="100" step="1">
```

### Currency

```html
<div class="form-group">
    <label class="form-label">Valor</label>
    <div class="form-control-wrap">
        <span class="form-icon form-icon-left">R$</span>
        <input type="text" class="form-control ps-5" id="valor" name="valor" placeholder="0,00">
    </div>
</div>
```

### Phone (with mask)

```html
<input type="tel" class="form-control phone-mask" id="phone" name="phone" placeholder="(00) 00000-0000">
```

### CPF/CNPJ

```html
<input type="text" class="form-control cpf-mask" id="cpf" name="cpf" placeholder="000.000.000-00">
<input type="text" class="form-control cnpj-mask" id="cnpj" name="cnpj" placeholder="00.000.000/0000-00">
```

## Input Sizes

```html
<input type="text" class="form-control form-control-sm" placeholder="Small">
<input type="text" class="form-control" placeholder="Default">
<input type="text" class="form-control form-control-lg" placeholder="Large">
<input type="text" class="form-control form-control-xl" placeholder="Extra Large">
```

## Input with Icons

### Icon Left

```html
<div class="form-group">
    <label class="form-label">Email</label>
    <div class="form-control-wrap">
        <span class="form-icon form-icon-left">
            <em class="icon ni ni-mail"></em>
        </span>
        <input type="email" class="form-control" placeholder="Email">
    </div>
</div>
```

### Icon Right

```html
<div class="form-group">
    <label class="form-label">Buscar</label>
    <div class="form-control-wrap">
        <span class="form-icon form-icon-right">
            <em class="icon ni ni-search"></em>
        </span>
        <input type="text" class="form-control" placeholder="Buscar...">
    </div>
</div>
```

### Clickable Icon

```html
<div class="form-control-wrap">
    <a href="#" class="form-icon form-icon-right">
        <em class="icon ni ni-search"></em>
    </a>
    <input type="text" class="form-control" placeholder="Buscar...">
</div>
```

## Input Groups

### Prefix

```html
<div class="form-group">
    <label class="form-label">Website</label>
    <div class="input-group">
        <span class="input-group-text">https://</span>
        <input type="text" class="form-control" placeholder="www.exemplo.com">
    </div>
</div>
```

### Suffix

```html
<div class="form-group">
    <label class="form-label">Email</label>
    <div class="input-group">
        <input type="text" class="form-control" placeholder="usuario">
        <span class="input-group-text">@empresa.com</span>
    </div>
</div>
```

### With Button

```html
<div class="form-group">
    <label class="form-label">Buscar</label>
    <div class="input-group">
        <input type="text" class="form-control" placeholder="Buscar...">
        <button class="btn btn-outline-primary" type="button">
            <em class="icon ni ni-search"></em>
        </button>
    </div>
</div>
```

### Multiple Elements

```html
<div class="input-group">
    <span class="input-group-text">R$</span>
    <input type="text" class="form-control" placeholder="0">
    <span class="input-group-text">,</span>
    <input type="text" class="form-control" placeholder="00" style="max-width: 60px;">
</div>
```

## Input States

### Disabled

```html
<input type="text" class="form-control" value="Valor não editável" disabled>
```

### Readonly

```html
<input type="text" class="form-control" value="Valor somente leitura" readonly>
```

### Readonly Plain Text

```html
<input type="text" class="form-control-plaintext" value="Valor como texto" readonly>
```

### Focused

```html
<input type="text" class="form-control focus" placeholder="Com foco visual">
```

## Search Input Pattern

```html
<div class="form-group">
    <div class="form-control-wrap">
        <div class="form-icon form-icon-right">
            <em class="icon ni ni-search"></em>
        </div>
        <input type="text" class="form-control" id="search" placeholder="Buscar...">
    </div>
</div>
```

## Filter Input (in toolbar)

```html
<div class="card-tools me-n1">
    <ul class="btn-toolbar gx-1">
        <li>
            <div class="form-control-wrap">
                <div class="form-icon form-icon-left">
                    <em class="icon ni ni-search"></em>
                </div>
                <input type="text" class="form-control" id="searchFilter" placeholder="Buscar">
            </div>
        </li>
    </ul>
</div>
```

## Complete Example

```html
<form>
    <div class="row g-4">
        <div class="col-lg-6">
            <div class="form-group">
                <label class="form-label" for="firstName">Nome <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="firstName" name="firstName" required>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="form-group">
                <label class="form-label" for="lastName">Sobrenome</label>
                <input type="text" class="form-control" id="lastName" name="lastName">
            </div>
        </div>
        <div class="col-lg-6">
            <div class="form-group">
                <label class="form-label" for="email">Email <span class="text-danger">*</span></label>
                <div class="form-control-wrap">
                    <span class="form-icon form-icon-left">
                        <em class="icon ni ni-mail"></em>
                    </span>
                    <input type="email" class="form-control" id="email" name="email" required>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="form-group">
                <label class="form-label" for="phone">Telefone</label>
                <div class="form-control-wrap">
                    <span class="form-icon form-icon-left">
                        <em class="icon ni ni-call"></em>
                    </span>
                    <input type="tel" class="form-control phone-mask" id="phone" name="phone">
                </div>
            </div>
        </div>
    </div>
</form>
```

## DO NOT

- Don't use `type="text"` for emails (use `type="email"`)
- Don't use inline `style` for icon positioning - use `.form-icon` classes
- Don't forget the `.form-control-wrap` when using icons
