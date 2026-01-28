# Domain Pitfalls: Multi-Stack Code Generation

**Domain:** Multi-target code generator for WinDev to Django, Laravel, NestJS, Rails, and 10+ other stacks
**Researched:** 2026-01-23
**Context:** wxcode currently generates FastAPI+Pydantic. Adding support for 14 additional stack combinations requires rearchitecting the generator layer without breaking existing functionality.

---

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or fundamental architecture failures.

### Pitfall 1: Hardcoded Stack Assumptions in Base Generator

**What goes wrong:** The current `BaseGenerator` class contains FastAPI-specific assumptions (template paths like `templates/python`, file paths like `app/models/`, method names like `_to_snake_case`). When adding new stacks, developers copy-paste the base class or add conditional logic, creating parallel hierarchies and spaghetti code.

**Why it happens:** The original generator was built for a single target. Abstractions weren't designed for extensibility. When pressed for time, developers extend rather than refactor.

**Consequences:**
- Each new stack requires modifying the base class
- Changes to shared logic must be replicated across all stacks
- Bugs appear in some stacks but not others
- Testing becomes exponentially more complex

**Warning signs:**
- `if stack == "django":` conditionals appearing in base class
- Multiple `template_subdir` properties being used for different purposes
- Generated file paths hardcoded with `/app/` or `/src/`
- The word "TODO: support other stacks" appearing in code

**Prevention:**
1. Define a `StackProfile` interface that encapsulates ALL stack-specific decisions:
   - File structure (where models go, where routes go)
   - Naming conventions (snake_case vs PascalCase vs camelCase)
   - Template directory
   - Import style
   - ORM pattern (Active Record vs Data Mapper)
2. Make `BaseGenerator` truly abstract, taking a `StackProfile` dependency
3. Implement `StackProfile` for each target (e.g., `DjangoProfile`, `LaravelProfile`)

**Phase to address:** Architecture phase. Must be resolved before implementing ANY new stack.

