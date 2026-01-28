"""
Testes para o catálogo de funções H*.

Testa:
- Catálogo tem funções
- Funções têm informações completas
- Helpers de lookup funcionam
- Comportamentos estão corretos
"""

import pytest

from wxcode.transpiler.hyperfile_catalog import (
    BufferBehavior,
    HFunctionInfo,
    HFUNCTION_CATALOG,
    get_hfunction,
    get_functions_by_behavior,
    is_buffer_modifying,
    needs_llm_conversion,
    get_mongodb_equivalent,
    get_all_function_names,
    get_functions_needing_llm,
)


# ===========================================================================
# Tests: Catálogo
# ===========================================================================

class TestHFunctionCatalog:
    """Testes para o catálogo de funções H*."""

    def test_catalog_not_empty(self):
        """Catálogo deve ter funções."""
        assert len(HFUNCTION_CATALOG) > 0

    def test_catalog_has_minimum_functions(self):
        """Catálogo deve ter pelo menos 35 funções."""
        assert len(HFUNCTION_CATALOG) >= 35

    def test_all_functions_have_name(self):
        """Todas funções devem ter nome."""
        for name, func in HFUNCTION_CATALOG.items():
            assert func.name, f"Função {name} sem nome"
            assert func.name == name, f"Nome inconsistente: {func.name} vs {name}"

    def test_all_functions_have_behavior(self):
        """Todas funções devem ter behavior definido."""
        for name, func in HFUNCTION_CATALOG.items():
            assert func.behavior is not None, f"Função {name} sem behavior"
            assert isinstance(func.behavior, BufferBehavior), \
                f"Função {name} behavior não é BufferBehavior"

    def test_all_functions_have_description(self):
        """Todas funções devem ter descrição."""
        for name, func in HFUNCTION_CATALOG.items():
            assert func.description, f"Função {name} sem descrição"

    def test_all_functions_have_mongodb_equivalent(self):
        """Todas funções devem ter equivalente MongoDB."""
        for name, func in HFUNCTION_CATALOG.items():
            assert func.mongodb_equivalent, f"Função {name} sem mongodb_equivalent"


# ===========================================================================
# Tests: Comportamentos
# ===========================================================================

class TestBufferBehaviors:
    """Testes para comportamentos de buffer."""

    def test_modifies_buffer_functions(self):
        """Funções que modificam buffer estão corretas."""
        expected = ['HReadFirst', 'HReadNext', 'HReadSeekFirst', 'HReset']
        for name in expected:
            func = get_hfunction(name)
            assert func is not None, f"{name} não encontrada"
            assert func.behavior == BufferBehavior.MODIFIES_BUFFER, \
                f"{name} deveria ter MODIFIES_BUFFER"

    def test_reads_buffer_functions(self):
        """Funções que leem buffer estão corretas."""
        expected = ['HFound', 'HOut', 'HRecNum']
        for name in expected:
            func = get_hfunction(name)
            assert func is not None, f"{name} não encontrada"
            assert func.behavior == BufferBehavior.READS_BUFFER, \
                f"{name} deveria ter READS_BUFFER"

    def test_persists_buffer_functions(self):
        """Funções que persistem buffer estão corretas."""
        expected = ['HAdd', 'HModify', 'HDelete', 'HSave']
        for name in expected:
            func = get_hfunction(name)
            assert func is not None, f"{name} não encontrada"
            assert func.behavior == BufferBehavior.PERSISTS_BUFFER, \
                f"{name} deveria ter PERSISTS_BUFFER"

    def test_independent_functions(self):
        """Funções independentes estão corretas."""
        expected = ['HExecuteQuery', 'HNbRec', 'HCreation']
        for name in expected:
            func = get_hfunction(name)
            assert func is not None, f"{name} não encontrada"
            assert func.behavior == BufferBehavior.INDEPENDENT, \
                f"{name} deveria ter INDEPENDENT"

    def test_behavior_counts(self):
        """Cada comportamento tem múltiplas funções."""
        for behavior in BufferBehavior:
            funcs = get_functions_by_behavior(behavior)
            assert len(funcs) > 0, f"Nenhuma função com {behavior}"


# ===========================================================================
# Tests: Lookup Helpers
# ===========================================================================

