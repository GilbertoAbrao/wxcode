# Conversion UI System

User-friendly abstraction of the OpenSpec Change system for the frontend.

## ADDED Requirements

### Requirement: Conversion Abstraction

The frontend MUST present OpenSpec Changes as "Conversões" (Conversions) without exposing internal terminology.

#### Scenario: Terminology mapping
**Given** the frontend displays conversion information
**When** showing Change data to the user
**Then** "Change" MUST be displayed as "Conversão"
**And** "Tasks" MUST be displayed as "Passos"
**And** "Requirements" MUST be displayed as "Requisitos"
**And** "Scenarios" MUST be displayed as "Validações"
**And** the term "OpenSpec" MUST NOT appear anywhere in the UI

### Requirement: Conversion Card Display

The frontend MUST display conversions as visual cards with progress indicators.

#### Scenario: Card shows essential info
**Given** a conversion exists for a project
**When** viewing the conversions list
**Then** each card MUST show the conversion title
**And** MUST show a progress bar (0-100%)
**And** MUST show the current status (Pendente/Em Progresso/Completo)
**And** MUST show the number of completed steps vs total

#### Scenario: Progress calculation
**Given** a conversion with 5 steps
**When** 3 steps are marked as completed
**Then** the progress MUST show 60%
**And** the display MUST show "3/5 passos completos"

### Requirement: Conversion Detail View

The frontend MUST provide a detailed view of each conversion.

#### Scenario: Detail sections
**Given** a user opens a conversion detail
**When** viewing the detail page
**Then** the page MUST show a "Resumo" section with the conversion summary
**And** MUST show a "Passos" section with a checklist
**And** MUST show a "Requisitos" section listing what will be delivered
**And** MUST show a "Validações" section with test status

#### Scenario: Steps checklist
**Given** the steps section of a conversion
**When** displaying the steps
**Then** each step MUST show its title
**And** MUST show a checkbox indicating completion status
**And** completed steps MUST be visually distinct (strikethrough or checkmark)
**And** the current step MUST be highlighted

### Requirement: Validation Status Display

The frontend MUST show the status of automated validations.

#### Scenario: Validation badges
**Given** a conversion has validations defined
**When** displaying validation status
**Then** passing validations MUST show a green checkmark
**And** failing validations MUST show a red X
**And** pending validations MUST show a gray circle
**And** a summary badge MUST show "X/Y passando"

### Requirement: Conversion Actions

The frontend MUST provide action buttons for conversion management.

#### Scenario: Available actions
**Given** a conversion in "review" status
**When** viewing the conversion detail
**Then** an "Aprovar" button MUST be available
**And** a "Solicitar Ajustes" button MUST be available
**And** a "Ver Código Gerado" button MUST be available
**And** a "Ver Diff" button MUST be available

#### Scenario: Approve action
**Given** a user clicks "Aprovar"
**When** the action is processed
**Then** the conversion status MUST change to "completed"
**And** the generated code MUST be applied to the project
**And** the conversion MUST be archived

### Requirement: Single Active Conversion

The frontend MUST enforce one active conversion per project at a time.

#### Scenario: New conversion blocked
**Given** a project has an active conversion (status != completed)
**When** attempting to create a new conversion
**Then** the system MUST block the action
**And** MUST display a message explaining that the current conversion must be completed first

#### Scenario: Conversion history
**Given** a project has completed conversions
**When** viewing the conversions list
**Then** archived conversions MUST be visible in a "Histórico" section
**And** archived conversions MUST be read-only

### Requirement: Real-time Progress Updates

The frontend MUST update conversion progress in real-time.

#### Scenario: Live step updates
**Given** a conversion is in progress
**When** a step is completed by the backend
**Then** the UI MUST update the step status without page refresh
**And** the progress bar MUST update automatically

#### Scenario: WebSocket connection
**Given** a user is viewing a conversion detail
**When** the conversion is being processed
**Then** the frontend MUST maintain a WebSocket connection
**And** MUST receive real-time updates for status changes

### Requirement: Visualization Levels

The frontend MUST support different levels of detail based on user preference.

#### Scenario: Simple view
**Given** user preference is "Simples"
**When** viewing a conversion
**Then** only steps and progress MUST be shown
**And** requirements and validations MUST be hidden

#### Scenario: Standard view
**Given** user preference is "Padrão" (default)
**When** viewing a conversion
**Then** steps, requirements, and validations MUST be shown

#### Scenario: Advanced view
**Given** user preference is "Avançado"
**When** viewing a conversion
**Then** all sections MUST be shown
**And** "Decisões Técnicas" section MUST be visible
**And** detailed diff view MUST be available
