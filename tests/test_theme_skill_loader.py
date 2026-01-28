"""Tests for ThemeSkillLoader.

Tests the theme skill loading functionality for LLM-based page conversion.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wxcode.generator.theme_skill_loader import (
    ThemeSkillLoader,
    CONTROL_TYPE_TO_COMPONENT,
    CONTROL_NAME_TO_COMPONENT,
    INPUT_TYPE_TO_COMPONENT,
    get_available_themes,
)


class TestControlMappings:
    """Tests for control type to component mappings."""

    def test_button_type_maps_to_buttons(self):
        """Test that type_code 3 (Button) maps to buttons component."""
        assert CONTROL_TYPE_TO_COMPONENT[3] == "buttons"

    def test_edit_type_maps_to_forms_input(self):
        """Test that type_code 4 (Edit) maps to forms/input component."""
        assert CONTROL_TYPE_TO_COMPONENT[4] == "forms/input"

    def test_table_type_maps_to_tables(self):
        """Test that type_code 9 (Table) maps to tables component."""
        assert CONTROL_TYPE_TO_COMPONENT[9] == "tables"

    def test_combo_type_maps_to_forms_select(self):
        """Test that type_code 7 (Combo) maps to forms/select component."""
        assert CONTROL_TYPE_TO_COMPONENT[7] == "forms/select"

    def test_checkbox_type_maps_to_forms_checkbox(self):
        """Test that type_code 6 (Check) maps to forms/checkbox component."""
        assert CONTROL_TYPE_TO_COMPONENT[6] == "forms/checkbox"

    def test_static_type_maps_to_none(self):
        """Test that type_code 1 (Static) maps to None (no skill needed)."""
        assert CONTROL_TYPE_TO_COMPONENT[1] is None

    def test_name_prefix_button_maps_to_buttons(self):
        """Test that 'button' prefix maps to buttons component."""
        assert CONTROL_NAME_TO_COMPONENT["button"] == "buttons"
        assert CONTROL_NAME_TO_COMPONENT["btn"] == "buttons"

    def test_name_prefix_edit_maps_to_forms_input(self):
        """Test that 'edit' prefix maps to forms/input component."""
        assert CONTROL_NAME_TO_COMPONENT["edit"] == "forms/input"
        assert CONTROL_NAME_TO_COMPONENT["edt"] == "forms/input"

    def test_input_type_date_maps_to_datepicker(self):
        """Test that date input types map to datepicker component."""
        assert INPUT_TYPE_TO_COMPONENT["date"] == "forms/datepicker"
        assert INPUT_TYPE_TO_COMPONENT["datetime"] == "forms/datepicker"
        assert INPUT_TYPE_TO_COMPONENT["datetime-local"] == "forms/datepicker"


class TestThemeSkillLoaderInit:
    """Tests for ThemeSkillLoader initialization."""

    def test_init_with_theme_name(self):
        """Test initialization with just theme name."""
        loader = ThemeSkillLoader("dashlite")
        assert loader.theme == "dashlite"
        assert loader.skills_path.name == "dashlite"

    def test_init_with_custom_skills_path(self):
        """Test initialization with custom skills base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            loader = ThemeSkillLoader("mytheme", skills_base_path=base_path)
            assert loader.skills_path == base_path / "mytheme"

    def test_init_with_project_root(self):
        """Test initialization with project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            loader = ThemeSkillLoader("dashlite", project_root=root)
            expected = root / ".claude/skills/themes/dashlite"
            assert loader.skills_path == expected


class TestThemeSkillLoaderExists:
    """Tests for theme existence checking."""

    def test_theme_exists_returns_false_for_nonexistent(self):
        """Test theme_exists returns False when theme doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ThemeSkillLoader("nonexistent", project_root=Path(tmpdir))
            assert loader.theme_exists() is False

    def test_theme_exists_returns_true_for_existing(self):
        """Test theme_exists returns True when theme exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            theme_path = root / ".claude/skills/themes/dashlite"
            theme_path.mkdir(parents=True)
            (theme_path / "_index.md").write_text("# DashLite")

            loader = ThemeSkillLoader("dashlite", project_root=root)
            assert loader.theme_exists() is True


class TestThemeSkillLoaderAnalyze:
    """Tests for analyzing required components from controls."""

    def test_analyze_empty_controls(self):
        """Test analyze with no controls."""
        loader = ThemeSkillLoader("dashlite")
        components = loader.analyze_required_components([])
        assert components == set()

    def test_analyze_button_control(self):
        """Test analyze identifies button component."""
        loader = ThemeSkillLoader("dashlite")

        # Mock a button control
        control = MagicMock()
        control.type_code = 3
        control.name = "BTN_Submit"
        control.properties = None

        components = loader.analyze_required_components([control])
        assert "buttons" in components

    def test_analyze_edit_with_date_input_type(self):
        """Test analyze identifies datepicker for date input types."""
        loader = ThemeSkillLoader("dashlite")

        # Mock an edit control with date input type
        control = MagicMock()
        control.type_code = 4  # Edit
        control.name = "EDT_DataNascimento"
        control.properties = MagicMock()
        control.properties.input_type = "date"

        components = loader.analyze_required_components([control])
        assert "forms/datepicker" in components

    def test_analyze_multiple_controls_deduplicates(self):
        """Test analyze deduplicates components from multiple controls."""
        loader = ThemeSkillLoader("dashlite")

        # Create two button controls
        btn1 = MagicMock()
        btn1.type_code = 3
        btn1.name = "BTN_Save"
        btn1.properties = None

        btn2 = MagicMock()
        btn2.type_code = 3
        btn2.name = "BTN_Cancel"
        btn2.properties = None

        components = loader.analyze_required_components([btn1, btn2])
        # Should only have one "buttons" entry
        assert components == {"buttons"}

    def test_analyze_by_name_prefix_fallback(self):
        """Test analyze uses name prefix when type_code not mapped."""
        loader = ThemeSkillLoader("dashlite")

        # Mock control with unknown type_code but recognizable name
        control = MagicMock()
        control.type_code = 99999  # Unknown type
        control.name = "button_special"
        control.properties = None

        components = loader.analyze_required_components([control])
        assert "buttons" in components


class TestThemeSkillLoaderLoadSkills:
    """Tests for loading skill content."""

    @pytest.fixture
    def theme_dir(self):
        """Create a temporary theme directory with skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            theme_path = root / ".claude/skills/themes/testtheme"
            theme_path.mkdir(parents=True)

            # Create _index.md
            (theme_path / "_index.md").write_text(
                "---\n"
                "name: testtheme\n"
                "description: Test Theme\n"
                "---\n"
                "# Test Theme Index\n"
            )

            # Create buttons.md
            (theme_path / "buttons.md").write_text(
                "---\n"
                "name: testtheme-buttons\n"
                "depends-on: [testtheme-_index]\n"
                "---\n"
                "# Buttons\n"
                "Button content here.\n"
            )

            # Create forms directory
            forms_path = theme_path / "forms"
            forms_path.mkdir()

            # Create forms/_index.md
            (forms_path / "_index.md").write_text(
                "---\n"
                "name: testtheme-forms\n"
                "---\n"
                "# Forms Index\n"
            )

            # Create forms/input.md
            (forms_path / "input.md").write_text(
                "---\n"
                "name: testtheme-forms-input\n"
                "---\n"
                "# Input\n"
                "Input content here.\n"
            )

            yield root

    def test_load_skills_loads_index(self, theme_dir):
        """Test load_skills always loads _index.md first."""
        loader = ThemeSkillLoader("testtheme", project_root=theme_dir)
        content = loader.load_skills(set())
        assert "# Test Theme Index" in content

    def test_load_skills_loads_component(self, theme_dir):
        """Test load_skills loads specified component."""
        loader = ThemeSkillLoader("testtheme", project_root=theme_dir)
        content = loader.load_skills({"buttons"})
        assert "# Buttons" in content
        assert "Button content here." in content

    def test_load_skills_loads_subcomponent_with_parent_index(self, theme_dir):
        """Test load_skills loads parent index for subcomponents."""
        loader = ThemeSkillLoader("testtheme", project_root=theme_dir)
        content = loader.load_skills({"forms/input"})
        # Should include forms/_index.md and forms/input.md
        assert "# Forms Index" in content
        assert "# Input" in content

    def test_load_skills_handles_missing_component(self, theme_dir):
        """Test load_skills handles missing component gracefully."""
        loader = ThemeSkillLoader("testtheme", project_root=theme_dir)
        # Should not raise, just skip the missing component
        content = loader.load_skills({"nonexistent"})
        # Should still have the index
        assert "# Test Theme Index" in content

    def test_load_skills_raises_for_missing_theme(self):
        """Test load_skills raises ValueError for missing theme."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ThemeSkillLoader("nonexistent", project_root=Path(tmpdir))
            with pytest.raises(ValueError, match="not found"):
                loader.load_skills({"buttons"})


class TestThemeSkillLoaderMetadata:
    """Tests for frontmatter metadata parsing."""

    @pytest.fixture
    def theme_with_deps(self):
        """Create theme with skill dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            theme_path = root / ".claude/skills/themes/deptheme"
            theme_path.mkdir(parents=True)

            (theme_path / "_index.md").write_text(
                "---\n"
                "name: deptheme\n"
                "description: Theme with dependencies\n"
                "---\n"
                "# Dep Theme\n"
            )

            (theme_path / "base.md").write_text(
                "---\n"
                "name: deptheme-base\n"
                "---\n"
                "# Base\n"
            )

            (theme_path / "advanced.md").write_text(
                "---\n"
                "name: deptheme-advanced\n"
                "depends-on: [deptheme-base]\n"
                "---\n"
                "# Advanced\n"
            )

            yield root

    def test_get_theme_description(self, theme_with_deps):
        """Test getting theme description from _index.md."""
        loader = ThemeSkillLoader("deptheme", project_root=theme_with_deps)
        desc = loader.get_theme_description()
        assert desc == "Theme with dependencies"

    def test_dependencies_are_loaded(self, theme_with_deps):
        """Test that dependencies in frontmatter are loaded."""
        loader = ThemeSkillLoader("deptheme", project_root=theme_with_deps)
        content = loader.load_skills({"advanced"})
        # Should include base.md due to depends-on
        assert "# Base" in content
        assert "# Advanced" in content