**Sources:**
- Current codebase analysis: `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/generator/base.py`
- [Strumenta: A Guide to Code Generation](https://tomassetti.me/code-generation/)

---

### Pitfall 2: Type Mapping Without Precision/Scale Preservation

**What goes wrong:** WinDev types like `Numeric(18,4)` or `Currency` have specific precision requirements. The current `TYPE_MAP` loses this information, mapping everything to Python's `Decimal` without specifying precision. When generating for Django or Laravel, the generated model lacks constraints, causing silent data truncation.

**Why it happens:** Each target stack has different ways to express precision:
- Python/Pydantic: `Decimal` (precision handled at runtime)
- Django: `DecimalField(max_digits=18, decimal_places=4)`
- Laravel: `$table->decimal('amount', 18, 4)`
- Rails: `t.decimal :amount, precision: 18, scale: 4`
- TypeScript/Prisma: `@db.Decimal(18, 4)`

The simple `TYPE_MAP` approach cannot capture this variation.

**Consequences:**
- Financial data gets truncated (storing `123456.789` as `123456.78`)
- Currency calculations fail due to rounding errors
- Compliance issues for regulated industries (banking, healthcare)
- Data loss that's invisible until production

**Warning signs:**
- Money/currency fields showing rounded values
- Database migration warnings about precision
- Type mapping that returns just `Decimal` or `float` without metadata
- No tests covering precision edge cases

**Prevention:**
1. Create a `MappedTypeWithMeta` structure that preserves precision:
   ```python
   @dataclass
   class MappedTypeWithMeta:
       type_name: str
       precision: int | None = None
       scale: int | None = None
       nullable: bool = False
       constraints: dict[str, Any] = field(default_factory=dict)
   ```
2. Modify type mappers to produce stack-specific output INCLUDING precision
3. Template generation must consume and render precision appropriately
4. Add validation tests comparing source schema precision with generated output

**Phase to address:** Core infrastructure phase. Must be in place before generating any financial/decimal types.

**Sources:**
- [EF Core Decimal Precision Warning](https://www.codegenes.net/blog/ef-core-6-decimal-precision-warning/)
- [Laravel Numeric Types](https://medium.com/@sehouli.hamza/understanding-numeric-types-in-laravel-migration-schemas-integer-float-decimal-double-bd5cddd12705)
- [Pydantic Decimal Precision PR](https://github.com/pydantic/pydantic/pull/6810)

---

### Pitfall 3: Nullable/Optional Semantics Mismatch

**What goes wrong:** Each language handles nullability differently:
- **TypeScript:** `null` vs `undefined` vs optional (`?`)
- **Python:** `None` with `Optional[T]` or `T | None`
- **PHP:** `?Type` prefix or union types
- **Ruby:** `nil` (no type annotations by default)

A WinDev field marked as "nullable" gets translated incorrectly, causing runtime errors or database constraint violations.

**Why it happens:** The source schema has a simple boolean `nullable: true/false`, but target languages have nuanced concepts:
- Optional parameter (can be omitted) vs Nullable (can be explicitly null)
- Default value handling differs (`undefined` uses default in TS, `null` does not)
- Some frameworks distinguish "not provided" from "explicitly null"

**Consequences:**
- API endpoints reject valid requests (missing vs null confusion)
- Database inserts fail on NOT NULL constraints
- TypeScript strict mode errors
- Django/Laravel form validation rejects empty fields

**Warning signs:**
- Generated TypeScript has `T | null | undefined` everywhere
- Optional fields in Python are `Optional[T] = None` when they should be required
- ORM complaints about null constraint violations
- "undefined is not assignable to null" TypeScript errors

**Prevention:**
1. Distinguish between source semantics:
   - `nullable: true` = field can contain null value
   - `has_default: true` = field can be omitted (uses default)
   - `required: false` = field might not be present at all
2. Map these three concepts to each target's idioms:
   ```
   Source: nullable=true, has_default=false, required=true
   Python: field: str | None  # Required, but value can be None
   TypeScript: field: string | null  # Not optional, but nullable
   Django: field = CharField(null=True, blank=False)
   ```
3. Test with validation scenarios for each combination

**Phase to address:** Type mapping phase. Critical for API and form generation.

**Sources:**
- [TypeScript Optional vs Nullable](https://betterstack.com/community/guides/scaling-nodejs/typescript-optional-properties/)
- [OpenAPI Null Best Practices](https://www.speakeasy.com/openapi/schemas/null)

---

### Pitfall 4: Naming Convention Collisions with Reserved Words

**What goes wrong:** WinDev allows field names like `class`, `type`, `from`, `import`, `end` which are reserved keywords in target languages. Generated code has syntax errors or unexpected behavior.

**Why it happens:** Each language has different reserved words:
- Python: `class`, `from`, `import`, `global`, `type`, `async`
- JavaScript/TypeScript: `class`, `const`, `function`, `delete`, `default`
- PHP: `class`, `public`, `private`, `abstract`, `final`
- Ruby: `class`, `end`, `begin`, `rescue`, `module`

The source schema uses valid WLanguage identifiers that become invalid in targets.

**Consequences:**
- Generated code fails to compile/parse
- Runtime errors when accessing properties
- Developer must manually rename fields
- ORM mapping breaks if field name doesn't match database column

**Warning signs:**
- Syntax errors in generated files
- "Reserved word" or "unexpected token" errors
- Fields named `class_`, `_from`, `type_field`
- Tests failing on specific field names

**Prevention:**
1. Maintain a reserved word list PER TARGET LANGUAGE
2. Implement a `sanitize_identifier(name, target)` function that:
   - Checks against reserved word list
   - Appends suffix (`_field`, `_`) or prefix (`f_`) if collision
   - Tracks original name for ORM column mapping
3. Generate column mapping annotations when renaming:
   ```python
   # Django
   class_field = models.CharField(db_column='class')

   # SQLAlchemy
   class_field: str = Field(alias='class')
   ```
4. Add unit tests with ALL reserved words for each target

**Phase to address:** Type mapping / Generator infrastructure. Simple to implement early, painful to retrofit.

**Sources:**
- [Rails Naming Conventions and Conflicts](https://gist.github.com/iangreenleaf/b206d09c587e8fc6399e)
- [Active Record Naming Conflicts](https://guides.rubyonrails.org/active_record_basics.html)

---

### Pitfall 5: ORM Pattern Mismatch (Active Record vs Data Mapper)

**What goes wrong:** Different frameworks use fundamentally different ORM patterns:
- **Active Record** (Rails, Laravel Eloquent, Django): Model classes have database methods (`.save()`, `.delete()`)
- **Data Mapper** (TypeORM option, SQLAlchemy, Prisma): Separate repository/manager handles persistence

Generating Active Record-style models for a Data Mapper framework produces non-idiomatic code that fights the framework.

**Why it happens:** The current FastAPI generator uses Pydantic models (essentially DTOs) with Beanie ODM (Active Record-like for MongoDB). This pattern doesn't translate directly to:
- NestJS with TypeORM using Data Mapper pattern
- Go with GORM (yet another pattern)
- Node.js with Prisma (schema-first, generated client)

**Consequences:**
- Generated code doesn't follow framework best practices
- Developers have to rewrite generated code
- Business logic ends up in wrong layer
- Relationships and lazy loading don't work as expected

**Warning signs:**
- Model classes with `.save()` methods in Data Mapper frameworks
- Repository classes generated for Active Record frameworks
- Generated code imports both model AND repository layers inconsistently
- Framework documentation conflicts with generated patterns

**Prevention:**
1. Define ORM pattern in `StackProfile`:
   ```python
   class StackProfile:
       orm_pattern: Literal["active_record", "data_mapper", "repository", "prisma"]
   ```
2. Generate appropriate layer based on pattern:
   - Active Record: Model has persistence methods
   - Data Mapper: Separate Entity + Repository
   - Prisma: Schema file + generated client usage
3. Template sets must differ fundamentally between patterns (not just syntax)
4. Include framework-specific relationship handling

**Phase to address:** Architecture phase. Fundamental to how each generator is structured.

**Sources:**
- [Comparing NestJS ORMs](https://blog.logrocket.com/comparing-four-popular-nestjs-orms/)
- [The ORM Delusion](https://matthewdaly.co.uk/blog/2022/06/05/the-orm-delusion/)

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or significant refactoring.

### Pitfall 6: Leaky Abstraction in Generated Code

**What goes wrong:** Generated code references framework internals or makes assumptions that leak through the abstraction. When the framework updates or configuration changes, generated code breaks.

**Why it happens:** Generators take shortcuts:
- Hardcoding import paths (`from app.config import settings`)
- Assuming specific framework versions
- Using deprecated APIs that "still work"
- Embedding configuration values instead of reading from environment

**Consequences:**
- Framework upgrade breaks generated code
- Configuration changes require regeneration
- Developers can't customize without touching generated files
- Generated code diverges from framework best practices

**Warning signs:**
- Import paths like `from app.` assuming directory structure
- Framework version pinned in generated code
- Deprecation warnings in generated output
- "Works on my machine" after framework updates

**Prevention:**
1. Generate code that follows official framework patterns
2. Use relative imports where possible
3. Externalize configuration (environment variables, config files)
4. Include framework version in generation metadata for future migration
5. Test generated code against current AND next major version of target framework

**Phase to address:** Generator implementation. Ongoing discipline.

**Sources:**
- [Leaky Abstractions](https://medium.com/machine-words/leaky-abstractions-2c42dd6e53d5)
- [All Abstractions Are Failed Abstractions](https://blog.codinghorror.com/all-abstractions-are-failed-abstractions/)

---

### Pitfall 7: Template Explosion Without Shared Components

**What goes wrong:** Each stack gets its own complete template set. When updating shared logic (header comments, imports), changes must be made in 15+ places. Templates diverge over time.

**Why it happens:** Initial implementation copies templates for each stack. No mechanism for template inheritance or includes. Jinja2 `{% include %}` not used or used inconsistently.

**Consequences:**
- Bug fixes applied to some templates but not others
- Inconsistent output style across stacks
- Massive template directory (15 stacks x 5 template types = 75+ templates)
- Fear of changing templates (might break something)

**Warning signs:**
- Copy-paste commit messages for template files
- Template files >80% identical across stacks
- Different header comment formats per stack
- No shared template fragments

**Prevention:**
1. Design template hierarchy:
   ```
   templates/
     _base/
       header.j2
       docstring.j2
       imports.j2
     python/
       _layout.j2 (extends _base/)
       model.py.j2
     typescript/
       _layout.j2
       model.ts.j2
   ```
2. Use Jinja2 inheritance (`{% extends %}`) and includes (`{% include %}`)
3. Stack-specific templates override only what's different
4. Generate a "template coverage" report showing shared vs unique

**Phase to address:** Template architecture phase. Before adding second stack.

---

### Pitfall 8: N+1 Query Generation

**What goes wrong:** Generated code produces N+1 query patterns that work correctly but have terrible performance. ORM relationship traversal in loops.

**Why it happens:** WLanguage code often uses loops like:
```
FOR EACH Customer
    FOR EACH Order OF Customer
        // process
```
Direct translation produces N+1:
```python
for customer in customers:
    for order in customer.orders:  # N queries!
```

**Consequences:**
- Performance degrades exponentially with data size
- Database connection pool exhaustion
- Timeouts in production
- Works fine in dev (small data), fails in prod (real data)

**Warning signs:**
- Nested loops accessing related objects
- No eager loading annotations in generated code
- Performance tests showing non-linear degradation
- Database query counts in hundreds for simple operations

**Prevention:**
1. Detect relationship traversal patterns in source code
2. Generate eager loading by default:
   ```python
   # Django
   customers = Customer.objects.prefetch_related('orders')

   # SQLAlchemy
   customers = session.query(Customer).options(joinedload(Customer.orders))

   # Prisma
   const customers = await prisma.customer.findMany({ include: { orders: true } })
   ```
3. Add performance warnings as comments when eager loading isn't possible
4. Include N+1 detection in generated tests

**Phase to address:** Service/Query generation phase. Critical for production readiness.

**Sources:**
- [Django ORM Best Practices](https://www.rootstrap.com/blog/tips-for-using-databases-with-django-orm-object-relational-mapper)
- [ORM N+1 Problem](https://www.altexsoft.com/blog/orm-object-relational-mapping/)

---

### Pitfall 9: Inconsistent Date/Time Handling

**What goes wrong:** WinDev has Date, DateTime, Time, Duration. Target stacks have different defaults:
- Python: `datetime.datetime` (timezone-naive by default)
- JavaScript: `Date` (always UTC internally)
- PHP: `DateTime` (needs explicit timezone)
- Database: Various (MySQL DATETIME vs PostgreSQL TIMESTAMPTZ)

Generated code has timezone bugs, serialization issues, and comparison failures.

**Why it happens:** Date/time handling is notoriously complex. Generators often pick "simplest" approach which ignores timezones. Source WinDev data may not have timezone info.

**Consequences:**
- Events appear at wrong times
- Scheduled tasks fire at wrong hours
- Date comparisons fail across timezones
- API serialization produces unexpected formats

**Warning signs:**
- No timezone annotations in generated code
- Date fields using `date` when source is `datetime`
- String formatting without ISO 8601
- "Off by one day" bugs around midnight

**Prevention:**
1. Establish timezone policy: UTC everywhere, convert at edges
2. Generate timezone-aware types:
   ```python
   # Python
   from datetime import datetime, timezone
   created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

   # TypeScript
   createdAt: Date  // Always UTC
   ```
3. Include serialization format in API generation (ISO 8601)
4. Add date/time edge case tests (DST transitions, year boundaries)

**Phase to address:** Type mapping phase. Needs clear policy decision.

---

### Pitfall 10: Missing Relationship Cardinality Translation

**What goes wrong:** WinDev relationships (foreign keys, links) have cardinality (one-to-one, one-to-many, many-to-many). This information exists in schema but doesn't translate correctly to all ORMs.

**Why it happens:** Different ORMs express relationships differently:
- Django: `ForeignKey`, `OneToOneField`, `ManyToManyField`
- Laravel: `belongsTo`, `hasMany`, `belongsToMany`
- TypeORM: `@ManyToOne`, `@OneToMany`, `@ManyToMany`
- Rails: `belongs_to`, `has_many`, `has_and_belongs_to_many`

Simple FK detection misses:
- Junction tables (many-to-many)
- Self-referential relationships
- Polymorphic associations

**Consequences:**
- Missing inverse relationships
- Orphaned records when parent deleted
- Incorrect cascade behavior
- Can't navigate relationships in generated code

**Warning signs:**
- Foreign keys without corresponding relationship definitions
- Missing `related_name` or back-references
- Junction tables generated as regular entities
- "Cannot access X from Y" errors

**Prevention:**
1. Detect relationship patterns in schema:
   - FK column ending in `_id` → one-to-many
   - Junction table with two FKs → many-to-many
   - Unique FK → one-to-one
2. Generate BOTH sides of relationships:
   ```python
   # Django - both sides explicit
   class Customer(models.Model):
       pass

   class Order(models.Model):
       customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
   ```
3. Include cascade/delete behavior appropriate to target
4. Add relationship navigation tests

**Phase to address:** Schema analysis and generator implementation.

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable without major refactoring.

### Pitfall 11: Inconsistent Code Style Across Generated Files

**What goes wrong:** Generated Python uses 4-space indent, generated TypeScript uses 2-space. Some files have trailing newlines, others don't. Formatting is inconsistent.

**Prevention:**
- Run language-specific formatters post-generation (Black, Prettier, php-cs-fixer, RuboCop)
- Configure formatter in generation pipeline
- Include `.editorconfig` in generated projects

**Phase to address:** Generator infrastructure. Simple addition.

---

### Pitfall 12: No Idempotent Generation

**What goes wrong:** Running the generator twice produces different output (different timestamps, different ordering). This makes it hard to verify changes and pollutes git diffs.

**Prevention:**
- Sort outputs deterministically (by name, not by insertion order)
- Use stable timestamps or omit them
- Hash-based change detection before writing
- Generated file header includes generation parameters for comparison

**Phase to address:** Generator infrastructure.

---

### Pitfall 13: Generated Tests That Don't Run

**What goes wrong:** Tests are generated but have import errors, missing fixtures, or assumptions about database state. Developers immediately delete generated tests.

**Prevention:**
- Generate minimal, runnable tests (even if trivial)
- Include fixture generation
- Add setup/teardown for database tests
- Test the generated tests in CI

**Phase to address:** Test generation phase.

---

### Pitfall 14: Magic Strings in Type Mapping

**What goes wrong:** Type names are hardcoded as strings throughout:
```python
if type_name == "string":  # What about "chaîne"?
    return "str"
```

Prevention:
- Use enums or constants for type identifiers
- Canonical normalization before comparison
- Exhaustive match with default case handling

**Phase to address:** Type mapping phase. Refactoring needed.

---

### Pitfall 15: Generated Comments That Become Lies

**What goes wrong:** Generated code includes comments like "TODO: implement" or "Auto-generated, do not edit" but developers MUST edit the file, making comments misleading.

**Prevention:**
- Distinguish "safe to edit" vs "will be overwritten" files
- Update TODO comments to be specific
- Include generation timestamp and source reference
- Consider generating "protected regions" that survive regeneration

**Phase to address:** Template design phase.

---

## Phase-Specific Warnings Summary

| Phase | Likely Pitfall | Mitigation |
|-------|----------------|------------|
| **Architecture** | Hardcoded stack assumptions (#1) | Define StackProfile interface before any implementation |
| **Architecture** | ORM pattern mismatch (#5) | Document each target's ORM pattern in profile |
| **Type Mapping** | Precision loss (#2) | Create MappedTypeWithMeta that preserves precision/scale |
| **Type Mapping** | Nullable semantics (#3) | Model nullable/optional/required as separate concepts |
| **Type Mapping** | Reserved words (#4) | Build per-language reserved word lists and sanitizer |
| **Template Design** | Template explosion (#7) | Design template inheritance before second stack |
| **Generator Implementation** | Leaky abstractions (#6) | Follow official framework patterns, externalize config |
| **Service Generation** | N+1 queries (#8) | Detect relationship traversal, generate eager loading |
| **Schema Generation** | Relationship cardinality (#10) | Detect and generate both sides of relationships |
| **Test Generation** | Non-runnable tests (#13) | Generate minimal working tests with fixtures |
| **Infrastructure** | Non-idempotent output (#12) | Deterministic ordering, stable timestamps |

---

## Critical Path: What Must Not Be Skipped

1. **StackProfile abstraction** - Without this, every new stack is a copy-paste nightmare. Define the interface BEFORE implementing the second stack.

2. **Precision-preserving type mapping** - Financial data loss is invisible until production disaster. Test with edge cases (max precision values).

3. **Reserved word handling** - One collision = syntax error = regeneration failure. Complete lists per language.

4. **Template inheritance architecture** - 15 stacks x 10 templates = 150 files without sharing. Design hierarchy first.

5. **Relationship generation both directions** - Unidirectional relationships are half-usable. Always generate back-references.

---

## Current Codebase Observations

Analyzing the existing wxcode generator code reveals these specific risks for multi-stack expansion:

### In `base.py`:
- `template_subdir: str = "python"` - Stack-specific default
- `_to_snake_case`, `_to_pascal_case`, `_to_camel_case` - Good, but need per-stack convention selection
- `_detect_file_type` checking `/models/`, `/services/`, `/routes/` - Hardcoded Python/FastAPI structure

### In `schema_generator.py`:
- `TYPE_MAP: dict[int, str]` - No precision preservation
- Output path `app/models/{filename}.py` - Hardcoded structure
- Email detection via field name heuristic - Works for Python, may not for typed languages

### In `domain_generator.py`:
- Dual TYPE_MAP (WLanguage and defaults) - Needs to be per-stack
- Inheritance handling `self._class_names` - Good pattern, keep
- `_format_constant_value` - Python-specific string quoting

### In `python/type_mapper.py`:
- Good abstraction with `BaseTypeMapper` and `MappedType`
- Missing: precision, scale, constraints in `MappedType`
- Needs: per-stack mapper implementations (LaravelTypeMapper, etc.)

---

## Sources

### Multi-Stack Architecture
- [Strumenta: A Guide to Code Generation](https://tomassetti.me/code-generation/)
- [Google Multi-Agent Design Patterns](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/)

### Type Safety and ORM
- [TypeSafe Database Querying via Code Generation](https://www.geldata.com/blog/typesafe-database-querying-via-code-generation)
- [Comparing NestJS ORMs](https://blog.logrocket.com/comparing-four-popular-nestjs-orms/)
- [Prisma vs Sequelize](https://www.prisma.io/docs/orm/more/comparisons/prisma-and-sequelize)
- [The ORM Delusion](https://matthewdaly.co.uk/blog/2022/06/05/the-orm-delusion/)

### Precision and Data Types
- [EF Core 6 Decimal Precision Warning](https://www.codegenes.net/blog/ef-core-6-decimal-precision-warning/)
- [Laravel Numeric Types in Migrations](https://medium.com/@sehouli.hamza/understanding-numeric-types-in-laravel-migration-schemas-integer-float-decimal-double-bd5cddd12705)
- [SQL Type Coercion and Precision](https://selectfromwhereand.com/posts/sql_types/)

### Naming and Conventions
- [Rails Naming Conventions](https://gist.github.com/iangreenleaf/b206d09c587e8fc6399e)
- [Active Record Basics](https://guides.rubyonrails.org/active_record_basics.html)
- [Building Rails with Legacy Database](https://twinsunsolutions.com/blog/building-a-ruby-on-rails-app-with-a-legacy-database/)

### Nullable Types
- [TypeScript Optional Properties and Null Handling](https://betterstack.com/community/guides/scaling-nodejs/typescript-optional-properties/)
- [OpenAPI Null Best Practices](https://www.speakeasy.com/openapi/schemas/null)

### Leaky Abstractions
- [Leaky Abstractions - Medium](https://medium.com/machine-words/leaky-abstractions-2c42dd6e53d5)
- [All Abstractions Are Failed Abstractions](https://blog.codinghorror.com/all-abstractions-are-failed-abstractions/)
- [Law of Leaky Abstractions](https://www.researchgate.net/publication/213877619_The_Law_of_Leaky_Abstractions)

### Performance
- [Django ORM Best Practices](https://www.rootstrap.com/blog/tips-for-using-databases-with-django-orm-object-relational-mapper)
- [ORM Explained](https://www.altexsoft.com/blog/orm-object-relational-mapping/)
