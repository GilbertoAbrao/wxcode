---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/config.py
type: config
updated: 2026-01-21
status: active
---

# config.py

## Purpose

Centralizes all application configuration using pydantic-settings. Provides typed settings for MongoDB connection, Anthropic API credentials, Neo4j database, and general application parameters like debug mode and API host/port. Uses singleton pattern with lru_cache for efficient settings access.

## Exports

- `Settings` - Pydantic BaseSettings class with all configuration fields
- `get_settings() -> Settings` - Cached singleton getter for application settings

## Dependencies

- pydantic-settings - Settings management with environment variable support
- functools - lru_cache for singleton pattern

## Used By

TBD
