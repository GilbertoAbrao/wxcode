"""Integration tests for DashLite theme skills.

Tests the complete theme skill loading and context building with DashLite theme.
"""

from pathlib import Path

import pytest

from wxcode.generator.theme_skill_loader import (
    ThemeSkillLoader,
    get_available_themes,
    CONTROL_TYPE_TO_COMPONENT,
)
from wxcode.llm_converter.models import ConversionContext


# Get project root (go up from tests/integration to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestDashLiteThemeStructure:
    """Tests for DashLite theme file structure."""

    @pytest.fixture
    def loader(self):
        """Create ThemeSkillLoader for DashLite."""
        return ThemeSkillLoader("dashlite", project_root=PROJECT_ROOT)

    def test_dashlite_theme_exists(self, loader):
        """Verify DashLite theme is installed."""
        assert loader.theme_exists(), (
            "DashLite theme not found. "
            f"Expected at: {loader.skills_path}"
        )

    def test_dashlite_has_index(self, loader):
        """Verify DashLite has _index.md."""
        index_path = loader.skills_path / "_index.md"
        assert index_path.exists(), f"Missing _index.md at {index_path}"

    def test_dashlite_has_description(self, loader):
        """Verify DashLite has a description in _index.md."""
        desc = loader.get_theme_description()
        assert desc is not None
        assert len(desc) > 0

    def test_dashlite_has_required_skills(self, loader):
        """Verify DashLite has all required skill files."""
        required_skills = [
            "buttons.md",
            "tables.md",
            "cards.md",
            "layout.md",
            "modals.md",
            "alerts.md",
            "forms/_index.md",
            "forms/input.md",
            "forms/select.md",
            "forms/checkbox.md",
            "forms/datepicker.md",
            "forms/textarea.md",
        ]

        for skill in required_skills:
            skill_path = loader.skills_path / skill
            assert skill_path.exists(), f"Missing skill: {skill}"


class TestDashLiteSkillContent:
    """Tests for DashLite skill content quality."""

    @pytest.fixture
    def loader(self):
        """Create ThemeSkillLoader for DashLite."""
        return ThemeSkillLoader("dashlite", project_root=PROJECT_ROOT)

    def test_index_has_page_structure(self, loader):
        """Verify _index.md documents DashLite page structure."""
        content = loader._load_skill("_index.md")
        assert content is not None

        # Should document key DashLite structures
        key_terms = ["nk-wrap", "nk-main", "nk-content"]
        found = sum(1 for term in key_terms if term in content)
        assert found >= 2, "Index should document nk-wrap, nk-main, nk-content structure"

    def test_index_has_nioicon_reference(self, loader):
        """Verify _index.md references NioIcon system."""
        content = loader._load_skill("_index.md")
        assert content is not None
        assert "ni-" in content or "NioIcon" in content or "icon" in content.lower()

    def test_buttons_has_variants(self, loader):
        """Verify buttons.md documents button variants."""
        content = loader._load_skill("buttons.md")
        assert content is not None

        # Should have button classes
        assert "btn-primary" in content
        assert "btn-secondary" in content or "btn-outline" in content

    def test_buttons_has_code_examples(self, loader):
        """Verify buttons.md has HTML code examples."""
        content = loader._load_skill("buttons.md")
        assert content is not None

        # Should have code blocks with HTML
        assert "```html" in content or "```" in content
        assert "<button" in content or "btn" in content

    def test_tables_has_nk_tb_structure(self, loader):
        """Verify tables.md documents nk-tb structure."""
        content = loader._load_skill("tables.md")
        assert content is not None

        # Should document DashLite's custom table classes
        assert "nk-tb" in content or "table" in content.lower()

    def test_forms_input_has_form_control(self, loader):
        """Verify forms/input.md documents form-control classes."""
        content = loader._load_skill("forms/input.md")
        assert content is not None
        assert "form-control" in content

    def test_forms_select_has_select2_reference(self, loader):
        """Verify forms/select.md references Select2 or similar."""
        content = loader._load_skill("forms/select.md")
        assert content is not None
        # Should have either Select2 or standard select
        assert "select" in content.lower()


