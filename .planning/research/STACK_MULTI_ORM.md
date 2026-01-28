# Stack Research: Multi-ORM Schema Generation

**Project:** wxcode Multi-Stack Support (v4 Milestone)
**Researched:** 2026-01-23
**Overall confidence:** HIGH

## Executive Summary

This research covers programmatic model/schema generation for Django ORM, Laravel Eloquent, NestJS (TypeORM and Prisma), and Rails ActiveRecord. The goal is expanding wxcode's schema generator to support 15 target stack combinations beyond the existing FastAPI+Pydantic.

**Key insight:** All target ORMs use declarative model definitions that map cleanly to Jinja2 templates. The existing template-based architecture (BaseGenerator + Jinja2) scales well to all stacks. No new generation approach needed.

**Recommendation:** Create stack-specific templates and type mapping dictionaries. One SchemaGenerator subclass per ORM with its own TYPE_MAP and templates.

## Recommended Approach

### Architecture: Template-per-Stack

```
src/wxcode/generator/
├── schema_generator.py          # Base + Pydantic (existing)
├── schema_django.py             # Django ORM generator
├── schema_eloquent.py           # Laravel Eloquent generator
├── schema_typeorm.py            # NestJS TypeORM generator
├── schema_prisma.py             # NestJS Prisma generator
├── schema_activerecord.py       # Rails ActiveRecord generator
└── templates/
    ├── python/model.py.j2       # Pydantic (existing)
    ├── django/model.py.j2       # Django models
    ├── php/model.php.j2         # Eloquent models
    ├── typescript/entity.ts.j2  # TypeORM entities
    ├── prisma/model.prisma.j2   # Prisma schema
    └── ruby/model.rb.j2         # ActiveRecord models
```

**Why this approach:**
- Consistent with existing wxcode architecture
- Jinja2 handles all target languages well
- Type mappings are the only ORM-specific logic
- Easy to add new stacks later

---

## Stack 1: Django ORM (Python)

### Current Version
- **Django 5.2** (stable, Jan 2026)
- **Django 6.0** (development, coming 2026)

