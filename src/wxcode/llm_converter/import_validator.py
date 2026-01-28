"""ImportValidator - Validates and fixes imports in generated code."""

import ast
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class ImportValidator:
    """Validates and fixes imports in generated code.

    Scans the output directory for available modules and removes imports
    from modules that don't exist.
    """

    def __init__(self, output_dir: Path):
        """Initialize the validator.

        Args:
            output_dir: Root directory of the generated project
        """
        self.output_dir = Path(output_dir)
        self.available_modules: set[str] = set()
        self._scan_modules()

    def _scan_modules(self) -> None:
        """Scan app/ directory for available Python modules."""
        app_dir = self.output_dir / "app"
        if not app_dir.exists():
            return

        for py_file in app_dir.rglob("*.py"):
            # Convert path to module name
            rel_path = py_file.relative_to(self.output_dir)
            parts = list(rel_path.parts)

            # Remove .py extension
            parts[-1] = parts[-1].replace(".py", "")

            # Skip __init__ for module name, but mark parent as valid
            if parts[-1] == "__init__":
                parts = parts[:-1]
                if parts:
                    module_name = ".".join(parts)
                    self.available_modules.add(module_name)
            else:
                module_name = ".".join(parts)
                self.available_modules.add(module_name)

                # Also add parent package
                if len(parts) > 1:
                    parent = ".".join(parts[:-1])
                    self.available_modules.add(parent)

    def _module_exists(self, module: str) -> bool:
        """Check if a module exists.

        Args:
            module: Module name (e.g., 'app.models.user')

        Returns:
            True if module exists or is not an app.* module
        """
        # Only validate app.* imports
        if not module.startswith("app."):
            return True

        # Check if exact module exists
        # e.g., 'app.core.database' must be in available_modules
        return module in self.available_modules

    def _extract_imports(self, code: str) -> list[tuple[int, str, str]]:
        """Extract import statements from code.

        Args:
            code: Python source code

        Returns:
            List of (line_number, full_line, module_name) tuples
        """
        imports = []
        lines = code.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("#"):
                continue

            # Match "from x import y" or "from x.y import z"
            match = re.match(r"^from\s+([\w.]+)\s+import", stripped)
            if match:
                module = match.group(1)
                imports.append((i, line, module))

        return imports

    def validate_and_fix(self, code: str) -> tuple[str, list[str]]:
        """Validate imports and remove invalid ones.

        Args:
            code: Python source code to validate

        Returns:
            Tuple of (fixed_code, removed_imports)
        """
        # Rescan modules in case new ones were added
        self._scan_modules()

        imports = self._extract_imports(code)
        lines = code.split("\n")
        removed_imports: list[str] = []
        lines_to_remove: set[int] = set()

        for line_num, full_line, module in imports:
            if not self._module_exists(module):
                logger.warning(f"Removing invalid import: {module}")
                removed_imports.append(module)
                lines_to_remove.add(line_num)

        # Remove invalid import lines
        if lines_to_remove:
            new_lines = []
            for i, line in enumerate(lines):
                if i not in lines_to_remove:
                    new_lines.append(line)
            code = "\n".join(new_lines)

        return code, removed_imports

    def get_available_modules(self) -> list[str]:
        """Get list of available modules.

        Returns:
            Sorted list of available module names
        """
        return sorted(self.available_modules)
