---
name: dashlite-forms-datepicker
description: Date e datetime pickers DashLite
depends-on: [dashlite-forms-_index]
---

# DashLite: Date & Time Pickers

DashLite uses Flatpickr for date picking. Add class `date-picker` to enable.

## Basic Date Picker

```html
<div class="form-group">
    <label class="form-label">Data</label>
    <div class="form-control-wrap">
        <div class="form-icon form-icon-left">
            <em class="icon ni ni-calendar"></em>
        </div>
        <input type="text" class="form-control date-picker" id="date" name="date" placeholder="dd/mm/aaaa">
    </div>
</div>
```

## Date Formats

### Brazilian Format (dd/mm/yyyy)

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       placeholder="dd/mm/aaaa">
```

### ISO Format (yyyy-mm-dd)

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="Y-m-d"
       placeholder="aaaa-mm-dd">
```

### US Format (mm/dd/yyyy)

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="m/d/Y"
       placeholder="mm/dd/yyyy">
```

## DateTime Picker

```html
<div class="form-group">
    <label class="form-label">Data e Hora</label>
    <div class="form-control-wrap">
        <div class="form-icon form-icon-left">
            <em class="icon ni ni-calendar"></em>
        </div>
        <input type="text"
               class="form-control date-picker"
               data-date-format="d/m/Y H:i"
               data-enable-time="true"
               placeholder="dd/mm/aaaa hh:mm">
    </div>
</div>
```

## Time Only Picker

```html
<div class="form-group">
    <label class="form-label">Horário</label>
    <div class="form-control-wrap">
        <div class="form-icon form-icon-left">
            <em class="icon ni ni-clock"></em>
        </div>
        <input type="text"
               class="form-control time-picker"
               data-date-format="H:i"
               data-enable-time="true"
               data-no-calendar="true"
               placeholder="hh:mm">
    </div>
</div>
```

## Date Range Picker

```html
<div class="form-group">
    <label class="form-label">Período</label>
    <div class="form-control-wrap">
        <div class="form-icon form-icon-left">
            <em class="icon ni ni-calendar"></em>
        </div>
        <input type="text"
               class="form-control date-picker"
               data-mode="range"
               data-date-format="d/m/Y"
               placeholder="Data inicial - Data final">
    </div>
</div>
```

## Multiple Dates

```html
<div class="form-group">
    <label class="form-label">Selecione as datas</label>
    <div class="form-control-wrap">
        <div class="form-icon form-icon-left">
            <em class="icon ni ni-calendar"></em>
        </div>
        <input type="text"
               class="form-control date-picker"
               data-mode="multiple"
               data-date-format="d/m/Y"
               placeholder="Clique para selecionar">
    </div>
</div>
```

## Date with Min/Max

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       data-min-date="today"
       placeholder="Datas a partir de hoje">

<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       data-max-date="today"
       placeholder="Datas até hoje">
```

## Default Value

### Static Default

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       data-default-date="2024-01-15">
```

### Today as Default

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       data-default-date="today">
```

### With Jinja2

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       value="{{ form.birth_date.strftime('%d/%m/%Y') if form.birth_date else '' }}"
       name="birth_date"
       placeholder="dd/mm/aaaa">
```

## Date Range with Separate Inputs

```html
<div class="row g-4">
    <div class="col-md-6">
        <div class="form-group">
            <label class="form-label">Data Início</label>
            <div class="form-control-wrap">
                <div class="form-icon form-icon-left">
                    <em class="icon ni ni-calendar"></em>
                </div>
                <input type="text"
                       class="form-control date-picker"
                       id="startDate"
                       name="start_date"
                       data-date-format="d/m/Y"
                       placeholder="dd/mm/aaaa">
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="form-group">
            <label class="form-label">Data Fim</label>
            <div class="form-control-wrap">
                <div class="form-icon form-icon-left">
                    <em class="icon ni ni-calendar"></em>
                </div>
                <input type="text"
                       class="form-control date-picker"
                       id="endDate"
                       name="end_date"
                       data-date-format="d/m/Y"
                       placeholder="dd/mm/aaaa">
            </div>
        </div>
    </div>
