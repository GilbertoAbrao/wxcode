---
name: dashlite-cards
description: Cards DashLite - preview, bordered, header/footer
depends-on: [dashlite-_index]
---

# DashLite: Cards

## Basic Card

```html
<div class="card">
    <div class="card-inner">
        <p>Card content here</p>
    </div>
</div>
```

## Card Variants

### Bordered Card

```html
<div class="card card-bordered">
    <div class="card-inner">
        <p>Card with border</p>
    </div>
</div>
```

### Preview Card (Recommended for forms/tables)

```html
<div class="card card-bordered card-preview">
    <div class="card-inner">
        <p>Card for previews and forms</p>
    </div>
</div>
```

### Full Card

```html
<div class="card card-bordered card-full">
    <div class="card-inner">
        <p>Full height card</p>
    </div>
</div>
```

## Card with Header

### Basic Header

```html
<div class="card card-bordered">
    <div class="card-inner card-inner-lg">
        <div class="card-head">
            <h5 class="card-title">Card Title</h5>
        </div>
        <p>Card content</p>
    </div>
</div>
```

### Header with Subtitle

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="card-head">
            <h5 class="card-title">Card Title</h5>
            <p class="card-title-sub text-soft">Subtitle text</p>
        </div>
        <p>Card content</p>
    </div>
</div>
```

### Header with Actions

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="card-title-group">
            <div class="card-title">
                <h6 class="title">Usuários</h6>
            </div>
            <div class="card-tools">
                <a href="#" class="btn btn-primary btn-sm">
                    <em class="icon ni ni-plus"></em>
                    <span>Adicionar</span>
                </a>
            </div>
        </div>
        <!-- Card content -->
    </div>
</div>
```

### Header with Dropdown

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="card-title-group">
            <div class="card-title">
                <h6 class="title">Relatório</h6>
            </div>
            <div class="card-tools">
                <div class="drodown">
                    <a href="#" class="dropdown-toggle btn btn-icon btn-trigger" data-bs-toggle="dropdown">
                        <em class="icon ni ni-more-h"></em>
                    </a>
                    <div class="dropdown-menu dropdown-menu-end">
                        <ul class="link-list-opt no-bdr">
                            <li><a href="#"><span>Exportar</span></a></li>
                            <li><a href="#"><span>Imprimir</span></a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        <!-- Card content -->
    </div>
</div>
```

## Card Inner Groups

For cards with multiple sections:

```html
<div class="card card-bordered">
    <div class="card-inner-group">
        <div class="card-inner">
            <div class="card-title-group">
                <div class="card-title">
                    <h6 class="title">Seção 1</h6>
                </div>
            </div>
        </div>
        <div class="card-inner card-inner-md">
            <p>Content of section 1</p>
        </div>
        <div class="card-inner">
            <p>Content of section 2</p>
        </div>
    </div>
</div>
```

## Card Inner Padding

| Class | Padding |
|-------|---------|
| `.card-inner` | Default (1.5rem) |
| `.card-inner-sm` | Small |
| `.card-inner-md` | Medium |
| `.card-inner-lg` | Large |
| `.card-inner-xl` | Extra Large |

```html
<div class="card-inner card-inner-sm">Small padding</div>
<div class="card-inner card-inner-lg">Large padding</div>
```

## Card with Tabs

```html
<div class="card card-bordered">
    <ul class="nav nav-tabs nav-tabs-mb-icon nav-tabs-card">
        <li class="nav-item">
            <a class="nav-link active" data-bs-toggle="tab" href="#tabItem1">
                <em class="icon ni ni-user"></em>
                <span>Dados</span>
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#tabItem2">
                <em class="icon ni ni-lock"></em>
                <span>Segurança</span>
            </a>
        </li>
    </ul>
    <div class="card-inner">
        <div class="tab-content">
            <div class="tab-pane active" id="tabItem1">
                <p>Tab 1 content</p>
            </div>
            <div class="tab-pane" id="tabItem2">
                <p>Tab 2 content</p>
            </div>
        </div>
    </div>
