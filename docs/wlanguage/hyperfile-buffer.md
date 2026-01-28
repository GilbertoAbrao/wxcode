# HyperFile Buffer Global

Documentação do modelo de buffer global do HyperFile para conversão WLanguage → Python.

## Conceito de Buffer Global

Em WinDev/WebDev, o HyperFile mantém um **buffer global por tabela** que armazena o registro atual de cada tabela do banco de dados.

```
+------------------------------------------------------------------+
|                      MEMÓRIA DO APLICATIVO                       |
+------------------------------------------------------------------+
|                                                                  |
|  +------------------+    +------------------+    +-------------+ |
|  | BUFFER: CLIENTE  |    | BUFFER: PEDIDO   |    | BUFFER: ... | |
|  +------------------+    +------------------+    +-------------+ |
|  | _id: 123         |    | _id: 456         |    |             | |
|  | nome: "João"     |    | data: 2024-01-15 |    |             | |
|  | cpf: "123..."    |    | cliente_id: 123  |    |             | |
|  | email: "..."     |    | status: "aberto" |    |             | |
|  +------------------+    +------------------+    +-------------+ |
|         ↑                        ↑                               |
|         |                        |                               |
|   HReadSeekFirst           HReadFirst                            |
|   HReadNext                HModify                               |
|   HReset + atribuições     HAdd                                  |
|                                                                  |
+------------------------------------------------------------------+
```

### Características do Buffer Global

1. **Um buffer por tabela**: Cada tabela tem exatamente um buffer em memória
2. **Modificado por funções H***: Funções como `HReadSeekFirst`, `HReadNext` carregam dados no buffer
3. **Acessado via sintaxe `TABELA.campo`**: `CLIENTE.nome` lê do buffer, não faz query
4. **Persistido por funções H***: `HAdd`, `HModify`, `HDelete` salvam/modificam o registro do buffer

### Problema para Python/Web

Python e aplicações web são **stateless** - não há buffer global persistente entre requests. Cada request HTTP é independente.

```
WLanguage (Stateful)              Python/FastAPI (Stateless)
--------------------              -------------------------
HReadSeekFirst(CLIENTE, CPF)     cliente = await db.find_one({"cpf": cpf})
IF HFound() THEN                  if cliente:
    Trace(CLIENTE.nome)              print(cliente["nome"])
END
```

## Padrões de Conversão

### 1. Loop HReadFirst/HReadNext → `async for` com Cursor

**WLanguage:**
```wlanguage
HReadFirst(PEDIDO, DATA_PEDIDO)
WHILE NOT HOut()
    Trace(PEDIDO.numero, PEDIDO.valor)
    HReadNext(PEDIDO, DATA_PEDIDO)
END
```

**Python (MongoDB):**
```python
async for pedido in db.pedidos.find().sort("data_pedido", 1):
    print(pedido["numero"], pedido["valor"])
```

**Python (SQLAlchemy):**
```python
async with session.begin():
    result = await session.execute(
        select(Pedido).order_by(Pedido.data_pedido)
    )
    for pedido in result.scalars():
        print(pedido.numero, pedido.valor)
```

### 2. HReset + Atribuições + HAdd → `insert_one(dict)`

**WLanguage:**
```wlanguage
HReset(CLIENTE)
CLIENTE.nome = EDT_Nome
CLIENTE.cpf = EDT_CPF
CLIENTE.email = EDT_Email
HAdd(CLIENTE)
```

**Python (MongoDB):**
```python
cliente = {
    "nome": form.nome,
    "cpf": form.cpf,
    "email": form.email,
}
await db.clientes.insert_one(cliente)
```

**Python (SQLAlchemy):**
```python
cliente = Cliente(
    nome=form.nome,
    cpf=form.cpf,
    email=form.email,
)
session.add(cliente)
await session.commit()
```

### 3. FileToScreen → Template Context

**WLanguage:**
```wlanguage
// Carrega registro
HReadSeekFirst(CLIENTE, CPF, gsCodigoBusca)
IF HFound() THEN
    // Copia buffer para controles da tela
    FileToScreen()
END
```

**Python (FastAPI + Jinja2):**
```python
@router.get("/cliente/{cpf}")
async def get_cliente(cpf: str):
    cliente = await db.clientes.find_one({"cpf": cpf})
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")

    # Passa dados para o template como contexto
    return templates.TemplateResponse(
        "cliente/form.html",
        {"request": request, "cliente": cliente}
    )
```