</div>
```

## Disable Specific Days

### Disable Weekends

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       data-disable-weekends="true"
       placeholder="Apenas dias úteis">
```

### Disable Specific Dates

```html
<input type="text"
       class="form-control date-picker"
       data-date-format="d/m/Y"
       data-disable='["2024-12-25", "2024-01-01"]'
       placeholder="Exceto feriados">
```

## Month/Year Only

```html
<div class="form-group">
    <label class="form-label">Competência</label>
    <div class="form-control-wrap">
        <input type="text"
               class="form-control"
               data-date-format="m/Y"
               placeholder="mm/aaaa">
    </div>
</div>
```

## Inline Calendar

```html
<div class="form-group">
    <label class="form-label">Selecione a data</label>
    <div class="date-picker-inline" data-date-format="d/m/Y">
        <input type="hidden" id="inlineDate" name="date">
    </div>
</div>
```

## Data Attributes Reference

| Attribute | Values | Description |
|-----------|--------|-------------|
| `data-date-format` | `d/m/Y`, `Y-m-d`, `d/m/Y H:i` | Date format |
| `data-enable-time` | `true`/`false` | Enable time selection |
| `data-no-calendar` | `true`/`false` | Time only mode |
| `data-mode` | `single`, `multiple`, `range` | Selection mode |
| `data-min-date` | date string or `today` | Minimum date |
| `data-max-date` | date string or `today` | Maximum date |
| `data-default-date` | date string or `today` | Initial value |

## Format Tokens

| Token | Output |
|-------|--------|
| `d` | Day (01-31) |
| `m` | Month (01-12) |
| `Y` | Full year (2024) |
| `y` | 2-digit year (24) |
| `H` | Hours 24h (00-23) |
| `h` | Hours 12h (01-12) |
| `i` | Minutes (00-59) |
| `s` | Seconds (00-59) |
| `K` | AM/PM |

## Complete Example

```html
<div class="row g-4">
    <div class="col-md-4">
        <div class="form-group">
            <label class="form-label">Data Nascimento <span class="text-danger">*</span></label>
            <div class="form-control-wrap">
                <div class="form-icon form-icon-left">
                    <em class="icon ni ni-calendar"></em>
                </div>
                <input type="text"
                       class="form-control date-picker {% if errors.birth_date %}is-invalid{% endif %}"
                       id="birthDate"
                       name="birth_date"
                       data-date-format="d/m/Y"
                       data-max-date="today"
                       value="{{ form.birth_date }}"
                       placeholder="dd/mm/aaaa"
                       required>
                {% if errors.birth_date %}
                <div class="invalid-feedback">{{ errors.birth_date }}</div>
                {% endif %}
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="form-group">
            <label class="form-label">Data Admissão</label>
            <div class="form-control-wrap">
                <div class="form-icon form-icon-left">
                    <em class="icon ni ni-calendar"></em>
                </div>
                <input type="text"
                       class="form-control date-picker"
                       id="hireDate"
                       name="hire_date"
                       data-date-format="d/m/Y"
                       value="{{ form.hire_date }}"
                       placeholder="dd/mm/aaaa">
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="form-group">
            <label class="form-label">Horário Preferencial</label>
            <div class="form-control-wrap">
                <div class="form-icon form-icon-left">
                    <em class="icon ni ni-clock"></em>
                </div>
                <input type="text"
                       class="form-control time-picker"
                       id="preferredTime"
                       name="preferred_time"
                       data-date-format="H:i"
                       data-enable-time="true"
                       data-no-calendar="true"
                       value="{{ form.preferred_time }}"
                       placeholder="hh:mm">
            </div>
        </div>
    </div>
</div>
```

## DO NOT

- Don't use `type="date"` HTML5 native - use `.date-picker` class
- Don't forget to include Flatpickr JS and CSS
- Don't hardcode Brazilian format - use `data-date-format`
- Don't forget the calendar icon for visual consistency
