# TODO - Backlog Informal

Ideias e tarefas que ainda não viraram OpenSpec proposals.
Quando algo amadurecer, use `/openspec:proposal` para formalizar.

---

## Próximas Prioridades

- [ ] Fazer a conversao do Project Code
- [ ] Verificar se todas as dependencias da página já foram convertidas e propor lista de conversoes


## Ideias para Explorar

- [ ] Suporte a Django como stack alternativa
- [ ] Exportar para GitHub como projeto template
- [ ] Dashboard web para acompanhar conversões
- [ ] Integração com VS Code (extensão)

## Débitos Técnicos

- [ ] Refatorar element_enricher.py (muito grande)
- [ ] Adicionar mais testes no query_parser
- [ ] Documentar edge cases do WLanguage

## Bugs Conhecidos

- [ ] PDF splitter falha com PDFs protegidos
- [ ] Neo4j sync não trata caracteres especiais em nomes

---

## Como usar este arquivo

1. **Adicionar ideia**: Joga aqui sem cerimônia
2. **Priorizar**: Move para "Próximas Prioridades"  
3. **Formalizar**: Quando for implementar, crie `/openspec:proposal`
4. **Limpar**: Após criar proposal, remove daqui

Este arquivo é informal. A fonte de verdade para trabalho em andamento é `openspec list`.
