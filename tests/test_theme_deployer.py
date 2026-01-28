"""Tests for ThemeDeployer.

Tests the theme asset deployment functionality for copying CSS, JS, fonts, and images
to generated project static directories.
"""

import tempfile
from pathlib import Path

import pytest

from wxcode.generator.theme_deployer import (
    ThemeAssetStats,
    DeployResult,
    get_theme_path,
    list_themes,
    get_theme_asset_stats,
    deploy_theme_assets,
    ASSET_DIRS,
)


class TestThemeAssetStats:
    """Tests for ThemeAssetStats dataclass."""

    def test_total_property(self):
        """Test total calculates sum of all asset counts."""
        stats = ThemeAssetStats(css_count=5, js_count=10, fonts_count=20, images_count=3)
        assert stats.total == 38

    def test_total_with_zeros(self):
        """Test total with zero counts."""
        stats = ThemeAssetStats()
        assert stats.total == 0

    def test_to_dict(self):
        """Test to_dict conversion."""
        stats = ThemeAssetStats(css_count=2, js_count=3, fonts_count=4, images_count=1)
        result = stats.to_dict()
        assert result == {
            "css": 2,
            "js": 3,
            "fonts": 4,
            "images": 1,
            "total": 10,
        }


class TestDeployResult:
    """Tests for DeployResult dataclass."""

    def test_success_when_files_copied_and_no_errors(self):
        """Test success is True when files copied and no errors."""
        result = DeployResult(
            theme="test",
            output_dir=Path("/tmp"),
            files_copied=["file1.css", "file2.js"],
            errors=[],
        )
        assert result.success is True

    def test_failure_when_errors(self):
        """Test success is False when errors exist."""
        result = DeployResult(
            theme="test",
            output_dir=Path("/tmp"),
            files_copied=["file1.css"],
            errors=["Error copying file"],
        )
        assert result.success is False

    def test_failure_when_no_files_copied(self):
        """Test success is False when no files were copied."""
        result = DeployResult(
            theme="test",
            output_dir=Path("/tmp"),
            files_copied=[],
            errors=[],
        )
        assert result.success is False


