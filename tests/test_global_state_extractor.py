"""Tests for GlobalStateExtractor."""

import pytest

from wxcode.parser.global_state_extractor import (
    GlobalStateExtractor,
    GlobalVariable,
    InitializationBlock,
    Scope,
)


def test_extract_simple_declaration():
    """Test extraction of simple GLOBAL declaration."""
    extractor = GlobalStateExtractor()
    code = """
GLOBAL
    gCnn is Connection
    gsUrlAPI is string
"""
    variables = extractor.extract_variables(code, 0, "Project.wwp")

    assert len(variables) == 2

    assert variables[0].name == "gCnn"
    assert variables[0].wlanguage_type == "Connection"
    assert variables[0].default_value is None
    assert variables[0].scope == Scope.APP
    assert variables[0].source_element == "Project.wwp"

    assert variables[1].name == "gsUrlAPI"
    assert variables[1].wlanguage_type == "string"


def test_extract_declaration_with_default():
    """Test extraction of declaration with default value."""
    extractor = GlobalStateExtractor()
    code = """
GLOBAL
    gnTimeout is int = 20
    gbDebug is boolean = True
"""
    variables = extractor.extract_variables(code, 0, "Project.wwp")

    assert len(variables) == 2

    assert variables[0].name == "gnTimeout"
    assert variables[0].wlanguage_type == "int"
    assert variables[0].default_value == "20"

    assert variables[1].name == "gbDebug"
    assert variables[1].wlanguage_type == "boolean"
    assert variables[1].default_value == "True"


def test_extract_multi_declaration():
    """Test extraction of multiple variables in one line."""
    extractor = GlobalStateExtractor()
    code = """
GLOBAL
    a, b, c are string
"""
    variables = extractor.extract_variables(code, 0, "Project.wwp")

    assert len(variables) == 3
    assert variables[0].name == "a"
    assert variables[1].name == "b"
    assert variables[2].name == "c"
    assert all(v.wlanguage_type == "string" for v in variables)


def test_wlanguage_types_preserved():
    """Test that WLanguage types are preserved (not mapped to Python)."""
    extractor = GlobalStateExtractor()
    code = """
GLOBAL
    gCnn is Connection
    gjsonParams is JSON
    gArray is array of string
"""
    variables = extractor.extract_variables(code, 0, "Project.wwp")

    # Verify types are WLanguage original, NOT Python types
    assert variables[0].wlanguage_type == "Connection"  # NOT AsyncEngine
    assert variables[1].wlanguage_type == "JSON"  # NOT dict[str, Any]
    assert variables[2].wlanguage_type == "array of string"  # NOT list[str]


def test_scope_determination():
    """Test correct scope assignment based on type_code."""
    extractor = GlobalStateExtractor()
    code = """
GLOBAL
    gVar is string
"""

    # Project Code → APP
    var_app = extractor.extract_variables(code, 0, "Project.wwp")
    assert var_app[0].scope == Scope.APP

    # WDG → MODULE
    var_module = extractor.extract_variables(code, 31, "ServerProcs.wdg")
    assert var_module[0].scope == Scope.MODULE

    # Page → REQUEST
    var_request = extractor.extract_variables(code, 38, "PAGE_Login.wwh")
    assert var_request[0].scope == Scope.REQUEST


def test_extract_initialization():
    """Test extraction of initialization blocks."""
    extractor = GlobalStateExtractor()
    code = """
GLOBAL
    gCnn is Connection

IF HOpenConnection(gCnn) = False THEN
    EndProgram("Erro")
END
"""
    blocks = extractor.extract_initialization(code)

    assert len(blocks) == 1
    assert "gCnn" in blocks[0].dependencies
    assert "HOpenConnection" in blocks[0].code
    assert blocks[0].order == 0


def test_no_global_block():
    """Test handling of code without GLOBAL block."""
    extractor = GlobalStateExtractor()
    code = """
PROCEDURE MyProc()
    LOCAL nVar is int
END
"""
    variables = extractor.extract_variables(code, 0, "Project.wwp")
    assert len(variables) == 0

    blocks = extractor.extract_initialization(code)
    assert len(blocks) == 0
