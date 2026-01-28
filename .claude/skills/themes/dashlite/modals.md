---
name: dashlite-modals
description: Modals DashLite - dialogs, confirm, sizes
depends-on: [dashlite-_index]
---

# DashLite: Modals

## Basic Modal

```html
<!-- Trigger Button -->
<button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#modalBasic">
    Abrir Modal
</button>

<!-- Modal -->
<div class="modal fade" id="modalBasic" tabindex="-1" aria-labelledby="modalBasicLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="modalBasicLabel">Título do Modal</h5>
                <a href="#" class="close" data-bs-dismiss="modal" aria-label="Close">
                    <em class="icon ni ni-cross"></em>
                </a>
            </div>
            <div class="modal-body">
                <p>Conteúdo do modal aqui.</p>
            </div>
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary">Confirmar</button>
            </div>
        </div>
    </div>
</div>
```

## Modal Sizes

### Small Modal

```html
<div class="modal fade" id="modalSm">
    <div class="modal-dialog modal-sm" role="document">
        <div class="modal-content">
            <!-- content -->
        </div>
    </div>
</div>
```

### Large Modal

```html
<div class="modal fade" id="modalLg">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <!-- content -->
        </div>
    </div>
</div>
```

### Extra Large Modal

```html
<div class="modal fade" id="modalXl">
    <div class="modal-dialog modal-xl" role="document">
        <div class="modal-content">
            <!-- content -->
        </div>
    </div>
</div>
```

### Full Screen Modal

```html
<div class="modal fade" id="modalFull">
    <div class="modal-dialog modal-fullscreen" role="document">
        <div class="modal-content">
            <!-- content -->
        </div>
    </div>
</div>
```

## Confirmation Modal

```html
<!-- Trigger -->
<button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#modalConfirmDelete">
    <em class="icon ni ni-trash"></em>
    <span>Excluir</span>
</button>

<!-- Modal -->
<div class="modal fade" id="modalConfirmDelete" tabindex="-1">
    <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-body modal-body-lg text-center">
                <div class="nk-modal">
                    <em class="nk-modal-icon icon icon-circle icon-circle-xxl ni ni-alert bg-warning"></em>
                    <h4 class="nk-modal-title">Confirmar Exclusão</h4>
                    <div class="nk-modal-text">
                        <p class="lead">Tem certeza que deseja excluir este registro?</p>
                        <p class="text-soft">Esta ação não pode ser desfeita.</p>
                    </div>
                    <div class="nk-modal-action mt-4">
                        <button class="btn btn-lg btn-light" data-bs-dismiss="modal">Cancelar</button>
                        <button class="btn btn-lg btn-danger ms-2" id="btnConfirmDelete">Excluir</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

## Success Modal

```html
<div class="modal fade" id="modalSuccess" tabindex="-1">
    <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-body modal-body-lg text-center">
                <div class="nk-modal">
                    <em class="nk-modal-icon icon icon-circle icon-circle-xxl ni ni-check bg-success"></em>
                    <h4 class="nk-modal-title">Sucesso!</h4>
                    <div class="nk-modal-text">
                        <p class="lead">Registro salvo com sucesso.</p>
                    </div>
                    <div class="nk-modal-action mt-4">
                        <button class="btn btn-lg btn-success" data-bs-dismiss="modal">Ok</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

## Error Modal

