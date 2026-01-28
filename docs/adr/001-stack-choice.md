# ADR-001: Escolha da Stack FastAPI + Jinja2

## Status

Aceito

## Contexto

Precisamos definir a stack de destino padrão para conversão de projetos WinDev/WebDev. Os desenvolvedores WinDev atuais precisam de uma curva de aprendizado suave.

## Decisão

Escolhemos **FastAPI + Jinja2** como stack padrão por:

1. **Python é acessível** - Sintaxe clara, similar a pseudocódigo
2. **Jinja2 é similar a templates WinDev** - Conceito de templates com variáveis
3. **FastAPI é moderno mas simples** - Tipagem, async, documentação automática
4. **Ecossistema rico** - Muitas bibliotecas disponíveis
5. **Boa documentação** - Facilita aprendizado

## Alternativas Consideradas

| Stack | Prós | Contras |
|-------|------|---------|
| Django | Full-featured, ORM | Mais opinado, curva maior |
| Flask | Simples | Menos estruturado |
| Next.js | React, SSR | JavaScript, maior complexidade |
| NestJS | TypeScript, estruturado | Mais complexo |

## Consequências

### Positivas
- Desenvolvedores WinDev conseguem entender o código rapidamente
- Python é amplamente suportado
- FastAPI gera documentação OpenAPI automaticamente

### Negativas
- Pode não ser ideal para projetos que precisam de React/Vue
- Python é mais lento que Go/Rust para casos específicos

## Notas

A arquitetura permite adicionar outras stacks no futuro. FastAPI + Jinja2 é apenas o padrão.