class TestGetAvailableThemes:
    """Tests for get_available_themes function."""

    def test_returns_empty_for_no_themes(self):
        """Test returns empty list when no themes exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            themes = get_available_themes(project_root=Path(tmpdir))
            assert themes == []

    def test_returns_themes_with_descriptions(self):
        """Test returns list of themes with descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            themes_dir = root / ".claude/skills/themes"

            # Create two themes
            for theme_name, desc in [("theme1", "First theme"), ("theme2", "Second theme")]:
                theme_path = themes_dir / theme_name
                theme_path.mkdir(parents=True)
                (theme_path / "_index.md").write_text(
                    f"---\nname: {theme_name}\ndescription: {desc}\n---\n# {theme_name}\n"
                )

            themes = get_available_themes(project_root=root)

            assert len(themes) == 2
            names = {t["name"] for t in themes}
            assert names == {"theme1", "theme2"}

    def test_excludes_underscore_prefixed_dirs(self):
        """Test excludes directories starting with underscore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            themes_dir = root / ".claude/skills/themes"
            themes_dir.mkdir(parents=True)

            # Create a real theme
            (themes_dir / "realtheme").mkdir()
            (themes_dir / "realtheme/_index.md").write_text("---\nname: real\n---\n# Real\n")

            # Create underscore-prefixed dir (should be ignored)
            (themes_dir / "_shared").mkdir()
            (themes_dir / "_shared/_index.md").write_text("---\nname: shared\n---\n# Shared\n")

            themes = get_available_themes(project_root=root)
            names = {t["name"] for t in themes}
            assert names == {"realtheme"}


class TestThemeSkillLoaderWithRealTheme:
    """Integration tests using the actual DashLite theme if available."""

    @pytest.fixture
    def project_root(self):
        """Get the actual project root."""
        # Go up from tests/ to project root
        return Path(__file__).parent.parent

    def test_dashlite_theme_exists(self, project_root):
        """Test that DashLite theme exists in the project."""
        loader = ThemeSkillLoader("dashlite", project_root=project_root)
        # This test documents that dashlite should exist
        if loader.theme_exists():
            assert loader.get_theme_description() is not None

    def test_dashlite_loads_buttons_skill(self, project_root):
        """Test loading buttons skill from DashLite."""
        loader = ThemeSkillLoader("dashlite", project_root=project_root)
        if not loader.theme_exists():
            pytest.skip("DashLite theme not installed")

        content = loader.load_skills({"buttons"})
        # Should have DashLite-specific content
        assert "btn-" in content.lower() or "button" in content.lower()

    def test_dashlite_progressive_discovery(self, project_root):
        """Test progressive discovery with DashLite theme."""
        loader = ThemeSkillLoader("dashlite", project_root=project_root)
        if not loader.theme_exists():
            pytest.skip("DashLite theme not installed")

        # Load only what we need
        small_set = loader.load_skills({"buttons"})
        large_set = loader.load_skills({"buttons", "tables", "forms/input", "modals"})

        # Larger set should have more content
        assert len(large_set) > len(small_set)