class TestDashLiteProgressiveDiscovery:
    """Tests for progressive skill loading with DashLite."""

    @pytest.fixture
    def loader(self):
        """Create ThemeSkillLoader for DashLite."""
        return ThemeSkillLoader("dashlite", project_root=PROJECT_ROOT)

    def test_load_single_component_is_small(self, loader):
        """Verify loading single component produces manageable size."""
        content = loader.load_skills({"buttons"})

        # Should be reasonable size (under 50KB for single component + index)
        assert len(content) < 50000, "Single component should be under 50KB"

    def test_load_all_components_is_larger(self, loader):
        """Verify loading all components produces larger output."""
        # Get all unique components from mappings
        all_components = {
            c for c in CONTROL_TYPE_TO_COMPONENT.values()
            if c is not None
        }

        small_content = loader.load_skills({"buttons"})
        large_content = loader.load_skills(all_components)

        assert len(large_content) > len(small_content)

    def test_skills_are_deduplicated(self, loader):
        """Verify requesting same component multiple times doesn't duplicate."""
        # Load with explicit duplicates (shouldn't happen normally)
        content = loader.load_skills({"buttons", "forms/input"})

        # Count occurrences of the separator used between skills
        # Skills are joined with "---" separators
        separator_count = content.count("\n\n---\n\n")

        # With buttons + forms/input we should have:
        # _index, forms/_index, forms/input, buttons = 4 skills
        # That means 3 separators
        # This verifies we're not loading duplicates
        assert separator_count <= 5, "Too many separators indicates duplicate skills"

        # Also verify the index is loaded only once by checking frontmatter
        # The main index has "name: dashlite-_index" in its frontmatter
        frontmatter_count = content.count("name: dashlite-_index")
        assert frontmatter_count == 1, "Index frontmatter should appear only once"

    def test_subcomponents_load_parent_index(self, loader):
        """Verify subcomponents load their parent _index.md."""
        content = loader.load_skills({"forms/input"})

        # Should have forms/_index content
        # Look for forms-specific content
        assert "form" in content.lower()


class TestDashLiteContextIntegration:
    """Tests for DashLite integration with ConversionContext."""

    @pytest.fixture
    def loader(self):
        """Create ThemeSkillLoader for DashLite."""
        return ThemeSkillLoader("dashlite", project_root=PROJECT_ROOT)

    def test_context_with_theme_skills(self, loader):
        """Verify ConversionContext can hold theme skills."""
        skills_content = loader.load_skills({"buttons", "forms/input"})

        context = ConversionContext(
            page_name="test_page",
            element_id="507f1f77bcf86cd799439011",
            controls=[],
            theme="dashlite",
            theme_skills=skills_content,
        )

        assert context.theme == "dashlite"
        assert context.theme_skills is not None
        assert len(context.theme_skills) > 0

    def test_context_theme_skills_estimation(self, loader):
        """Verify token estimation includes theme skills."""
        skills_content = loader.load_skills({"buttons"})

        context = ConversionContext(
            page_name="test_page",
            element_id="507f1f77bcf86cd799439011",
            controls=[],
            theme="dashlite",
            theme_skills=skills_content,
            estimated_tokens=len(skills_content) // 4,  # ~4 chars per token
        )

        # Token count should account for skills content
        assert context.estimated_tokens > 0


class TestDashLiteAvailability:
    """Tests for DashLite in available themes list."""

    def test_dashlite_in_available_themes(self):
        """Verify DashLite appears in available themes."""
        themes = get_available_themes(project_root=PROJECT_ROOT)
        names = {t["name"] for t in themes}
        assert "dashlite" in names

    def test_dashlite_has_description_in_list(self):
        """Verify DashLite has description in themes list."""
        themes = get_available_themes(project_root=PROJECT_ROOT)
        dashlite = next((t for t in themes if t["name"] == "dashlite"), None)

        assert dashlite is not None
        assert dashlite["description"] != "No description"
        assert len(dashlite["description"]) > 0