```html
<div class="modal fade" id="modalError" tabindex="-1">
    <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-body modal-body-lg text-center">
                <div class="nk-modal">
                    <em class="nk-modal-icon icon icon-circle icon-circle-xxl ni ni-cross bg-danger"></em>
                    <h4 class="nk-modal-title">Erro!</h4>
                    <div class="nk-modal-text">
                        <p class="lead">Ocorreu um erro ao processar sua solicitação.</p>
                        <p class="text-soft">Por favor, tente novamente.</p>
                    </div>
                    <div class="nk-modal-action mt-4">
                        <button class="btn btn-lg btn-danger" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

## Modal with Form

```html
<div class="modal fade" id="modalForm" tabindex="-1">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Novo Cliente</h5>
                <a href="#" class="close" data-bs-dismiss="modal" aria-label="Close">
                    <em class="icon ni ni-cross"></em>
                </a>
            </div>
            <div class="modal-body">
                <form id="formCliente">
                    <div class="row g-4">
                        <div class="col-lg-6">
                            <div class="form-group">
                                <label class="form-label" for="nome">Nome <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="nome" name="nome" required>
                            </div>
                        </div>
                        <div class="col-lg-6">
                            <div class="form-group">
                                <label class="form-label" for="email">Email <span class="text-danger">*</span></label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>
                        </div>
                        <div class="col-lg-6">
                            <div class="form-group">
                                <label class="form-label" for="telefone">Telefone</label>
                                <input type="tel" class="form-control" id="telefone" name="telefone">
                            </div>
                        </div>
                        <div class="col-lg-6">
                            <div class="form-group">
                                <label class="form-label" for="status">Status</label>
                                <select class="form-select" id="status" name="status">
                                    <option value="active">Ativo</option>
                                    <option value="inactive">Inativo</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <em class="icon ni ni-cross"></em>
                    <span>Cancelar</span>
                </button>
                <button type="submit" form="formCliente" class="btn btn-primary">
                    <em class="icon ni ni-check"></em>
                    <span>Salvar</span>
                </button>
            </div>
        </div>
    </div>
</div>
```

## Modal with Tabs

```html
<div class="modal fade" id="modalTabs" tabindex="-1">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Configurações</h5>
                <a href="#" class="close" data-bs-dismiss="modal">
                    <em class="icon ni ni-cross"></em>
                </a>
            </div>
            <ul class="nav nav-tabs nav-tabs-mb-icon nav-tabs-card">
                <li class="nav-item">
                    <a class="nav-link active" data-bs-toggle="tab" href="#tabGeral">
                        <em class="icon ni ni-setting"></em>
                        <span>Geral</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#tabSeguranca">
                        <em class="icon ni ni-lock"></em>
                        <span>Segurança</span>
                    </a>
                </li>
            </ul>
            <div class="modal-body">
                <div class="tab-content">
                    <div class="tab-pane active" id="tabGeral">
                        <p>Configurações gerais...</p>
                    </div>
                    <div class="tab-pane" id="tabSeguranca">
                        <p>Configurações de segurança...</p>
                    </div>
                </div>
            </div>
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                <button type="button" class="btn btn-primary">Salvar</button>
            </div>
        </div>
    </div>
</div>
```

## Vertically Centered

```html
<div class="modal fade" id="modalCentered" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <!-- content -->
        </div>
    </div>
</div>
```

## Scrollable Content

```html
<div class="modal fade" id="modalScrollable" tabindex="-1">
    <div class="modal-dialog modal-dialog-scrollable" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Termos de Uso</h5>
                <a href="#" class="close" data-bs-dismiss="modal">
                    <em class="icon ni ni-cross"></em>
                </a>
            </div>
            <div class="modal-body">
                <!-- Long content that scrolls -->
                <p>Lorem ipsum dolor sit amet...</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" data-bs-dismiss="modal">Aceitar</button>
            </div>
        </div>
    </div>
</div>
```

## Static Backdrop (Cannot Close by Clicking Outside)

```html
<div class="modal fade" id="modalStatic" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <!-- content -->
        </div>
    </div>
</div>
```

## JavaScript Control

```html
<script>
// Show modal
const modal = new bootstrap.Modal(document.getElementById('modalBasic'));
modal.show();

// Hide modal
modal.hide();

// Events
document.getElementById('modalBasic').addEventListener('shown.bs.modal', function () {
    // Modal is now visible
});

document.getElementById('modalBasic').addEventListener('hidden.bs.modal', function () {
    // Modal is now hidden
});
</script>
```

## Modal Body Variants

| Class | Effect |
|-------|--------|
| `.modal-body` | Default padding |
| `.modal-body-lg` | Large padding |
| `.modal-body-sm` | Small padding |
| `.modal-body-md` | Medium padding |

## DO NOT

- Don't forget unique IDs for each modal
- Don't use nested modals
- Don't forget `aria-labelledby` for accessibility
- Don't use inline styles - use DashLite's modal classes
- Don't forget `data-bs-dismiss="modal"` on close buttons
