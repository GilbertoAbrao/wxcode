---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/cli.py
type: module
updated: 2026-01-21
status: active
---

# cli.py

## Purpose

Typer CLI application providing command-line interface for all WXCODE operations. Includes commands for project import, initialization, dependency analysis, PDF splitting, element enrichment, procedure/schema/class parsing, Neo4j synchronization, impact analysis, and GSD context generation. Acts as the primary user interface for batch operations.

## Exports

- `app` - Typer application instance
- `import_project()` - Import WinDev project to MongoDB
- `init_project()` - Initialize project from directory
- `analyze()` - Analyze project dependencies
- `split_pdf()` - Split documentation PDF
- `enrich()` - Enrich elements with PDF data
- `parse_procedures()` - Parse .wdg files
- `parse_schema()` - Parse .xdd schema
- `parse_classes()` - Parse .wdc classes
- `sync_neo4j()` - Sync to Neo4j graph
- `impact()` - Analyze change impact
- `path()` - Find paths between elements
- `hubs()` - Find highly connected nodes
- `dead_code()` - Find unused code
- `gsd_context()` - Generate GSD context

## Dependencies

- [[src-wxcode-config]] - Application settings
- [[src-wxcode-database]] - MongoDB connection
- [[src-wxcode-parser-project_mapper]] - Project element mapping
- [[src-wxcode-analyzer-dependency_analyzer]] - Dependency analysis
- [[src-wxcode-graph-neo4j_sync]] - Neo4j synchronization
- [[src-wxcode-graph-impact_analyzer]] - Impact analysis
- typer - CLI framework
- rich - Terminal formatting

## Used By

TBD
