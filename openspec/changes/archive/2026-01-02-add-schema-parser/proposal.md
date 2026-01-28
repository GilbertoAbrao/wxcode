# Proposal: add-schema-parser

## Summary

Implementar parser para arquivos de Analysis WinDev (.xdd) para extrair o schema do banco de dados (tabelas, colunas, tipos, índices, conexões).

## Motivation

A Analysis (.wda/.wdd/.xdd) é a primeira camada do pipeline de conversão. Contém:
- Definição de todas as tabelas (FICHIER)
- Colunas com tipos HyperFile (RUBRIQUE)
- Conexões de banco de dados
- Índices e chaves primárias/estrangeiras

Sem o schema parseado, não é possível:
- Gerar models Pydantic/SQLAlchemy corretos
- Identificar relacionamentos entre tabelas
- Mapear operações HReadFirst/HAdd para ORM

## Approach

### Fonte de Dados

Usar arquivos **.xdd** (formato XML nativo WinDev) como fonte principal:
- Presente em todos os projetos WinDev (dentro de diretório `*.ana/`)
- Nome do arquivo varia por projeto (ex: `BD.xdd`, `Projeto.xdd`, `Schema.xdd`)
- Contém metadados completos (conexões, tipos exatos, índices)
- Encoding ISO-8859-1

### Descoberta do Arquivo de Analysis

O arquivo .xdd pode ser descoberto de duas formas:

#### 1. Via Project.analysis_path (Preferencial)
O arquivo .wwp/.wdp define o caminho da Analysis:
```
analysis : .\BD.ana\BD.wda
```

O path é relativo ao projeto e aponta para o arquivo `.wda`. O arquivo `.xdd` correspondente está no mesmo diretório com extensão diferente.

**Nota**: Atualmente o `project_mapper.py` não captura corretamente o `analysis_path` porque ele está após a seção `configurations`. Isso será corrigido como parte desta implementação.

#### 2. Via Descoberta Automática (Fallback)
Se `analysis_path` não estiver definido, fazer busca:
1. Procurar diretório `*.ana` no projeto (qualquer nome)
2. Localizar arquivo `*.xdd` dentro dele (qualquer nome)

Exemplos de estruturas suportadas:
- `Projeto/BD.ana/BD.xdd` (via analysis_path `.\BD.ana\BD.wda`)
- `MeuProjeto/MinhaBase.ana/MinhaBase.xdd`
- `App/Analysis.ana/Schema.xdd`

### Estrutura XML do .xdd

```xml
<ANALYSE>
  <CONNEXION Nom="CNX_BASE" Type="1">
    <SOURCE>192.168.10.13</SOURCE>
    <DB>NomeDatabase</DB>
  </CONNEXION>

  <FICHIER Nom="Cliente" Connexion="CNX_BASE">
    <RUBRIQUE Nom="IDcliente">
      <TYPE>24</TYPE>           <!-- Auto-increment -->
      <TYPE_CLE>1</TYPE_CLE>    <!-- Primary Key -->
      <TAILLE>8</TAILLE>
    </RUBRIQUE>
    <RUBRIQUE Nom="Nome">
      <TYPE>2</TYPE>            <!-- VARCHAR -->
      <TAILLE>200</TAILLE>
    </RUBRIQUE>
  </FICHIER>
</ANALYSE>
```

### Mapeamento de Tipos HyperFile → Python

| TYPE | HyperFile | Python | SQLAlchemy |
|------|-----------|--------|------------|
| 2 | Text | str | String |
| 3 | SmallInt | int | SmallInteger |
| 5 | Integer | int | Integer |
| 6 | BigInt | int | BigInteger |
| 11 | Float | float | Float |
| 14 | Date | date | Date |
| 17 | Time | time | Time |
| 24 | Auto-increment | int | Integer (PK, autoincrement) |
| 25 | Numeric (FK) | int | BigInteger |
| 29 | Memo/Text | str | Text |
| 34 | DateTime | datetime | DateTime |
| 37 | Boolean | bool | Boolean |
| 41 | Decimal | Decimal | Numeric |

### TYPE_CLE (Tipo de Chave)

| TYPE_CLE | Significado |
|----------|-------------|
| 0 | Sem índice |
| 1 | Primary Key |
| 2 | Índice (não único) |
| 3 | Índice único |

## Scope

### In Scope
- Parser XML para arquivos .xdd
- Model `DatabaseSchema` com tabelas, colunas, conexões
- CLI command `parse-schema`
- Armazenamento no MongoDB (collection `schemas`)
- Mapeamento de tipos HyperFile → Python

### Out of Scope
- Parsing de arquivos .sql (será fallback futuro se necessário)
- Geração de código SQLAlchemy (fase 4.1)
- Relacionamentos FK automáticos (inferidos pelo padrão ID*)

## Success Criteria

1. Parser descobre automaticamente arquivo .xdd em qualquer projeto
2. Parser extrai 100% das tabelas e colunas do arquivo .xdd
3. Tipos HyperFile mapeados corretamente para Python
4. Índices e PKs identificados
5. CLI command `parse-schema` funcional para qualquer projeto
6. Testes cobrindo parsing e edge cases

## Dependencies

- Nenhuma nova dependência (xml.etree.ElementTree é stdlib)

## Risks

1. **Encoding ISO-8859-1**: Mitigado com conversão explícita
2. **Tipos HyperFile desconhecidos**: Mitigado com mapeamento para `Any`
3. **XML em linha única**: Python xml.etree lida bem com isso