class TestGetThemePath:
    """Tests for get_theme_path function."""

    @pytest.fixture
    def themes_dir(self):
        """Create a temporary themes directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            themes_path = Path(tmpdir) / "themes"
            themes_path.mkdir()

            # Create dashlite-v3.3.0 theme
            dashlite = themes_path / "dashlite-v3.3.0"
            dashlite.mkdir()
            (dashlite / "css").mkdir()
            (dashlite / "js").mkdir()

            # Create exact-name theme
            exact = themes_path / "exact-name"
            exact.mkdir()

            yield themes_path

    def test_exact_match(self, themes_dir):
        """Test finding theme by exact name."""
        path = get_theme_path("exact-name", themes_dir=themes_dir)
        assert path is not None
        assert path.name == "exact-name"

    def test_prefix_match(self, themes_dir):
        """Test finding theme by prefix (e.g., 'dashlite' finds 'dashlite-v3.3.0')."""
        path = get_theme_path("dashlite", themes_dir=themes_dir)
        assert path is not None
        assert path.name == "dashlite-v3.3.0"

    def test_version_match(self, themes_dir):
        """Test finding theme by full versioned name."""
        path = get_theme_path("dashlite-v3.3.0", themes_dir=themes_dir)
        assert path is not None
        assert path.name == "dashlite-v3.3.0"

    def test_not_found(self, themes_dir):
        """Test returns None for non-existent theme."""
        path = get_theme_path("nonexistent", themes_dir=themes_dir)
        assert path is None


class TestListThemes:
    """Tests for list_themes function."""

    @pytest.fixture
    def themes_dir(self):
        """Create a temporary themes directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            themes_path = Path(tmpdir) / "themes"
            themes_path.mkdir()

            # Create some themes
            (themes_path / "alpha-theme").mkdir()
            (themes_path / "beta-theme").mkdir()
            (themes_path / "gamma-v1.0").mkdir()

            # Hidden and underscore dirs should be ignored
            (themes_path / ".hidden").mkdir()
            (themes_path / "_internal").mkdir()

            yield themes_path

    def test_list_themes_sorted(self, themes_dir):
        """Test list_themes returns sorted list."""
        themes = list_themes(themes_dir=themes_dir)
        assert themes == ["alpha-theme", "beta-theme", "gamma-v1.0"]

    def test_excludes_hidden_and_underscore(self, themes_dir):
        """Test hidden and underscore-prefixed dirs are excluded."""
        themes = list_themes(themes_dir=themes_dir)
        assert ".hidden" not in themes
        assert "_internal" not in themes

    def test_empty_when_no_themes(self):
        """Test returns empty list when no themes exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            themes_path = Path(tmpdir) / "themes"
            themes_path.mkdir()
            themes = list_themes(themes_dir=themes_path)
            assert themes == []


class TestGetThemeAssetStats:
    """Tests for get_theme_asset_stats function."""

    @pytest.fixture
    def theme_with_assets(self):
        """Create a theme directory with various assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            theme_path = Path(tmpdir) / "test-theme"
            theme_path.mkdir()

            # Create CSS files
            css_dir = theme_path / "css"
            css_dir.mkdir()
            (css_dir / "main.css").write_text("/* main */")
            (css_dir / "theme.css").write_text("/* theme */")
            # Nested CSS
            (css_dir / "libs").mkdir()
            (css_dir / "libs" / "vendor.css").write_text("/* vendor */")

            # Create JS files
            js_dir = theme_path / "js"
            js_dir.mkdir()
            (js_dir / "bundle.js").write_text("// bundle")

            # Create font files
            fonts_dir = theme_path / "fonts"
            fonts_dir.mkdir()
            (fonts_dir / "font.woff").write_text("font")
            (fonts_dir / "font.woff2").write_text("font2")

            # Create image files
            images_dir = theme_path / "images"
            images_dir.mkdir()
            (images_dir / "logo.png").write_text("logo")

            yield theme_path

    def test_counts_all_asset_types(self, theme_with_assets):
        """Test counts all types of assets correctly."""
        stats = get_theme_asset_stats(theme_with_assets)
        assert stats.css_count == 3  # main.css, theme.css, libs/vendor.css
        assert stats.js_count == 1
        assert stats.fonts_count == 2
        assert stats.images_count == 1
        assert stats.total == 7

    def test_handles_missing_directories(self):
        """Test handles themes with missing asset directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            theme_path = Path(tmpdir) / "empty-theme"
            theme_path.mkdir()

            stats = get_theme_asset_stats(theme_path)
            assert stats.total == 0


class TestDeployThemeAssets:
    """Tests for deploy_theme_assets function."""

    @pytest.fixture
    def theme_dir(self):
        """Create a theme directory with assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            themes_path = Path(tmpdir) / "themes"
            themes_path.mkdir()

            # Create theme with assets
            theme = themes_path / "test-theme"
            theme.mkdir()

            # CSS
            css_dir = theme / "css"
            css_dir.mkdir()
            (css_dir / "main.css").write_text(".main { color: red; }")
            (css_dir / "skins").mkdir()
            (css_dir / "skins" / "dark.css").write_text(".dark { color: black; }")

            # JS
            js_dir = theme / "js"
            js_dir.mkdir()
            (js_dir / "app.js").write_text("console.log('app');")

            # Fonts
            fonts_dir = theme / "fonts"
            fonts_dir.mkdir()
            (fonts_dir / "icon.woff").write_text("font-data")

            # Images
            images_dir = theme / "images"
            images_dir.mkdir()
            (images_dir / "logo.png").write_text("png-data")

            yield themes_path

    @pytest.fixture
    def output_dir(self):
        """Create an output directory with static folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "project"
            output.mkdir()
            (output / "app" / "static").mkdir(parents=True)
            yield output

    def test_deploy_copies_all_assets(self, theme_dir, output_dir):
        """Test deploy copies all asset types."""
        result = deploy_theme_assets(
            theme="test-theme",
            output_dir=output_dir,
            themes_dir=theme_dir,
        )

        assert result.success is True
        assert result.stats.css_count == 2
        assert result.stats.js_count == 1
        assert result.stats.fonts_count == 1
        assert result.stats.images_count == 1

        # Verify files exist
        static = output_dir / "app" / "static"
        assert (static / "css" / "main.css").exists()
        assert (static / "css" / "skins" / "dark.css").exists()
        assert (static / "js" / "app.js").exists()
        assert (static / "fonts" / "icon.woff").exists()
        assert (static / "images" / "logo.png").exists()

    def test_deploy_preserves_subdirectory_structure(self, theme_dir, output_dir):
        """Test deploy preserves nested directory structure."""
        result = deploy_theme_assets(
            theme="test-theme",
            output_dir=output_dir,
            themes_dir=theme_dir,
        )

        # Check nested CSS file
        nested_css = output_dir / "app" / "static" / "css" / "skins" / "dark.css"
        assert nested_css.exists()
        assert nested_css.read_text() == ".dark { color: black; }"

    def test_deploy_fails_for_missing_theme(self, output_dir):
        """Test deploy fails for non-existent theme."""
        with tempfile.TemporaryDirectory() as tmpdir:
            themes_path = Path(tmpdir) / "themes"
            themes_path.mkdir()

            result = deploy_theme_assets(
                theme="nonexistent",
                output_dir=output_dir,
                themes_dir=themes_path,
            )

            assert result.success is False
            assert len(result.errors) > 0
            assert "não encontrado" in result.errors[0]

    def test_deploy_fails_for_missing_static_dir(self, theme_dir):
        """Test deploy fails when static directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "project"
            output.mkdir()
            # Don't create app/static

            result = deploy_theme_assets(
                theme="test-theme",
                output_dir=output,
                themes_dir=theme_dir,
            )

            assert result.success is False
            assert "static não existe" in result.errors[0]

    def test_deploy_overwrites_existing_files(self, theme_dir, output_dir):
        """Test deploy overwrites existing files by default."""
        static = output_dir / "app" / "static"

        # Create existing file
        (static / "css").mkdir()
        (static / "css" / "main.css").write_text("/* old content */")

        result = deploy_theme_assets(
            theme="test-theme",
            output_dir=output_dir,
            themes_dir=theme_dir,
            overwrite=True,
        )

        assert result.success is True
        # File should have new content
        assert (static / "css" / "main.css").read_text() == ".main { color: red; }"

    def test_deploy_skips_existing_when_no_overwrite(self, theme_dir, output_dir):
        """Test deploy skips existing files when overwrite=False."""
        static = output_dir / "app" / "static"

        # Create existing file
        (static / "css").mkdir()
        (static / "css" / "main.css").write_text("/* old content */")

        result = deploy_theme_assets(
            theme="test-theme",
            output_dir=output_dir,
            themes_dir=theme_dir,
            overwrite=False,
        )

        # Should still succeed but skip the existing file
        assert result.success is True
        # main.css was skipped, but dark.css was copied (1 CSS)
        assert result.stats.css_count == 1
        # Old content should be preserved
        assert (static / "css" / "main.css").read_text() == "/* old content */"

    def test_deploy_returns_file_list(self, theme_dir, output_dir):
        """Test deploy returns list of copied files."""
        result = deploy_theme_assets(
            theme="test-theme",
            output_dir=output_dir,
            themes_dir=theme_dir,
        )

        assert "main.css" in result.files_copied
        assert "skins/dark.css" in result.files_copied
        assert "app.js" in result.files_copied


class TestDeployWithRealTheme:
    """Integration tests using the actual DashLite theme if available."""

    @pytest.fixture
    def project_root(self):
        """Get the actual project root."""
        return Path(__file__).parent.parent

    def test_real_theme_can_be_found(self, project_root):
        """Test that real themes can be discovered."""
        themes = list_themes()
        # Should have at least dashlite
        if themes:
            assert any("dashlite" in t.lower() for t in themes)

    def test_real_theme_has_assets(self, project_root):
        """Test that real theme has expected assets."""
        theme_path = get_theme_path("dashlite")
        if theme_path is None:
            pytest.skip("DashLite theme not installed")

        stats = get_theme_asset_stats(theme_path)
        # DashLite should have substantial assets
        assert stats.css_count > 0
        assert stats.js_count > 0
        assert stats.fonts_count > 0
