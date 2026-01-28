---
phase: 14-data-models
plan: 01
subsystem: database
tags: [beanie, mongodb, pydantic, data-models]

# Dependency graph
requires: []
provides:
  - Stack model for target technology definition
  - OutputProject model for conversion target tracking
  - Milestone model for element conversion tracking
affects: [14-02, stack-selection-ui, output-project-api, milestone-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - PydanticObjectId for inter-document references
    - (str, Enum) for JSON-serializable enums
    - dict[str, str] for typed dictionary fields

key-files:
  created:
    - src/wxcode/models/stack.py
    - src/wxcode/models/output_project.py
    - src/wxcode/models/milestone.py
  modified: []

key-decisions:
  - "Use PydanticObjectId instead of Link to avoid extra queries"
  - "Stack uses string stack_id as business key (MongoDB generates _id)"
  - "element_name denormalized in Milestone for display without joins"

patterns-established:
  - "Pattern: PydanticObjectId for references between Beanie Documents"
  - "Pattern: (str, Enum) for status enums to enable JSON serialization"
  - "Pattern: default_factory=dict for typed dictionary fields"

# Metrics
duration: 4min
completed: 2026-01-23
---

# Phase 14 Plan 01: Core Data Models Summary

**Stack, OutputProject, and Milestone Beanie Documents for v4 multi-stack LLM-driven generation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-23T14:24:18Z
- **Completed:** 2026-01-23T14:28:30Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments

- Stack model with 13 fields defining target technology characteristics
- OutputProject model connecting KB to target Stack with workspace tracking
- Milestone model tracking individual element conversion status

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Stack Model** - `24b3f99` (feat)
2. **Task 2: Create OutputProject Model** - `8b40ecf` (feat)
3. **Task 3: Create Milestone Model** - `ab8a8d7` (feat)

## Files Created

- `src/wxcode/models/stack.py` - Stack Document with stack_id, name, group, language, framework, orm, orm_pattern, template_engine, file_structure, naming_conventions, type_mappings, imports_template, model_template
- `src/wxcode/models/output_project.py` - OutputProject Document with kb_id, name, stack_id, configuration_id, workspace_path, status, timestamps; OutputProjectStatus enum
- `src/wxcode/models/milestone.py` - Milestone Document with output_project_id, element_id, element_name, status, timestamps; MilestoneStatus enum

## Decisions Made

- **PydanticObjectId over Link:** Used PydanticObjectId for all inter-document references (kb_id, output_project_id, element_id) to avoid automatic fetching and extra queries. Follows existing pattern from conversion_history.py.
- **String stack_id as business key:** Stack uses string stack_id (like "fastapi-htmx") as the primary identifier for API/UI usage, while MongoDB generates _id automatically for internal references.
- **Denormalized element_name:** Milestone includes element_name denormalized to avoid extra queries when displaying milestone lists.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Core data models ready for 14-02 (register models in Beanie init)
- Stack model ready for stack data seeding
- OutputProject model ready for API endpoint creation
- Milestone model ready for element conversion tracking

---
*Phase: 14-data-models*
*Completed: 2026-01-23*