</div>
```

## Stat Cards

### Basic Stat

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="card-title-group align-start mb-2">
            <div class="card-title">
                <h6 class="title">Total Vendas</h6>
            </div>
            <div class="card-tools">
                <em class="card-hint icon ni ni-help" title="Total de vendas do mês"></em>
            </div>
        </div>
        <div class="align-end flex-sm-wrap g-4 flex-md-nowrap">
            <div class="nk-sale-data">
                <span class="amount">R$ 45.890,00</span>
                <span class="sub-title">
                    <span class="change up text-success">
                        <em class="icon ni ni-arrow-long-up"></em>4.63%
                    </span>
                    vs. mês anterior
                </span>
            </div>
        </div>
    </div>
</div>
```

### Stat with Icon

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="card-title-group">
            <div class="card-title">
                <h6 class="title">Novos Clientes</h6>
            </div>
            <div class="card-tools">
                <div class="icon-circle icon-circle-lg bg-primary-dim">
                    <em class="icon ni ni-users text-primary"></em>
                </div>
            </div>
        </div>
        <div class="mt-4">
            <span class="amount">1.250</span>
            <span class="change up text-success">
                <em class="icon ni ni-arrow-long-up"></em>12.5%
            </span>
        </div>
    </div>
</div>
```

## Info Cards

```html
<div class="card card-bordered">
    <div class="card-inner">
        <div class="align-center justify-between">
            <div class="g">
                <h6 class="overline-title-alt text-soft">Pendentes</h6>
                <p class="lead-text">15 itens</p>
            </div>
            <div class="g">
                <a href="#" class="btn btn-dim btn-primary">
                    <span>Ver todos</span>
                    <em class="icon ni ni-chevron-right"></em>
                </a>
            </div>
        </div>
    </div>
</div>
```

## Card for Form

```html
<div class="card card-bordered card-preview">
    <div class="card-inner">
        <div class="preview-block">
            <span class="preview-title-lg overline-title">Dados do Usuário</span>
            <form>
                <div class="row g-4">
                    <div class="col-lg-6">
                        <div class="form-group">
                            <label class="form-label">Nome</label>
                            <input type="text" class="form-control">
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control">
                        </div>
                    </div>
                    <div class="col-12">
                        <button class="btn btn-primary">Salvar</button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>
```

## Colored Cards

```html
<div class="card bg-primary">
    <div class="card-inner">
        <h5 class="card-title text-white">Primary Card</h5>
        <p class="text-white">White text on primary background</p>
    </div>
</div>

<div class="card bg-success-dim">
    <div class="card-inner">
        <h5 class="card-title">Success Dim Card</h5>
        <p>Soft green background</p>
    </div>
</div>
```

## Card Grid

```html
<div class="row g-gs">
    <div class="col-md-6 col-lg-4">
        <div class="card card-bordered">
            <div class="card-inner">Card 1</div>
        </div>
    </div>
    <div class="col-md-6 col-lg-4">
        <div class="card card-bordered">
            <div class="card-inner">Card 2</div>
        </div>
    </div>
    <div class="col-md-6 col-lg-4">
        <div class="card card-bordered">
            <div class="card-inner">Card 3</div>
        </div>
    </div>
</div>
```

## Complete Form Card Example

```html
<div class="nk-block">
    <div class="card card-bordered">
        <div class="card-inner-group">
            <div class="card-inner card-inner-lg">
                <div class="nk-block-head">
                    <div class="nk-block-head-content">
                        <h4 class="nk-block-title">Cadastro de Cliente</h4>
                        <div class="nk-block-des">
                            <p>Preencha os dados do cliente.</p>
                        </div>
                    </div>
                </div>
                <div class="nk-block">
                    <form>
                        <div class="row g-4">
                            <div class="col-lg-6">
                                <div class="form-group">
                                    <label class="form-label" for="name">Nome <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" id="name" name="name" required>
                                </div>
                            </div>
                            <div class="col-lg-6">
                                <div class="form-group">
                                    <label class="form-label" for="email">Email <span class="text-danger">*</span></label>
                                    <input type="email" class="form-control" id="email" name="email" required>
                                </div>
                            </div>
                            <div class="col-12">
                                <div class="form-group">
                                    <button type="submit" class="btn btn-lg btn-primary">
                                        <em class="icon ni ni-check"></em>
                                        <span>Salvar</span>
                                    </button>
                                    <a href="#" class="btn btn-lg btn-outline-secondary ms-2">
                                        <span>Cancelar</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
```

## DO NOT

- Don't use `.card` without `.card-inner` for content
- Don't forget `.card-bordered` for visible borders
- Don't nest cards unnecessarily
- Don't use inline styles for spacing - use `.card-inner-*` classes
