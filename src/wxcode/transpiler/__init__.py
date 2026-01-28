"""
Módulo de transpilação WLanguage → Python.

Contém catálogos e helpers para conversão de código.
"""

from wxcode.transpiler.hyperfile_catalog import (
    BufferBehavior,
    HFunctionInfo,
    HFUNCTION_CATALOG,
    get_hfunction,
    get_functions_by_behavior,
    is_buffer_modifying,
    needs_llm_conversion,
    get_mongodb_equivalent,
)

__all__ = [
    "BufferBehavior",
    "HFunctionInfo",
    "HFUNCTION_CATALOG",
    "get_hfunction",
    "get_functions_by_behavior",
    "is_buffer_modifying",
    "needs_llm_conversion",
    "get_mongodb_equivalent",
]