**Template Jinja2:**
```html
<input name="nome" value="{{ cliente.nome }}">
<input name="cpf" value="{{ cliente.cpf }}">
<input name="email" value="{{ cliente.email }}">
```

### 4. ScreenToFile + HModify → Form Data + Update

**WLanguage:**
```wlanguage
// Copia controles para buffer
ScreenToFile()
// Salva no banco
HModify(CLIENTE)
```

**Python (FastAPI):**
```python
@router.post("/cliente/{cpf}")
async def update_cliente(cpf: str, form: ClienteForm):
    # Form data já está validado pelo Pydantic
    result = await db.clientes.update_one(
        {"cpf": cpf},
        {"$set": form.model_dump()}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Cliente não encontrado")

    return RedirectResponse("/cliente/" + cpf, status_code=303)
```

## Conflito de Buffer

### Problema

Quando dois loops usam a mesma tabela, eles competem pelo mesmo buffer:

```wlanguage
// PROBLEMA: Loop externo e interno usam o mesmo buffer de CLIENTE
HReadFirst(CLIENTE, NOME)
WHILE NOT HOut()
    // Ao ler o pedido, o buffer de CLIENTE é perdido!
    HReadSeekFirst(PEDIDO, CLIENTE_ID, CLIENTE.id)
    WHILE NOT HOut(PEDIDO)
        // CLIENTE.nome aqui pode estar ERRADO!
        Trace(CLIENTE.nome, PEDIDO.numero)
        HReadNext(PEDIDO, CLIENTE_ID)
    END
    HReadNext(CLIENTE, NOME)  // Vai para registro incorreto!
END
```

### Solução WLanguage: HAlias

```wlanguage
// Cria alias para ter dois buffers independentes
AliasCliente is Data Source = HAlias(CLIENTE)

HReadFirst(CLIENTE, NOME)
WHILE NOT HOut()
    // Usa o alias - buffer separado
    HReadSeekFirst(PEDIDO, CLIENTE_ID, CLIENTE.id)
    WHILE NOT HOut(PEDIDO)
        Trace(CLIENTE.nome, PEDIDO.numero)  // CLIENTE original preservado
        HReadNext(PEDIDO, CLIENTE_ID)
    END
    HReadNext(CLIENTE, NOME)  // Continua corretamente
END
```

### Solução Python: Variáveis Locais (Natural)

```python
# Python não tem esse problema - cada query retorna dados independentes
async for cliente in db.clientes.find().sort("nome", 1):
    # cliente é uma variável local, não afetada por outras queries
    async for pedido in db.pedidos.find({"cliente_id": cliente["_id"]}):
        print(cliente["nome"], pedido["numero"])
```

## Resumo de Conversão

| WLanguage | Python | Notas |
|-----------|--------|-------|
| `TABELA.campo` (leitura) | `doc["campo"]` ou `obj.campo` | Ler do dict/objeto local |
| `TABELA.campo = valor` | `doc["campo"] = valor` | Modificar dict local |
| `HReset(TABELA)` | `doc = {}` | Criar dict vazio |
| `HReadSeekFirst(T, K, v)` | `await db.find_one({k: v})` | Query direta |
| `HReadFirst/Next loop` | `async for doc in cursor` | Iteração de cursor |
| `HFound()` | `doc is not None` | Verificar resultado |
| `HOut()` | Fim do `for` loop | Iterador esgotado |
| `HAdd(TABELA)` | `await db.insert_one(doc)` | Inserir documento |
| `HModify(TABELA)` | `await db.update_one(...)` | Atualizar documento |
| `HDelete(TABELA)` | `await db.delete_one(...)` | Deletar documento |
| `FileToScreen()` | Template context | Passar dict para template |
| `ScreenToFile()` | Form validation | Pydantic form → dict |
| `HAlias(TABELA)` | Não necessário | Python usa variáveis locais |

## Implicações para o Transpiler

1. **Funções que modificam buffer** precisam ser convertidas para queries explícitas
2. **Acesso a `TABELA.campo`** precisa ser convertido para acesso a variável local
3. **Loops H*** precisam ser convertidos para iteradores
4. **HAlias** pode ser ignorado - Python já é naturalmente seguro

## Referências

- [HAlias - PC SOFT Doc](https://doc.windev.com/en-US/?3044176)
- [FileToScreen - PC SOFT Doc](https://doc.windev.com/en-US/?3044210)
- [Using HAlias for Multiple Buffers - WX Blog](https://blog.wxperts.com/2018/10/28/using-halias-to-have-2-active-record-buffers-for-the-same-file/)
