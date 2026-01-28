"""
Stack configuration service.

Loads stack YAML files from data/stacks/ and provides query methods.
Stacks are seeded to MongoDB on application startup for runtime querying.
"""

import logging
from pathlib import Path
from typing import Optional

import yaml

from wxcode.models import Stack

logger = logging.getLogger(__name__)

# Path to stack configuration files
STACKS_DATA_DIR = Path(__file__).parent.parent / "data" / "stacks"


async def seed_stacks(force: bool = False) -> int:
    """
    Seed all stack configurations from YAML files to MongoDB.

    Uses upsert pattern: updates existing stacks, creates new ones.
    Called on application startup to ensure MongoDB has latest configs.

    Args:
        force: If True, always update even if stack exists unchanged

    Returns:
        Number of stacks seeded
    """
    if not STACKS_DATA_DIR.exists():
        logger.warning(f"Stacks data directory not found: {STACKS_DATA_DIR}")
        return 0

    count = 0
    for yaml_file in STACKS_DATA_DIR.rglob("*.yaml"):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "stack_id" not in data:
                logger.warning(f"Invalid stack file (missing stack_id): {yaml_file}")
                continue

            stack_id = data["stack_id"]
            existing = await Stack.find_one(Stack.stack_id == stack_id)

            if existing:
                # Update existing stack
                for key, value in data.items():
                    setattr(existing, key, value)
                await existing.save()
                logger.debug(f"Updated stack: {stack_id}")
            else:
                # Create new stack
                stack = Stack(**data)
                await stack.insert()
                logger.debug(f"Created stack: {stack_id}")

            count += 1

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {yaml_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading stack {yaml_file}: {e}")

    logger.info(f"Seeded {count} stacks from {STACKS_DATA_DIR}")
    return count


async def get_stack_by_id(stack_id: str) -> Optional[Stack]:
    """
    Get a stack by its unique identifier.

    Args:
        stack_id: Unique stack identifier (e.g., "fastapi-htmx")

    Returns:
        Stack document if found, None otherwise
    """
    return await Stack.find_one(Stack.stack_id == stack_id)


async def list_stacks(
    group: Optional[str] = None,
    language: Optional[str] = None,
) -> list[Stack]:
    """
    List stacks with optional filtering.

    Args:
        group: Filter by group ("server-rendered", "spa", "fullstack")
        language: Filter by primary language ("python", "typescript", etc.)

    Returns:
        List of matching Stack documents
    """
    query = {}
    if group:
        query["group"] = group
    if language:
        query["language"] = language

    if query:
        return await Stack.find(query).to_list()
    return await Stack.find_all().to_list()


async def get_stacks_grouped() -> dict[str, list[Stack]]:
    """
    Get all stacks organized by their group.

    Returns:
        Dict with keys: "server-rendered", "spa", "fullstack"
        Each value is a list of Stack documents in that group.
    """
    all_stacks = await Stack.find_all().to_list()

    grouped: dict[str, list[Stack]] = {
        "server-rendered": [],
        "spa": [],
        "fullstack": [],
    }

    for stack in all_stacks:
        if stack.group in grouped:
            grouped[stack.group].append(stack)

    return grouped
