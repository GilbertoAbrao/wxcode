---
name: dashlite-layout
description: Grid system, containers, spacing DashLite
depends-on: [dashlite-_index]
---

# DashLite: Layout & Grid

## Grid System

DashLite uses Bootstrap 5 grid with some custom additions.

### Basic Grid

```html
<div class="row">
    <div class="col-md-6">Column 1</div>
    <div class="col-md-6">Column 2</div>
</div>
```

### With Gutters

```html
<!-- Standard gutter -->
<div class="row g-4">
    <div class="col-md-6">Column 1</div>
    <div class="col-md-6">Column 2</div>
</div>

<!-- DashLite special gutter -->
<div class="row g-gs">
    <div class="col-md-6">Column 1</div>
    <div class="col-md-6">Column 2</div>
</div>
```

### Gutter Sizes

| Class | Size |
|-------|------|
| `g-0` | No gutter |
| `g-1` | 0.25rem |
| `g-2` | 0.5rem |
| `g-3` | 1rem |
| `g-4` | 1.5rem |
| `g-5` | 3rem |
| `g-gs` | DashLite standard (usually 28px) |

## Breakpoints

| Breakpoint | Class infix | Dimensions |
|------------|-------------|------------|
| X-Small | (none) | <576px |
| Small | `sm` | ≥576px |
| Medium | `md` | ≥768px |
| Large | `lg` | ≥992px |
| Extra large | `xl` | ≥1200px |
| XXL | `xxl` | ≥1400px |

## Column Sizes

```html
<div class="row g-4">
    <div class="col-12">Full width</div>
    <div class="col-6">Half width</div>
    <div class="col-4">Third width</div>
    <div class="col-3">Quarter width</div>
</div>

<!-- Responsive -->
<div class="row g-4">
    <div class="col-12 col-md-6 col-lg-4">
        Full on mobile, half on tablet, third on desktop
    </div>
</div>
```

## Common Layouts

### Two Column Form

```html
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
</div>
```

### Three Column Cards

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

### Sidebar + Content

```html
<div class="row g-gs">
    <div class="col-lg-4 col-xl-3">
        <!-- Sidebar content -->
        <div class="card card-bordered">
            <div class="card-inner">Sidebar</div>
        </div>
    </div>
    <div class="col-lg-8 col-xl-9">
        <!-- Main content -->
        <div class="card card-bordered">
            <div class="card-inner">Main Content</div>
        </div>
    </div>
</div>
```

## Containers

```html
<!-- Full width -->
<div class="container-fluid">...</div>

<!-- Fixed max-width -->
<div class="container">...</div>

<!-- Responsive containers -->
<div class="container-sm">...</div>
<div class="container-md">...</div>
<div class="container-lg">...</div>
<div class="container-xl">...</div>
```

## NioBlocks

DashLite's content block system:

```html
<!-- Block with default spacing -->
<div class="nk-block">
    <div class="card card-bordered">...</div>
</div>

<!-- Block with more spacing -->
<div class="nk-block nk-block-lg">
    <div class="card card-bordered">...</div>
</div>

<!-- Block head -->
<div class="nk-block-head nk-block-head-sm">
    <div class="nk-block-between">
        <div class="nk-block-head-content">
            <h3 class="nk-block-title page-title">Page Title</h3>
        </div>
    </div>
</div>
```

## Spacing Utilities

### Margin

| Class | Property |
|-------|----------|
| `mt-{n}` | margin-top |
| `mb-{n}` | margin-bottom |
| `ms-{n}` | margin-start (left) |
| `me-{n}` | margin-end (right) |
| `mx-{n}` | margin horizontal |
| `my-{n}` | margin vertical |
| `m-{n}` | margin all |

### Padding

| Class | Property |
|-------|----------|
| `pt-{n}` | padding-top |
| `pb-{n}` | padding-bottom |
| `ps-{n}` | padding-start (left) |
| `pe-{n}` | padding-end (right) |
| `px-{n}` | padding horizontal |
| `py-{n}` | padding vertical |
| `p-{n}` | padding all |

### Values

| Value | Size |
|-------|------|
| `0` | 0 |
| `1` | 0.25rem |
| `2` | 0.5rem |
| `3` | 1rem |
| `4` | 1.5rem |
| `5` | 3rem |
| `auto` | auto |

