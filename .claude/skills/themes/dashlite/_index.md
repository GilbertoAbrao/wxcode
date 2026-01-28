---
name: dashlite-_index
description: Overview do tema DashLite v3.3.0 - SEMPRE carregado
---

# DashLite Theme Overview

DashLite is a Bootstrap 5 admin dashboard theme. This skill provides the foundational knowledge for generating DashLite-compatible HTML.

## Page Structure

```html
<!DOCTYPE html>
<html lang="pt-BR" class="js">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='css/dashlite.css') }}">
</head>
<body class="nk-body bg-lighter npc-default has-sidebar">

    <div class="nk-app-root">
        <div class="nk-main">
            <!-- Sidebar -->
            <div class="nk-sidebar nk-sidebar-fixed is-light" data-content="sidebarMenu">
                {% include "partials/sidebar.html" %}
            </div>

            <!-- Main Content -->
            <div class="nk-wrap">
                <!-- Header -->
                <div class="nk-header nk-header-fixed is-light">
                    {% include "partials/header.html" %}
                </div>

                <!-- Content Area -->
                <div class="nk-content">
                    <div class="container-fluid">
                        <div class="nk-content-inner">
                            <div class="nk-content-body">
                                {% block content %}{% endblock %}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer -->
                <div class="nk-footer">
                    {% include "partials/footer.html" %}
                </div>
            </div>
        </div>
    </div>

    <script src="{{ url_for('static', path='js/bundle.js') }}"></script>
    <script src="{{ url_for('static', path='js/scripts.js') }}"></script>
</body>
</html>
```

## Container Classes

| Class | Usage |
|-------|-------|
| `.nk-app-root` | Root app wrapper |
| `.nk-main` | Main layout container |
| `.nk-wrap` | Content wrapper (excludes sidebar) |
| `.nk-content` | Page content area |
| `.nk-content-inner` | Inner content wrapper |
| `.nk-content-body` | Content body |
| `.container-fluid` | Full-width container |

## Body Classes

| Class | Purpose |
|-------|---------|
| `.nk-body` | Base body class (required) |
| `.bg-lighter` | Light gray background |
| `.bg-white` | White background |
| `.npc-default` | Default page configuration |
| `.has-sidebar` | Indicates sidebar layout |

## UI Style Variants

Add to `<body>` to change overall style:

| Class | Effect |
|-------|--------|
| `.ui-default` | Standard styling |
| `.ui-clean` | White background, card borders |
| `.ui-shady` | Soft shadows |
| `.ui-softy` | Soft backgrounds |
| `.ui-bordered` | Emphasized borders |

## NioIcon System

DashLite uses NioIcon for all icons. Pattern: `ni ni-{icon-name}`

```html
<!-- Icon only -->
<em class="icon ni ni-user"></em>

<!-- Icon with text -->
<span>
    <em class="icon ni ni-plus"></em>
    <span>Add New</span>
</span>
```

### Common Icons Reference

| Icon | Class | Usage |
|------|-------|-------|
| Plus | `ni ni-plus` | Add/Create |
| Edit | `ni ni-edit` | Edit/Modify |
| Trash | `ni ni-trash` | Delete |
| Search | `ni ni-search` | Search |
| Eye | `ni ni-eye` | View |
| Download | `ni ni-download` | Download |
| Upload | `ni ni-upload` | Upload |
| Check | `ni ni-check` | Confirm/Success |
| Cross | `ni ni-cross` | Cancel/Close |
| More | `ni ni-more-h` | More options (horizontal) |
| More | `ni ni-more-v` | More options (vertical) |
| User | `ni ni-user` | User/Profile |
| Users | `ni ni-users` | Users/Team |
| Setting | `ni ni-setting` | Settings |
| Filter | `ni ni-filter` | Filter |
| Sort | `ni ni-sort` | Sort |
| Calendar | `ni ni-calendar` | Date/Calendar |
| Clock | `ni ni-clock` | Time |
| Mail | `ni ni-mail` | Email |
| Bell | `ni ni-bell` | Notifications |
| Menu | `ni ni-menu` | Menu toggle |
| Arrow Left | `ni ni-arrow-left` | Back/Previous |
| Arrow Right | `ni ni-arrow-right` | Next/Forward |
| Chevron Down | `ni ni-chevron-down` | Expand |
| Chevron Up | `ni ni-chevron-up` | Collapse |

### Icon Sizes

```html
<em class="icon ni ni-user"></em>          <!-- Default -->
<em class="icon ni ni-user icon-sm"></em>  <!-- Small -->
<em class="icon ni ni-user icon-lg"></em>  <!-- Large -->
```

## Color Palette

### Background Colors

| Class | Color |
|-------|-------|
| `.bg-primary` | Primary blue (#6576ff) |
| `.bg-secondary` | Secondary gray |
| `.bg-success` | Green (#1ee0ac) |
| `.bg-danger` | Red (#e85347) |
| `.bg-warning` | Orange (#f4bd0e) |
| `.bg-info` | Cyan (#09c2de) |
| `.bg-light` | Light gray |
| `.bg-dark` | Dark gray |
| `.bg-lighter` | Lighter gray |
| `.bg-white` | White |

### Text Colors

| Class | Color |
|-------|-------|
| `.text-primary` | Primary blue |
| `.text-secondary` | Secondary |
| `.text-success` | Green |
| `.text-danger` | Red |
| `.text-warning` | Orange |
| `.text-info` | Cyan |
| `.text-muted` | Muted gray |
| `.text-soft` | Soft gray |

## Page Header Pattern

```html
<div class="nk-block-head nk-block-head-sm">
    <div class="nk-block-between">
        <div class="nk-block-head-content">
            <h3 class="nk-block-title page-title">Page Title</h3>
            <div class="nk-block-des text-soft">
                <p>Page description or subtitle</p>
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
                            <button class="btn btn-primary">
                                <em class="icon ni ni-plus"></em>
                                <span>Add New</span>
                            </button>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
```

## Block System

Content blocks use the `.nk-block` class:

```html
<div class="nk-block">
    <!-- Block content here -->
</div>

<div class="nk-block nk-block-lg">
    <!-- Large block with more spacing -->
</div>
```

## Common Patterns

### Spacing Utilities

Use Bootstrap 5 spacing utilities:
- `mt-{n}`, `mb-{n}`, `my-{n}` - Margin top/bottom
- `ms-{n}`, `me-{n}`, `mx-{n}` - Margin start/end
- `pt-{n}`, `pb-{n}`, `py-{n}` - Padding top/bottom
- `ps-{n}`, `pe-{n}`, `px-{n}` - Padding start/end
- `g-{n}` - Gap (for flexbox/grid)

Where `{n}` is 0, 1, 2, 3, 4, 5, or auto.

### Flex Utilities

```html
<div class="d-flex align-items-center justify-content-between">
    <!-- Flexbox layout -->
</div>
```

## DO NOT

- Don't use standard Bootstrap wrapper classes (use nk-* instead)
- Don't use FontAwesome icons (use NioIcon ni ni-*)
- Don't omit the nk-body class on body element
- Don't use inline styles when DashLite classes exist