**Source:** [Django Documentation](https://docs.djangoproject.com/en/5.2/ref/models/fields/)

### Model Syntax

```python
from django.db import models

class Cliente(models.Model):
    """Model for CLIENTE table."""

    class Meta:
        db_table = 'CLIENTE'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Foreign Key
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='clientes',
        null=True,
        blank=True
    )
```

### Type Mapping: HyperFile to Django

| HyperFile Type | Code | Django Field | Notes |
|----------------|------|--------------|-------|
| Binary | 1 | `BinaryField` | Use `max_length` if size known |
| Text/String | 2, 3 | `CharField` | Requires `max_length` |
| Integer (4 bytes) | 4 | `IntegerField` | |
| Integer (2 bytes) | 5 | `SmallIntegerField` | |
| Integer (1 byte) | 6 | `SmallIntegerField` | No TinyIntegerField |
| Integer (8 bytes) | 7 | `BigIntegerField` | |
| Real (4 bytes) | 8 | `FloatField` | |
| Real (8 bytes) | 9 | `FloatField` | |
| DateTime | 10 | `DateTimeField` | |
| Date | 11 | `DateField` | |
| Time | 12 | `TimeField` | |
| Boolean | 13 | `BooleanField` | |
| Currency | 14 | `DecimalField` | Use `max_digits=15, decimal_places=2` |
| Memo (text) | 15, 16, 18 | `TextField` | |
| Memo (binary) | 17 | `BinaryField` | |
| Duration | 19 | `DurationField` | |
| Character | 20 | `CharField(max_length=1)` | |
| Unicode string | 21 | `CharField` | Django uses UTF-8 by default |
| Unicode memo | 22 | `TextField` | |
| JSON | 23 | `JSONField` | |
| Auto-increment | 24 | `AutoField` | |
| Auto-increment (8) | 25 | `BigAutoField` | |
| UUID | 26 | `UUIDField` | |
| Password | 27, 28 | `CharField(max_length=128)` | Use hashing in application |

### Field Options Mapping

| WinDev Property | Django Option |
|-----------------|---------------|
| `nullable=True` | `null=True, blank=True` |
| `is_primary_key=True` | `primary_key=True` |
| `is_unique=True` | `unique=True` |
| `is_indexed=True` | `db_index=True` |
| `default_value=X` | `default=X` |
| `is_auto_increment=True` | Use `AutoField` or `BigAutoField` |

### Template Variables Needed

```python
{
    "table_name": "CLIENTE",
    "class_name": "Cliente",
    "meta_db_table": "CLIENTE",
    "fields": [
        {
            "name": "nome",
            "django_field": "CharField",
            "options": {"max_length": 100},
            "null": False,
            "blank": False,
            "unique": False,
            "comment": None
        }
    ],
    "foreign_keys": [
        {
            "name": "empresa",
            "to_model": "Empresa",
            "on_delete": "CASCADE",
            "related_name": "clientes",
            "null": True
        }
    ]
}
```

---

## Stack 2: Laravel Eloquent (PHP)

### Current Version
- **Laravel 12.x** (current, Jan 2026)
- **PHP 8.3+** recommended

**Source:** [Laravel Eloquent Documentation](https://laravel.com/docs/12.x/eloquent)

### Model Syntax

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Cliente extends Model
{
    /**
     * The table associated with the model.
     */
    protected $table = 'CLIENTE';

    /**
     * The primary key for the model.
     */
    protected $primaryKey = 'id';

    /**
     * Indicates if the model's ID is auto-incrementing.
     */
    public $incrementing = true;

    /**
     * The data type of the primary key.
     */
    protected $keyType = 'int';

    /**
     * Indicates if the model should be timestamped.
     */
    public $timestamps = true;

    /**
     * The attributes that are mass assignable.
     */
    protected $fillable = [
        'nome',
        'email',
        'cpf',
        'data_nascimento',
        'saldo',
        'ativo',
        'empresa_id',
    ];

    /**
     * The attributes that should be cast.
     */
    protected $casts = [
        'data_nascimento' => 'date',
        'saldo' => 'decimal:2',
        'ativo' => 'boolean',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];

    /**
     * Get the empresa that owns the cliente.
     */
    public function empresa(): BelongsTo
    {
        return $this->belongsTo(Empresa::class);
    }
}
```

### Type Mapping: HyperFile to Eloquent Casts

| HyperFile Type | Code | Eloquent Cast | Migration Type |
|----------------|------|---------------|----------------|
| Binary | 1 | - | `binary` |
| Text/String | 2, 3 | `string` | `string` |
| Integer (4 bytes) | 4 | `integer` | `integer` |
| Integer (2 bytes) | 5 | `integer` | `smallInteger` |
| Integer (1 byte) | 6 | `integer` | `tinyInteger` |
| Integer (8 bytes) | 7 | `integer` | `bigInteger` |
| Real (4 bytes) | 8 | `float` | `float` |
| Real (8 bytes) | 9 | `double` | `double` |
| DateTime | 10 | `datetime` | `dateTime` |
| Date | 11 | `date` | `date` |
| Time | 12 | - | `time` |
| Boolean | 13 | `boolean` | `boolean` |
| Currency | 14 | `decimal:2` | `decimal` |
| Memo (text) | 15, 16, 18 | `string` | `text` |
| Memo (binary) | 17 | - | `binary` |
| Duration | 19 | `integer` | `integer` |
| Character | 20 | `string` | `char` |
| Unicode string | 21 | `string` | `string` |
| Unicode memo | 22 | `string` | `text` |
| JSON | 23 | `array` or `object` | `json` |
| Auto-increment | 24 | - | `increments` |
| Auto-increment (8) | 25 | - | `bigIncrements` |
| UUID | 26 | - | `uuid` |
| Password | 27, 28 | `hashed` | `string` |

### Eloquent-Specific Patterns

**Timestamps convention:** Eloquent expects `created_at` and `updated_at` by default. If table uses different names, configure:

```php
const CREATED_AT = 'criado_em';
const UPDATED_AT = 'atualizado_em';
```

**Mass assignment:** Always generate `$fillable` with all non-auto columns (security best practice).

**Casts for special types:** Always cast dates, decimals, and booleans explicitly.

### Template Variables Needed

```php
{
    "namespace": "App\\Models",
    "class_name": "Cliente",
    "table_name": "CLIENTE",
    "primary_key": "id",
    "incrementing": true,
    "key_type": "int",
    "timestamps": true,
    "fillable": ["nome", "email", "cpf", "..."],
    "casts": {
        "data_nascimento": "date",
        "saldo": "decimal:2",
        "ativo": "boolean"
    },
    "relationships": [
        {
            "method": "empresa",
            "type": "BelongsTo",
            "model": "Empresa"
        }
    ]
}
```

---

## Stack 3: NestJS + TypeORM (TypeScript)

### Current Version
- **NestJS 11.x** (stable, Jan 2026)
- **TypeORM 0.3.x** (stable)
- **Node.js 22 LTS**

**Source:** [NestJS Database Documentation](https://docs.nestjs.com/techniques/database), [TypeORM Entities](https://typeorm.io/docs/entity/entities/)

### Entity Syntax

```typescript
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { Empresa } from './empresa.entity';

@Entity('CLIENTE')
export class Cliente {
  @PrimaryGeneratedColumn('increment', { type: 'bigint' })
  id: number;

  @Column({ type: 'varchar', length: 100 })
  nome: string;

  @Column({ type: 'varchar', length: 254, unique: true, nullable: true })
  email: string | null;

  @Column({ type: 'varchar', length: 14, unique: true })
  cpf: string;

  @Column({ type: 'date', nullable: true })
  dataNascimento: Date | null;

  @Column({ type: 'decimal', precision: 15, scale: 2, default: 0 })
  saldo: number;

  @Column({ type: 'boolean', default: true })
  ativo: boolean;

  @CreateDateColumn({ type: 'timestamp' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamp' })
  updatedAt: Date;

  @ManyToOne(() => Empresa, (empresa) => empresa.clientes, { nullable: true })
  @JoinColumn({ name: 'empresa_id' })
  empresa: Empresa | null;
}
```

### Type Mapping: HyperFile to TypeORM

| HyperFile Type | Code | TypeORM Column Type | TypeScript Type |
|----------------|------|---------------------|-----------------|
| Binary | 1 | `bytea` / `blob` | `Buffer` |
| Text/String | 2, 3 | `varchar` | `string` |
| Integer (4 bytes) | 4 | `int` | `number` |
| Integer (2 bytes) | 5 | `smallint` | `number` |
| Integer (1 byte) | 6 | `smallint` | `number` |
| Integer (8 bytes) | 7 | `bigint` | `number` |
| Real (4 bytes) | 8 | `float` | `number` |
| Real (8 bytes) | 9 | `double precision` | `number` |
| DateTime | 10 | `timestamp` | `Date` |
| Date | 11 | `date` | `Date` |
| Time | 12 | `time` | `string` |
| Boolean | 13 | `boolean` | `boolean` |
| Currency | 14 | `decimal` | `number` |
| Memo (text) | 15, 16, 18 | `text` | `string` |
| Memo (binary) | 17 | `bytea` / `blob` | `Buffer` |
| Duration | 19 | `int` | `number` |
| Character | 20 | `char` | `string` |
| Unicode string | 21 | `varchar` | `string` |
| Unicode memo | 22 | `text` | `string` |
| JSON | 23 | `json` / `jsonb` | `Record<string, any>` |
| Auto-increment | 24 | `int` (auto) | `number` |
| Auto-increment (8) | 25 | `bigint` (auto) | `number` |
| UUID | 26 | `uuid` | `string` |
| Password | 27, 28 | `varchar` | `string` |

### TypeORM Decorator Patterns

**Primary Key options:**
```typescript
// Auto-increment integer
@PrimaryGeneratedColumn()
id: number;

// Auto-increment bigint
@PrimaryGeneratedColumn('increment', { type: 'bigint' })
id: number;

// UUID
@PrimaryGeneratedColumn('uuid')
id: string;
```

**Nullable columns:**
```typescript
@Column({ nullable: true })
email: string | null;  // TypeScript must reflect nullability
```

**Decimal precision:**
```typescript
@Column({ type: 'decimal', precision: 15, scale: 2 })
saldo: number;
```

### Template Variables Needed

```typescript
{
    "entity_name": "Cliente",
    "table_name": "CLIENTE",
    "columns": [
        {
            "property_name": "nome",
            "column_type": "varchar",
            "ts_type": "string",
            "options": { "length": 100 },
            "nullable": false,
            "unique": false,
            "default": null
        }
    ],
    "primary_key": {
        "property_name": "id",
        "strategy": "increment",
        "type": "bigint"
    },
    "relationships": [
        {
            "property_name": "empresa",
            "type": "ManyToOne",
            "target_entity": "Empresa",
            "inverse_property": "clientes",
            "join_column": "empresa_id",
            "nullable": true
        }
    ],
    "has_created_at": true,
    "has_updated_at": true
}
```

---

## Stack 4: NestJS + Prisma (TypeScript)

### Current Version
- **Prisma 6.x** (stable, Jan 2026)
- **Prisma Client** auto-generated

**Source:** [Prisma Schema Overview](https://www.prisma.io/docs/orm/prisma-schema/overview), [NestJS Prisma Guide](https://docs.nestjs.com/recipes/prisma)

### Schema Syntax

```prisma
// schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Cliente {
  id              BigInt    @id @default(autoincrement())
  nome            String    @db.VarChar(100)
  email           String?   @unique @db.VarChar(254)
  cpf             String    @unique @db.VarChar(14)
  dataNascimento  DateTime? @db.Date
  saldo           Decimal   @default(0) @db.Decimal(15, 2)
  ativo           Boolean   @default(true)
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  empresaId       BigInt?
  empresa         Empresa?  @relation(fields: [empresaId], references: [id])

  @@map("CLIENTE")
}

model Empresa {
  id       BigInt    @id @default(autoincrement())
  nome     String    @db.VarChar(100)
  clientes Cliente[]

  @@map("EMPRESA")
}
```

### Type Mapping: HyperFile to Prisma

| HyperFile Type | Code | Prisma Type | Native Type Attribute |
|----------------|------|-------------|----------------------|
| Binary | 1 | `Bytes` | `@db.ByteA` |
| Text/String | 2, 3 | `String` | `@db.VarChar(n)` |
| Integer (4 bytes) | 4 | `Int` | |
| Integer (2 bytes) | 5 | `Int` | `@db.SmallInt` |
| Integer (1 byte) | 6 | `Int` | `@db.SmallInt` |
| Integer (8 bytes) | 7 | `BigInt` | |
| Real (4 bytes) | 8 | `Float` | `@db.Real` |
| Real (8 bytes) | 9 | `Float` | `@db.DoublePrecision` |
| DateTime | 10 | `DateTime` | |
| Date | 11 | `DateTime` | `@db.Date` |
| Time | 12 | `DateTime` | `@db.Time` |
| Boolean | 13 | `Boolean` | |
| Currency | 14 | `Decimal` | `@db.Decimal(15, 2)` |
| Memo (text) | 15, 16, 18 | `String` | `@db.Text` |
| Memo (binary) | 17 | `Bytes` | |
| Duration | 19 | `Int` | |
| Character | 20 | `String` | `@db.Char(1)` |
| Unicode string | 21 | `String` | `@db.VarChar(n)` |
| Unicode memo | 22 | `String` | `@db.Text` |
| JSON | 23 | `Json` | |
| Auto-increment | 24 | `Int` | `@default(autoincrement())` |
| Auto-increment (8) | 25 | `BigInt` | `@default(autoincrement())` |
| UUID | 26 | `String` | `@db.Uuid` + `@default(uuid())` |
| Password | 27, 28 | `String` | `@db.VarChar(128)` |

### Prisma-Specific Patterns

**Nullability:** Use `?` suffix for nullable fields.

**Mapping to existing tables:** Use `@@map("TABLE_NAME")` at model level and `@map("column_name")` at field level.

**Timestamps:**
```prisma
createdAt DateTime @default(now())
updatedAt DateTime @updatedAt
```

**Relations always need both sides:**
```prisma
// On Cliente (many side)
empresaId BigInt?
empresa   Empresa? @relation(fields: [empresaId], references: [id])

// On Empresa (one side)
clientes Cliente[]
```

### Template Variables Needed

```python
{
    "model_name": "Cliente",
    "table_name": "CLIENTE",  # For @@map
    "fields": [
        {
            "name": "nome",
            "prisma_type": "String",
            "native_type": "@db.VarChar(100)",
            "nullable": False,
            "unique": False,
            "default": None,
            "attributes": []
        }
    ],
    "primary_key": {
        "name": "id",
        "type": "BigInt",
        "default": "@default(autoincrement())"
    },
    "relations": [
        {
            "name": "empresa",
            "target_model": "Empresa",
            "foreign_key": "empresaId",
            "nullable": True
        }
    ],
    "has_updated_at": True
}
```

---

## Stack 5: Rails ActiveRecord (Ruby)

### Current Version
- **Rails 8.1** (stable, Jan 2026)
- **Ruby 3.4**
- **ActiveRecord 8.1.1**

**Source:** [ActiveRecord Basics](https://guides.rubyonrails.org/active_record_basics.html), [Migrations](https://guides.rubyonrails.org/active_record_migrations.html)

### Model Syntax

```ruby
# app/models/cliente.rb

class Cliente < ApplicationRecord
  # Table configuration
  self.table_name = 'CLIENTE'

  # Associations
  belongs_to :empresa, optional: true

  # Validations
  validates :nome, presence: true, length: { maximum: 100 }
  validates :email, uniqueness: true, allow_nil: true
  validates :cpf, presence: true, uniqueness: true, length: { is: 14 }
  validates :saldo, numericality: { greater_than_or_equal_to: 0 }

  # Callbacks (optional, for special cases)
  # before_save :normalize_cpf
end
```

### Migration Syntax (Generated Separately)

```ruby
# db/migrate/YYYYMMDDHHMMSS_create_clientes.rb

class CreateClientes < ActiveRecord::Migration[8.1]
  def change
    create_table :CLIENTE do |t|
      t.string :nome, limit: 100, null: false
      t.string :email, limit: 254
      t.string :cpf, limit: 14, null: false
      t.date :data_nascimento
      t.decimal :saldo, precision: 15, scale: 2, default: 0
      t.boolean :ativo, default: true
      t.references :empresa, foreign_key: true

      t.timestamps
    end

    add_index :CLIENTE, :email, unique: true
    add_index :CLIENTE, :cpf, unique: true
  end
end
```

### Type Mapping: HyperFile to ActiveRecord

| HyperFile Type | Code | Migration Type | Ruby Type | Options |
|----------------|------|----------------|-----------|---------|
| Binary | 1 | `binary` | `String` | |
| Text/String | 2, 3 | `string` | `String` | `limit: n` |
| Integer (4 bytes) | 4 | `integer` | `Integer` | |
| Integer (2 bytes) | 5 | `integer` | `Integer` | `limit: 2` |
| Integer (1 byte) | 6 | `integer` | `Integer` | `limit: 1` |
| Integer (8 bytes) | 7 | `bigint` | `Integer` | |
| Real (4 bytes) | 8 | `float` | `Float` | |
| Real (8 bytes) | 9 | `float` | `Float` | `limit: 53` |
| DateTime | 10 | `datetime` | `DateTime` | |
| Date | 11 | `date` | `Date` | |
| Time | 12 | `time` | `Time` | |
| Boolean | 13 | `boolean` | `TrueClass/FalseClass` | |
| Currency | 14 | `decimal` | `BigDecimal` | `precision: 15, scale: 2` |
| Memo (text) | 15, 16, 18 | `text` | `String` | |
| Memo (binary) | 17 | `binary` | `String` | `limit: 16.megabytes` |
| Duration | 19 | `integer` | `Integer` | (store as seconds) |
| Character | 20 | `string` | `String` | `limit: 1` |
| Unicode string | 21 | `string` | `String` | `limit: n` |
| Unicode memo | 22 | `text` | `String` | |
| JSON | 23 | `json` / `jsonb` | `Hash/Array` | |
| Auto-increment | 24 | (automatic) | `Integer` | (Rails handles PK) |
| Auto-increment (8) | 25 | (automatic) | `Integer` | `id: :bigint` |
| UUID | 26 | `uuid` | `String` | (PostgreSQL native) |
| Password | 27, 28 | `string` | `String` | `limit: 128` |

### Rails-Specific Patterns

**Naming conventions:** Rails prefers snake_case table names and model names. Override with `self.table_name`.

**Timestamps:** Rails expects `created_at` and `updated_at`. Use `t.timestamps` in migrations.

**Foreign keys:** Use `t.references :model_name, foreign_key: true` for automatic FK setup.

**Validations:** Generate basic validations from schema constraints (presence, uniqueness, length).

### Template Variables Needed

```ruby
{
    "class_name": "Cliente",
    "table_name": "CLIENTE",
    "associations": [
        {
            "type": "belongs_to",
            "name": "empresa",
            "options": { "optional": true }
        }
    ],
    "validations": [
        {
            "field": "nome",
            "rules": ["presence: true", "length: { maximum: 100 }"]
        },
        {
            "field": "cpf",
            "rules": ["presence: true", "uniqueness: true"]
        }
    ]
}
```

---

## Code Generation Strategy

### Recommended: Jinja2 Templates

Continue using Jinja2 templates (existing pattern). Each stack gets its own template subdirectory.

**Why Jinja2:**
1. Already integrated in wxcode (BaseGenerator)
2. Handles Python, PHP, TypeScript, Ruby, and Prisma syntax
3. Clean separation of concerns (logic in generator, format in template)
4. Easy to maintain and extend

**Why NOT string concatenation:**
- Hard to read and maintain
- Error-prone for complex structures
- No syntax highlighting

**Why NOT AST manipulation:**
- Overkill for model generation
- Different AST libraries per language
- Templates are simpler for declarative code

### Generator Class Hierarchy

```python
class BaseSchemaGenerator(BaseGenerator):
    """Base for all schema generators."""

    # Subclasses override
    TYPE_MAP: dict[int, str]  # HyperFile code -> target type
    template_subdir: str

    async def generate(self) -> list[Path]:
        # Common logic: fetch schema, iterate tables
        pass

    def _get_target_type(self, column: SchemaColumn) -> str:
        # Use TYPE_MAP
        pass

    def _build_field_context(self, column: SchemaColumn) -> dict:
        # Stack-specific, override in subclasses
        pass

class DjangoSchemaGenerator(BaseSchemaGenerator):
    TYPE_MAP = DJANGO_TYPE_MAP
    template_subdir = "django"

    def _build_field_context(self, column):
        # Django-specific field options
        pass

class EloquentSchemaGenerator(BaseSchemaGenerator):
    TYPE_MAP = ELOQUENT_TYPE_MAP
    template_subdir = "php"
    # ...

# ... similar for TypeORM, Prisma, ActiveRecord
```

---

## What NOT to Do

### 1. Do NOT use external code generators

| Tool | Why NOT |
|------|---------|
| `django-code-generator` | Inactive maintenance, adds dependency |
| `django-builder` | Web-based, not programmatic |
| AI generators (Workik, etc.) | Non-deterministic, not version-controlled |

**Instead:** Use Jinja2 templates for full control.

### 2. Do NOT generate migrations for Django/Rails

| Why NOT |
|---------|
| Migrations are runtime artifacts, not source code |
| Schema may already exist in target database |
| Users should run `makemigrations`/`rails db:migrate` |

**Instead:** Generate models only. Document that users run migration commands.

### 3. Do NOT use runtime type inference

| Pattern | Why NOT |
|---------|---------|
| Python `type()` for dynamic models | Not serializable to files |
| PHP `eval()` for Eloquent | Security risk |

**Instead:** Generate static source files.

### 4. Do NOT hardcode database dialects

| Why NOT |
|---------|
| TypeORM/Prisma support multiple databases |
| Column types vary by database |

**Instead:** Use database-agnostic types where possible, or make database a configuration option.

---

## Type Mapping Summary Table

Master reference for WinDev HyperFile to all ORMs:

| HyperFile | Code | Pydantic | Django | Eloquent | TypeORM | Prisma | ActiveRecord |
|-----------|------|----------|--------|----------|---------|--------|--------------|
| Binary | 1 | `bytes` | `BinaryField` | `binary` | `bytea` | `Bytes` | `binary` |
| String | 2 | `str` | `CharField` | `string` | `varchar` | `String` | `string` |
| Integer | 4 | `int` | `IntegerField` | `integer` | `int` | `Int` | `integer` |
| BigInt | 7 | `int` | `BigIntegerField` | `bigInteger` | `bigint` | `BigInt` | `bigint` |
| Float | 8 | `float` | `FloatField` | `float` | `float` | `Float` | `float` |
| Decimal | 14 | `Decimal` | `DecimalField` | `decimal` | `decimal` | `Decimal` | `decimal` |
| DateTime | 10 | `datetime` | `DateTimeField` | `datetime` | `timestamp` | `DateTime` | `datetime` |
| Date | 11 | `date` | `DateField` | `date` | `date` | `DateTime` | `date` |
| Boolean | 13 | `bool` | `BooleanField` | `boolean` | `boolean` | `Boolean` | `boolean` |
| Text | 15 | `str` | `TextField` | `text` | `text` | `String` | `text` |
| JSON | 23 | `dict` | `JSONField` | `json` | `json` | `Json` | `json` |
| UUID | 26 | `UUID` | `UUIDField` | `uuid` | `uuid` | `String` | `uuid` |
| Auto | 24 | `int` | `AutoField` | `increments` | `int` | `Int` | (auto) |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Django field types | HIGH | Verified with official Django 5.2 docs |
| Laravel Eloquent syntax | HIGH | Verified with Laravel 12.x docs |
| TypeORM decorators | HIGH | Verified with TypeORM official docs |
| Prisma schema syntax | HIGH | Verified with Prisma official docs |
| Rails ActiveRecord | HIGH | Verified with Rails 8.1 guides |
| Type mappings | MEDIUM | Some edge cases may need runtime testing |
| Template approach | HIGH | Consistent with existing wxcode architecture |

---

## Sources

### HIGH Confidence (Official Documentation)
- [Django Model Field Reference (5.2)](https://docs.djangoproject.com/en/5.2/ref/models/fields/)
- [Laravel Eloquent (12.x)](https://laravel.com/docs/12.x/eloquent)
- [Laravel Eloquent Mutators & Casting](https://laravel.com/docs/12.x/eloquent-mutators)
- [NestJS Database Techniques](https://docs.nestjs.com/techniques/database)
- [TypeORM Entities](https://typeorm.io/docs/entity/entities/)
- [Prisma Schema Overview](https://www.prisma.io/docs/orm/prisma-schema/overview)
- [NestJS + Prisma Guide](https://www.prisma.io/docs/guides/nestjs)
- [Rails ActiveRecord Basics](https://guides.rubyonrails.org/active_record_basics.html)
- [Rails Migrations](https://guides.rubyonrails.org/active_record_migrations.html)

### MEDIUM Confidence (Community/Tutorial)
- [GeeksforGeeks Django Models](https://www.geeksforgeeks.org/python/django-models/)
- [Rails Migration Data Types - Beekeeper Studio](https://www.beekeeperstudio.io/blog/rails-migration-data-types)

---

## Implementation Checklist

- [ ] Create `BaseSchemaGenerator` with common type mapping logic
- [ ] Create `DjangoSchemaGenerator` with Django-specific TYPE_MAP
- [ ] Create `EloquentSchemaGenerator` for Laravel
- [ ] Create `TypeORMSchemaGenerator` for NestJS+TypeORM
- [ ] Create `PrismaSchemaGenerator` for NestJS+Prisma
- [ ] Create `ActiveRecordSchemaGenerator` for Rails
- [ ] Create Jinja2 templates for each stack
- [ ] Add stack selection to CLI (`--stack django|laravel|nestjs-typeorm|nestjs-prisma|rails`)
- [ ] Update orchestrator to select correct generator based on target stack
