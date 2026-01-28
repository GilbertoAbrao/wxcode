---
name: WX-Convert: Milestone
description: Orchestrate conversion of a WinDev module as a complete milestone.
category: Conversion
tags: [wxcode, conversion, milestone, mcp]
---

# WinDev Conversion Milestone: {{module_name}}

## Context

- **Project:** {{project_name}}
- **Module:** {{module_name}}
- **Target Stack:** FastAPI + Jinja2 + HTMX
- **Date Started:** {{date}}

## Objective

Convert all elements in {{module_name}} to the target stack, following topological order to respect dependencies. Track progress using MCP tools and mark elements as converted upon completion.

## Prerequisites

Before starting this milestone:

1. **Project imported:** `wxcode import` completed successfully
2. **Elements enriched:** `wxcode enrich` completed (controls, events, procedures extracted)
3. **Schema parsed:** `wxcode parse-schema` completed (database tables available)
4. **Analysis done:** `wxcode analyze {{project_name}}` completed
5. **Neo4j synced:** `wxcode sync-neo4j {{project_name}}` completed (for graph queries)
6. **MCP Server running:** `python -m wxcode.mcp.server`

## Workflow

### Phase 1: Discovery

Use MCP tools to understand the conversion scope:

**Check current progress:**
```
get_conversion_stats(project_name="{{project_name}}")
```
- Review total_elements, completed, progress_percentage
- Check by_layer breakdown for module focus

**Get conversion order:**
```
get_topological_order(project_name="{{project_name}}", layer="{{target_layer}}")
```
- Review ordered list of elements
- Note dependencies between elements
- Identify natural batches (same layer, similar complexity)

**Find elements ready now:**
```
get_conversion_candidates(project_name="{{project_name}}", layer="{{target_layer}}", limit=10)
```
- These elements have all dependencies satisfied
- Start conversion with these candidates

### Phase 2: Element Conversion

For each element in the conversion order:

1. **Get element details:**
   ```
   get_element(element_name="ELEMENT_NAME", project_name="{{project_name}}")
   ```
   - Review raw_content (WLanguage source)
   - Review dependencies.uses and dependencies.data_files
   - Check ast for procedures and events

2. **Get UI structure:**
   ```
   get_controls(element_name="ELEMENT_NAME", project_name="{{project_name}}")
   ```
   - Review control hierarchy
   - Note data_bindings for form fields
   - Check events for click handlers, validation

3. **Get business logic:**
   ```
   get_procedures(element_name="ELEMENT_NAME", project_name="{{project_name}}")
   ```
   - Review local procedures (is_local=True)
   - Review global procedures called by element
   - Note parameters and return types

4. **Convert element:**
   - Generate Pydantic models from data_bindings and schema
   - Generate FastAPI route from element type and events
   - Generate Jinja2 template from controls
   - Run `/wx-convert:phase` for detailed conversion workflow

5. **Mark element converted:**
   ```
   mark_converted(
     element_name="ELEMENT_NAME",
     project_name="{{project_name}}",
     confirm=True,
     notes="Converted via milestone workflow"
   )
   ```

### Phase 3: Validation

After all elements converted:

**Verify completion:**
```
get_conversion_stats(project_name="{{project_name}}")
```
- Confirm progress_percentage matches expectations
- Check by_layer for 100% in target layers

**Run validation tests:**
- Start generated FastAPI application
- Verify routes respond correctly
- Test form submissions
- Check data persistence

**Generate final output:**
```
wxcode export {{project_name}} -o ./output/{{module_name}}
```

## Success Criteria

- [ ] All elements in module have status "converted" or "validated"
- [ ] get_conversion_stats shows expected progress
- [ ] Generated FastAPI routes respond with 200
- [ ] Templates render without errors
- [ ] Data bindings connect to correct database tables
- [ ] Form validation matches original WLanguage validation
- [ ] All local procedures converted to Python functions

## Progress Tracking

| Element | Type | Status | Commit | Notes |
|---------|------|--------|--------|-------|
| | | | | |

## References

- [MCP + GSD Integration Guide](docs/mcp-gsd-integration.md)
- [WLanguage to Python Mapping](CLAUDE.md#mapeamento-wlanguage--python)
- [Target Stack Architecture](docs/architecture.md)
