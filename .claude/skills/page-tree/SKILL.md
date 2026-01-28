---
name: page-tree
description: Gera árvore hierárquica de uma página WebDev/WinDev com controles, eventos e procedures locais. Use quando precisar visualizar a estrutura completa de uma página do projeto wxcode.
allowed-tools: mcp__mongodb__find, mcp__mongodb__aggregate, Grep, Read
---

# Page Tree - Árvore de Página WebDev

Gera uma visualização hierárquica completa de uma página WebDev/WinDev, incluindo:
- Controles organizados por hierarquia (pai/filho)
- Eventos com código de cada controle
- Procedures locais da página

## Parâmetros

- **page_name**: Nome da página (case insensitive). Ex: `PAGE_Form_Boleto`, `page_login`

## Instruções

### Passo 1: Encontrar o Elemento da Página

```javascript
// MongoDB: elements collection
db.elements.findOne({
  source_name: { $regex: "PAGE_NAME", $options: "i" }
}, { _id: 1, source_name: 1, controls_count: 1, source_file: 1 })
```

Use o primeiro resultado que tiver `controls_count > 0`.

### Passo 2: Buscar Todos os Controles

```javascript
// MongoDB: controls collection
db.controls.find({
  element_id: ObjectId("ID_DO_ELEMENTO")
}, {
  name: 1, type_code: 1, parent_control_id: 1,
  depth: 1, is_container: 1, children_ids: 1
}).sort({ depth: 1, name: 1 })
```

### Passo 3: Buscar Controles com Eventos (código)

```javascript
// MongoDB: aggregation
db.controls.aggregate([
  { $match: {
      element_id: ObjectId("ID_DO_ELEMENTO"),
      events: { $elemMatch: { code: { $ne: null } } }
  }},
  { $project: {
      name: 1, type_code: 1, depth: 1,
      events: { $filter: {
        input: "$events",
        as: "evt",
        cond: { $ne: ["$$evt.code", null] }
      }}
  }},
  { $sort: { depth: 1, name: 1 }}
])
```

### Passo 4: Extrair Procedures Locais do Arquivo .wwh

Use Grep para encontrar procedures locais no arquivo fonte:

```bash
grep -n "procedure Local_" /path/to/PAGE_NAME.wwh
```

O path do arquivo está em `source_file` do elemento. O diretório base é:
`/Users/gilberto/projetos/wxk/wxcode/project-refs/Linkpay_ADM/`

### Passo 5: Montar a Árvore

Organize a saída no seguinte formato:

```
## **PAGE_NAME** (X controles, Y procedures locais)

### Procedures Locais
├── Local_Procedure1()
├── Local_Procedure2(param): returnType
└── ...

### Árvore de Controles

📄 PAGE_NAME
│
├── ICON CONTROL_NAME (type_code:TypeName)
│   └── ⚡ EventName: código resumido
│
├── 📦 CONTAINER_NAME (Cell/Zone/Popup) ────────┐
│   ├── CONTROL_FILHO                            │
│   │   └── ⚡ OnClick: ação                     │
│   └── ...                                      │
```

## Mapeamento de Ícones por Tipo

| type_code | Ícone | Tipo |
|-----------|-------|------|
| 2 (em TABLE) | 🔲 | Column |
| 2 (fora TABLE) | ✏️ | Edit |
| 3 | 📝 | Static |
| 4 | 🔘 | Button |
| 5, 132 | ☑️ | CheckBox |
| 6 | 🔘 | RadioButton |
| 9 | 📋 | Table |
| 11 | 🔄 | Looper |
| 14 | 📥 | ComboBox |
| 16 | 🔗 | Link |
| 18 | 📑 | Menu |
| 22, 8 | 🖼️ | Image |
| 39 | 📦 | Cell |
| 44 | 📂 | Tab |
| 84 | 🏗️ | LayoutZone |
| 90 | 💬 | Popup |
| 109 | 📄 | RichTextArea |

## Mapeamento de Event Codes

| type_code | Evento |
|-----------|--------|
| 851984 | OnClick (Server) |
| 851998 | OnClick (Browser) |
| 851999 | OnOpen/OnDisplay |
| 852015 | OnChange |
| 851995 | OnRowSelect |
| 851986 | OnInit |

## Exemplo de Saída

```
## **PAGE_FORM_Boleto** (75 controles, 12 procedures locais)

### Procedures Locais
├── Local_GetById()
├── Local_ListarComissoes()
├── Local_Escriturar()
├── Local_Cancelar()
└── Local_ConsultarDocumentNumber(): boolean

### Árvore de Controles

📄 PAGE_FORM_Boleto
│
├── 🖼️ IMG_Cube_24 (Image)
├── 📝 STC_NoName1 (Static)
│
├── 🔘 BTN_PRINT (Button)
│   └── ⚡ OnClick: BrowserOpen(Lower(EDT_LINK))
│
├── 📦 CELL_NoName3 (Cell) ─────────────────────┐
│   ├── 🔘 BTN_VOLTAR1                           │
│   │   └── ⚡ OnClick: PageCloseDialog()        │
│   └── 🔘 BTN_CANCELAR                          │
│       └── ⚡ OnClick: Local_Cancelar()         │
│
├── 📋 TABLE_Comissoes (Table) ─────────────────┐
│   ├── 🔲 COL_CPFComissionado                   │
│   └── 🔲 COL_ValorComissao                     │
│
└── 💬 POPUP_AlterarBoleto (Popup) ─────────────┐
    ├── ⚡ OnOpen: Limpa campos EDT_NOVO_*       │
    └── 🔘 BTN_Confirmar                         │
        └── ⚡ OnClick: Local_Confirmar()        │
```

## Resumo Final

Sempre termine com uma tabela resumo:

| Tipo | Quantidade |
|------|------------|
| Procedures locais | X |
| Controles com eventos | Y |
| Total de controles | Z |
| Depth máximo | N |

## Database Info

- **Database**: wxcode
- **Collections**: elements, controls
- **Project refs path**: /Users/gilberto/projetos/wxk/wxcode/project-refs/Linkpay_ADM/