class TestLookupHelpers:
    """Testes para funções de lookup."""

    def test_get_hfunction_found(self):
        """get_hfunction encontra função existente."""
        func = get_hfunction("HReadFirst")
        assert func is not None
        assert func.name == "HReadFirst"

    def test_get_hfunction_not_found(self):
        """get_hfunction retorna None para função inexistente."""
        func = get_hfunction("HFuncaoInexistente")
        assert func is None

    def test_get_hfunction_case_insensitive(self):
        """get_hfunction ignora case."""
        func1 = get_hfunction("HReadFirst")
        func2 = get_hfunction("hreadfirst")
        func3 = get_hfunction("HREADFIRST")

        assert func1 is not None
        assert func2 is not None
        assert func3 is not None
        assert func1.name == func2.name == func3.name

    def test_get_functions_by_behavior(self):
        """get_functions_by_behavior filtra corretamente."""
        funcs = get_functions_by_behavior(BufferBehavior.MODIFIES_BUFFER)
        assert len(funcs) >= 5  # Pelo menos 5 funções modificam buffer

        for func in funcs:
            assert func.behavior == BufferBehavior.MODIFIES_BUFFER

    def test_is_buffer_modifying_true(self):
        """is_buffer_modifying retorna True corretamente."""
        assert is_buffer_modifying("HReadFirst") == True
        assert is_buffer_modifying("HReadNext") == True
        assert is_buffer_modifying("HReset") == True

    def test_is_buffer_modifying_false(self):
        """is_buffer_modifying retorna False corretamente."""
        assert is_buffer_modifying("HNbRec") == False
        assert is_buffer_modifying("HFound") == False
        assert is_buffer_modifying("HAdd") == False

    def test_is_buffer_modifying_not_found(self):
        """is_buffer_modifying retorna False para função inexistente."""
        assert is_buffer_modifying("FuncaoInexistente") == False


# ===========================================================================
# Tests: LLM Markers
# ===========================================================================

class TestLLMMarkers:
    """Testes para marcação de funções que precisam LLM."""

    def test_hreadnext_needs_llm(self):
        """HReadNext precisa de LLM (contexto de iteração)."""
        assert needs_llm_conversion("HReadNext") == True

    def test_hexecutequery_needs_llm(self):
        """HExecuteQuery precisa de LLM (análise SQL)."""
        assert needs_llm_conversion("HExecuteQuery") == True

    def test_hadd_not_needs_llm(self):
        """HAdd não precisa de LLM (conversão direta)."""
        assert needs_llm_conversion("HAdd") == False

    def test_hreadfirst_not_needs_llm(self):
        """HReadFirst não precisa de LLM (conversão direta)."""
        assert needs_llm_conversion("HReadFirst") == False

    def test_functions_needing_llm_list(self):
        """get_functions_needing_llm retorna lista não vazia."""
        funcs = get_functions_needing_llm()
        assert len(funcs) > 0

        for func in funcs:
            assert func.needs_llm == True


# ===========================================================================
# Tests: MongoDB Equivalents
# ===========================================================================

class TestMongoDBEquivalents:
    """Testes para equivalentes MongoDB."""

    def test_hreadseekfirst_equivalent(self):
        """HReadSeekFirst tem equivalente find_one."""
        equiv = get_mongodb_equivalent("HReadSeekFirst")
        assert equiv is not None
        assert "find_one" in equiv

    def test_hadd_equivalent(self):
        """HAdd tem equivalente insert_one."""
        equiv = get_mongodb_equivalent("HAdd")
        assert equiv is not None
        assert "insert_one" in equiv

    def test_hnbrec_equivalent(self):
        """HNbRec tem equivalente count_documents."""
        equiv = get_mongodb_equivalent("HNbRec")
        assert equiv is not None
        assert "count" in equiv

    def test_not_found_returns_none(self):
        """Função inexistente retorna None."""
        equiv = get_mongodb_equivalent("FuncaoInexistente")
        assert equiv is None


# ===========================================================================
# Tests: Sanity Checks
# ===========================================================================

class TestSanityChecks:
    """Testes de sanidade do catálogo."""

    def test_all_modifies_have_equivalent(self):
        """Todas funções MODIFIES devem ter equivalente MongoDB."""
        funcs = get_functions_by_behavior(BufferBehavior.MODIFIES_BUFFER)
        for func in funcs:
            assert func.mongodb_equivalent, \
                f"{func.name} (MODIFIES) sem mongodb_equivalent"

    def test_all_persists_have_equivalent(self):
        """Todas funções PERSISTS devem ter equivalente MongoDB."""
        funcs = get_functions_by_behavior(BufferBehavior.PERSISTS_BUFFER)
        for func in funcs:
            assert func.mongodb_equivalent, \
                f"{func.name} (PERSISTS) sem mongodb_equivalent"

    def test_function_names_unique(self):
        """Nomes de funções são únicos."""
        names = list(HFUNCTION_CATALOG.keys())
        assert len(names) == len(set(names)), "Nomes duplicados no catálogo"

    def test_all_function_names_start_with_h(self):
        """Todas funções H* começam com H."""
        for name in HFUNCTION_CATALOG.keys():
            assert name.startswith('H'), f"{name} não começa com H"

    def test_get_all_function_names(self):
        """get_all_function_names retorna todas."""
        names = get_all_function_names()
        assert len(names) == len(HFUNCTION_CATALOG)
