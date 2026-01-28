---
name: WX-Convert: Phase
description: Convert a single WinDev element using KB context from MCP tools.
category: Conversion
tags: [wxcode, conversion, element, mcp]
---

# Convert Element: {{element_name}}

## Context

- **Project:** {{project_name}}
- **Element:** {{element_name}}
- **Type:** {{element_type}}
- **Target Files:**
  - Route: `routes/{{element_name_lower}}.py`
  - Template: `templates/{{element_name_lower}}.html`
  - Models: `models/{{element_name_lower}}.py`

## Step 1: Gather Context from Knowledge Base

### Element Definition

Use the MCP tool to retrieve the full element:

```
get_element(element_name="{{element_name}}", project_name="{{project_name}}")
```

**Extract from response:**
- `raw_content`: Original WLanguage source code
- `ast.procedures`: Local procedures with signatures
- `ast.variables`: Declared variables and types
- `ast.events`: UI event handlers
- `dependencies.uses`: Other elements this depends on
- `dependencies.used_by`: Elements that depend on this
- `dependencies.data_files`: Database tables accessed

### UI Structure

Use the MCP tool to retrieve control hierarchy:

```
get_controls(element_name="{{element_name}}", project_name="{{project_name}}")
```

**Extract from response:**
- `controls`: List of UI controls with:
  - `name`: Control identifier (e.g., EDT_LOGIN)
  - `type_name`: Control type (Edit, Button, Table, etc.)
  - `full_path`: Hierarchy path (CELL_Panel.EDT_LOGIN)
  - `events`: Event handlers with code
  - `data_bindings`: Table.field mappings for forms
  - `properties`: Visual configuration (width, height, visible, etc.)

### Business Logic

Use the MCP tool to retrieve procedures:

```
get_procedures(element_name="{{element_name}}", project_name="{{project_name}}")
```

**Extract from response:**
- `procedures`: List of procedures with:
  - `name`: Procedure name
  - `source_element`: Origin element name
  - `is_local`: True if defined in this element
  - `parameters`: List of {name, type, mode}
  - `return_type`: Return type if any
  - `code`: Full WLanguage procedure body

### Data Dependencies

Use MCP tools to get schema information:

```
get_schema(project_name="{{project_name}}")
```

For each table in `dependencies.data_files`:
```
get_table(table_name="TABLE_NAME", project_name="{{project_name}}")
```

**Extract from response:**
- `columns`: List with name, data_type, nullable, default_value
- `primary_key`: Primary key column(s)
- `foreign_keys`: Relationships to other tables
- `indexes`: Database indexes

## Step 2: Generate Pydantic Models

Based on `data_bindings` from controls and `schema` from tables:

**Model Pattern:**
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class {{ModelName}}Base(BaseModel):
    """Base model for {{element_name}} form."""
    # From data_bindings: TABLE.FIELD -> field_name: type
    # Map WLanguage types: string -> str, int -> int, date -> datetime.date

class {{ModelName}}Create({{ModelName}}Base):
    """Model for creating new records."""
    pass

class {{ModelName}}Response({{ModelName}}Base):
    """Model for API responses."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

**Type Mapping Reference:**
| WLanguage | Python |
|-----------|--------|
| chaîne / string | str |
| entier / int | int |
| réel / real | float |
| booléen / boolean | bool |
| date | datetime.date |
| dateheure | datetime.datetime |

## Step 3: Generate FastAPI Route

Based on `element_type`, `events`, and `procedures`:

**Route Pattern:**
```python
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/{{route_prefix}}", tags=["{{element_name}}"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def get_{{function_name}}(request: Request):
    """Render {{element_name}} page."""
    # From OnOpen event or initial load logic
    return templates.TemplateResponse(
        "{{element_name_lower}}.html",
        {"request": request}
    )

@router.post("/", response_class=HTMLResponse)
async def submit_{{function_name}}(request: Request):
    """Handle {{element_name}} form submission."""
    # From BTN_VALIDATE OnClick event or form submit
    form = await request.form()
    # Validation from local procedures
    # Database operations from HAdd/HModify calls
    return templates.TemplateResponse(
        "{{element_name_lower}}.html",
        {"request": request, "success": True}
    )
```

**Event Mapping Reference:**
| WLanguage Event | FastAPI |
|-----------------|---------|
| OnOpen / Ouverture | GET handler |
| OnClick (validate button) | POST handler |
| OnModify | HTMX hx-trigger="change" |
| OnSelect | GET with query params |

## Step 4: Generate Jinja2 Template

Based on `controls` hierarchy:

**Template Pattern:**
```html
{% extends "base.html" %}

{% block title %}{{element_name}}{% endblock %}

{% block content %}
<div class="container">
  <form method="post" hx-post="/{{route_prefix}}/" hx-swap="outerHTML">
    <!-- From controls hierarchy -->
    {% for control in controls %}
      {% if control.type_name == "Edit" %}
      <div class="form-group">
        <label for="{{control.name}}">{{control.caption}}</label>
        <input type="text"
               id="{{control.name}}"
               name="{{control.data_binding}}"
               class="form-control">
      </div>
      {% elif control.type_name == "Button" %}
      <button type="submit" class="btn btn-primary">
        {{control.caption}}
      </button>
      {% endif %}
    {% endfor %}
  </form>
</div>
{% endblock %}
```

**Control Mapping Reference:**
| WLanguage Control | HTML Element |
|-------------------|--------------|
| Champ de saisie (Edit) | `<input>` |
| Bouton (Button) | `<button>` |
| Libellé (Static) | `<span>` or `<label>` |
| Table | `<table>` with HTMX pagination |
| Liste (List) | `<select>` |
| Interrupteur (Check) | `<input type="checkbox">` |
| Sélecteur (Radio) | `<input type="radio">` |

## Step 5: Mark Element Converted

After all files generated and verified:

```
mark_converted(
  element_name="{{element_name}}",
  project_name="{{project_name}}",
  confirm=True,
  notes="Converted: route, template, models generated"
)
```

**First call without confirm** to see preview:
```
mark_converted(element_name="{{element_name}}", project_name="{{project_name}}")
```
- Review current_status and new_status
- Verify this is the correct element

**Then call with confirm=True** to execute:
- Status will change to "converted"
- converted_at timestamp will be set
- Audit log will record the change

## Verification Checklist

- [ ] Pydantic models match data_bindings types
- [ ] FastAPI route responds with 200
- [ ] Template renders without errors
- [ ] Form fields match control names
- [ ] HTMX attributes added for interactivity
- [ ] Event handlers converted to route methods
- [ ] Local procedures converted to helper functions
- [ ] Database operations use async ORM
- [ ] Element marked as converted in KB

## Generated Files

| File | Status | Notes |
|------|--------|-------|
| `routes/{{element_name_lower}}.py` | | |
| `templates/{{element_name_lower}}.html` | | |
| `models/{{element_name_lower}}.py` | | |

## References

- [MCP + GSD Integration Guide](docs/mcp-gsd-integration.md)
- [WLanguage to Python Mapping](CLAUDE.md#mapeamento-wlanguage--python)
- [Control Type Definitions](src/wxcode/models/control_type.py)