```html
<div class="mt-4 mb-3">Margin top 4, margin bottom 3</div>
<div class="px-3 py-2">Padding x 3, padding y 2</div>
```

## Flexbox Utilities

### Display

```html
<div class="d-flex">Flexbox</div>
<div class="d-inline-flex">Inline Flexbox</div>
<div class="d-none d-md-flex">Hidden on mobile, flex on md+</div>
```

### Direction

```html
<div class="d-flex flex-row">Row direction</div>
<div class="d-flex flex-column">Column direction</div>
```

### Justify Content

```html
<div class="d-flex justify-content-start">Start</div>
<div class="d-flex justify-content-center">Center</div>
<div class="d-flex justify-content-end">End</div>
<div class="d-flex justify-content-between">Space Between</div>
<div class="d-flex justify-content-around">Space Around</div>
```

### Align Items

```html
<div class="d-flex align-items-start">Align Start</div>
<div class="d-flex align-items-center">Align Center</div>
<div class="d-flex align-items-end">Align End</div>
```

### Gap

```html
<div class="d-flex gap-2">Gap 2 (0.5rem)</div>
<div class="d-flex gap-3">Gap 3 (1rem)</div>
<div class="d-flex gap-4">Gap 4 (1.5rem)</div>
```

## Common Layout Patterns

### Page with Header and Actions

```html
<div class="nk-content">
    <div class="container-fluid">
        <div class="nk-content-inner">
            <div class="nk-content-body">
                <!-- Page Header -->
                <div class="nk-block-head nk-block-head-sm">
                    <div class="nk-block-between">
                        <div class="nk-block-head-content">
                            <h3 class="nk-block-title page-title">Clientes</h3>
                            <div class="nk-block-des text-soft">
                                <p>Gerencie seus clientes.</p>
                            </div>
                        </div>
                        <div class="nk-block-head-content">
                            <div class="toggle-wrap nk-block-tools-toggle">
                                <a href="#" class="btn btn-icon btn-trigger toggle-expand me-n1" data-target="pageMenu">
                                    <em class="icon ni ni-menu-alt-r"></em>
                                </a>
                                <div class="toggle-expand-content" data-content="pageMenu">
                                    <ul class="nk-block-tools g-3">
                                        <li>
                                            <a href="#" class="btn btn-white btn-outline-light">
                                                <em class="icon ni ni-download-cloud"></em>
                                                <span>Exportar</span>
                                            </a>
                                        </li>
                                        <li class="nk-block-tools-opt">
                                            <a href="/clientes/novo" class="btn btn-primary">
                                                <em class="icon ni ni-plus"></em>
                                                <span>Novo Cliente</span>
                                            </a>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Content Block -->
                <div class="nk-block">
                    <div class="card card-bordered card-preview">
                        <div class="card-inner">
                            <!-- Main content here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Form Page Layout

```html
<div class="nk-content">
    <div class="container-fluid">
        <div class="nk-content-inner">
            <div class="nk-content-body">
                <div class="nk-block-head nk-block-head-sm">
                    <div class="nk-block-between g-3">
                        <div class="nk-block-head-content">
                            <h3 class="nk-block-title page-title">Novo Cliente</h3>
                            <div class="nk-block-des text-soft">
                                <p>Preencha os dados do cliente.</p>
                            </div>
                        </div>
                        <div class="nk-block-head-content">
                            <a href="/clientes" class="btn btn-outline-light bg-white d-none d-sm-inline-flex">
                                <em class="icon ni ni-arrow-left"></em>
                                <span>Voltar</span>
                            </a>
                        </div>
                    </div>
                </div>
                <div class="nk-block">
                    <div class="card card-bordered">
                        <div class="card-inner">
                            <form>
                                <div class="row g-4">
                                    <!-- Form fields -->
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

## Dividers

```html
<!-- Simple divider -->
<div class="nk-divider divider md"></div>

<!-- Divider with text -->
<div class="nk-divider divider md">
    <span>OU</span>
</div>
```

## DO NOT

- Don't use inline styles for layout - use utility classes
- Don't mix different grid systems
- Don't forget `.g-*` classes for gutters
- Don't use negative margins when utility classes exist
