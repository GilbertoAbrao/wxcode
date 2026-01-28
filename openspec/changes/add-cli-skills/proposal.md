# Proposal: add-cli-skills

## Summary

Criar skills para expor todos os 29 comandos do wxcode CLI, permitindo que outros agentes Claude (Claude Code, Claude Desktop) possam utilizar as funcionalidades do wxcode de forma estruturada e guiada.

## Motivation

Atualmente o wxcode CLI pode ser utilizado diretamente via Bash, mas isso requer que o agente conheça a sintaxe exata de cada comando. Skills fornecem:

1. **Documentação inline**: O agente recebe instruções claras sobre o que o comando faz
2. **Validação de parâmetros**: Instruções sobre parâmetros obrigatórios e opcionais
3. **Fluxo guiado**: Passos claros para execução correta
4. **Sugestões de próximos passos**: O que fazer após cada comando
5. **Tratamento de erros**: Como lidar com problemas comuns

## Scope

### In Scope
- 29 skills cobrindo todos os comandos do CLI
- Organização em categorias lógicas (import, parse, analyze, convert, neo4j, manage)
- Instruções claras para cada skill
- Mapeamento de parâmetros e opções

### Out of Scope
- MCP Server (pode ser adicionado futuramente)
- Novas funcionalidades no CLI
- Alterações no código Python

## Commands to Cover

### Category: Import & Setup (3 skills)
1. `wx:import` - Importa projeto WinDev/WebDev
2. `wx:init-project` - Inicializa projeto FastAPI gerado
3. `wx:purge` - Remove projeto do MongoDB

### Category: Parsing (6 skills)
4. `wx:split-pdf` - Divide PDF de documentação
5. `wx:enrich` - Enriquece elementos com controles/eventos
6. `wx:parse-procedures` - Parseia procedures globais (.wdg)
7. `wx:parse-classes` - Parseia classes (.wdc)
8. `wx:parse-schema` - Parseia schema do banco (.wdd)
9. `wx:list-orphans` - Lista controles órfãos

### Category: Analysis (5 skills)
10. `wx:analyze` - Analisa dependências do projeto
11. `wx:plan` - Planeja ordem de conversão
12. `wx:sync-neo4j` - Sincroniza grafo com Neo4j
13. `wx:impact` - Análise de impacto de mudanças
14. `wx:path` - Encontra caminhos entre elementos

### Category: Neo4j (3 skills)
15. `wx:hubs` - Encontra nós críticos
16. `wx:dead-code` - Detecta código não utilizado

### Category: Conversion (5 skills)
17. `wx:convert` - Converte elementos
18. `wx:convert-page` - Converte página específica (LLM)
19. `wx:validate` - Valida conversão
20. `wx:export` - Exporta projeto convertido
21. `wx:conversion-skip` - Marca elemento para skip

### Category: Themes (2 skills)
22. `wx:themes` - Gerencia temas
23. `wx:deploy-theme` - Deploy de tema

### Category: Status & Info (5 skills)
24. `wx:list-projects` - Lista projetos
25. `wx:list-elements` - Lista elementos do projeto
26. `wx:status` - Status do projeto
27. `wx:check-duplicates` - Verifica duplicatas
28. `wx:test-app` - Testa aplicação gerada

### Category: OpenSpec Integration (1 skill)
29. `wx:spec-proposal` - Gera proposta de especificação

## Success Criteria

- [ ] 29 skills criadas em `.claude/skills/wxcode/`
- [ ] Cada skill segue o formato padrão (frontmatter + instruções)
- [ ] Skills agrupadas por categoria em subdiretórios
- [ ] Documentação de uso em README.md
- [ ] Todas as skills testáveis via `/wx:<command>`

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Skills muito verbosas | Contexto excessivo | Manter instruções concisas |
| Parâmetros desatualizados | Execução falha | Referência ao `--help` do CLI |
| Duplicação com page-tree | Confusão | Prefixo `wx:` diferencia |

## Dependencies

- Nenhuma alteração de código necessária
- CLI já funcional e documentado
- Estrutura de skills já existe no projeto

## Estimated Complexity

**Baixa** - Apenas criação de arquivos Markdown seguindo padrão existente.
