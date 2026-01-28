"""
Testes para o algoritmo de matching de controles.

Valida as 3 fases do matching:
1. Match exato por full_path ou name
2. Match por leaf name (único candidato)
3. Propagação de container mapping

Baseado na spec: openspec/changes/improve-control-matching/specs/control-matching/spec.md
"""

import pytest
from unittest.mock import Mock

from wxcode.parser.element_enricher import (
    ElementEnricher,
    MatchingContext,
)
from wxcode.parser.wwh_parser import ParsedControl
from wxcode.parser.pdf_element_parser import ParsedPDFElement


class TestMatchingContext:
    """Testes para MatchingContext."""

    def test_empty_context(self):
        """Testa contexto vazio."""
        ctx = MatchingContext()
        assert ctx.pdf_props == {}
        assert ctx.pdf_leaf_index == {}
        assert ctx.container_map == {}
        assert ctx.exact_matches == 0
        assert ctx.leaf_matches == 0
        assert ctx.propagated_matches == 0
        assert ctx.ambiguous == 0

    def test_context_with_data(self):
        """Testa contexto com dados."""
        ctx = MatchingContext(
            pdf_props={"ZONE.EDT_NOME": {"Height": 24}},
            pdf_leaf_index={"EDT_NOME": ["ZONE.EDT_NOME"]},
        )
        assert "ZONE.EDT_NOME" in ctx.pdf_props
        assert "EDT_NOME" in ctx.pdf_leaf_index


class TestBuildMatchingContext:
    """Testes para _build_matching_context."""

    @pytest.fixture
    def enricher(self, tmp_path):
        """Cria enricher para testes."""
        return ElementEnricher(
            pdf_docs_dir=tmp_path,
            project_dir=tmp_path,
        )

    def test_no_pdf_data(self, enricher):
        """Testa quando não há dados do PDF."""
        ctx = enricher._build_matching_context(None)
        assert ctx.pdf_props == {}
        assert ctx.pdf_leaf_index == {}

    def test_empty_pdf_data(self, enricher):
        """Testa quando PDF está vazio."""
        pdf_data = Mock(spec=ParsedPDFElement)
        pdf_data.control_properties = {}

        ctx = enricher._build_matching_context(pdf_data)
        assert ctx.pdf_props == {}
        assert ctx.pdf_leaf_index == {}

    def test_builds_leaf_index(self, enricher):
        """Testa construção do índice por leaf name."""
        pdf_data = Mock(spec=ParsedPDFElement)
        pdf_data.control_properties = {
            "ZONE_NoName1.EDT_NOME": {"Height": 24},
            "ZONE_NoName2.EDT_SOBRENOME": {"Height": 24},
            "EDT_EMAIL": {"Height": 24},
        }

        ctx = enricher._build_matching_context(pdf_data)

        assert "EDT_NOME" in ctx.pdf_leaf_index
        assert ctx.pdf_leaf_index["EDT_NOME"] == ["ZONE_NoName1.EDT_NOME"]
        assert "EDT_SOBRENOME" in ctx.pdf_leaf_index
        assert "EDT_EMAIL" in ctx.pdf_leaf_index
        assert ctx.pdf_leaf_index["EDT_EMAIL"] == ["EDT_EMAIL"]

    def test_multiple_candidates_same_leaf(self, enricher):
        """Testa múltiplos candidatos com mesmo leaf name."""
        pdf_data = Mock(spec=ParsedPDFElement)
        pdf_data.control_properties = {
            "ZONE_1.STC_NoName1": {"Height": 10},
            "ZONE_2.STC_NoName1": {"Height": 10},
            "ZONE_3.STC_NoName1": {"Height": 10},
        }

        ctx = enricher._build_matching_context(pdf_data)

        assert len(ctx.pdf_leaf_index["STC_NoName1"]) == 3


class TestMatchControl:
    """Testes para _match_control."""

    @pytest.fixture
    def enricher(self, tmp_path):
        """Cria enricher para testes."""
        return ElementEnricher(
            pdf_docs_dir=tmp_path,
            project_dir=tmp_path,
        )

    @pytest.fixture
    def make_control(self):
        """Factory para criar ParsedControl."""
        def _make(name: str, full_path: str = None):
            ctrl = Mock(spec=ParsedControl)
            ctrl.name = name
            ctrl.full_path = full_path or name
            return ctrl
        return _make

    # Fase 1: Match exato por full_path

    def test_exact_match_by_full_path(self, enricher, make_control):
        """Scenario: Match exato por full_path."""
        ctx = MatchingContext(
            pdf_props={
                "ZONE_NoName1.EDT_NOME": {"Height": 24, "Width": 200},
            },
            pdf_leaf_index={
                "EDT_NOME": ["ZONE_NoName1.EDT_NOME"],
            },
        )
        ctrl = make_control("EDT_NOME", "ZONE_NoName1.EDT_NOME")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is False
        assert props == {"Height": 24, "Width": 200}
        assert ctx.exact_matches == 1

    # Fase 1b: Match exato por name

    def test_exact_match_by_name(self, enricher, make_control):
        """Scenario: Match exato por name."""
        ctx = MatchingContext(
            pdf_props={
                "BTN_SALVAR": {"Height": 30, "Width": 100},
            },
            pdf_leaf_index={
                "BTN_SALVAR": ["BTN_SALVAR"],
            },
        )
        ctrl = make_control("BTN_SALVAR", "ZONE_X.BTN_SALVAR")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is False
        assert props == {"Height": 30, "Width": 100}
        assert ctx.exact_matches == 1

    # Fase 2: Match por leaf name

    def test_match_by_leaf_name_unique(self, enricher, make_control):
        """Scenario: Match por leaf name quando único."""
        ctx = MatchingContext(
            pdf_props={
                "ZONE_NoName2.EDT_NOME": {"Height": 24},
            },
            pdf_leaf_index={
                "EDT_NOME": ["ZONE_NoName2.EDT_NOME"],
            },
        )
        # WWH tem container diferente
        ctrl = make_control("EDT_NOME", "POPUP_ITEM.EDT_NOME")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is False
        assert props == {"Height": 24}
        assert ctx.leaf_matches == 1
        # Verifica container mapping foi registrado
        assert ctx.container_map["POPUP_ITEM"] == "ZONE_NoName2"

    def test_match_by_leaf_ambiguous(self, enricher, make_control):
        """Scenario: Match ambíguo permanece órfão."""
        ctx = MatchingContext(
            pdf_props={
                "ZONE_1.STC_NoName1": {"Height": 10},
                "ZONE_2.STC_NoName1": {"Height": 12},
            },
            pdf_leaf_index={
                "STC_NoName1": ["ZONE_1.STC_NoName1", "ZONE_2.STC_NoName1"],
            },
        )
        ctrl = make_control("STC_NoName1", "POPUP.STC_NoName1")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is True
        assert props is None
        assert ctx.ambiguous == 1
        assert ctx.leaf_matches == 0

    # Fase 3: Container Mapping Propagation

    def test_propagated_match_via_container_mapping(self, enricher, make_control):
        """Scenario: Propagação para filhos do mesmo container."""
        ctx = MatchingContext(
            pdf_props={
                "ZONE_NoName2.BTN_X": {"Height": 30},
                "ZONE_NoName2.EDT_Y": {"Height": 24},
            },
            pdf_leaf_index={
                # BTN_X não é único (simulando que não fez match direto)
                "BTN_X": ["ZONE_NoName2.BTN_X", "ZONE_OTHER.BTN_X"],
                "EDT_Y": ["ZONE_NoName2.EDT_Y"],
            },
            # Mapping já descoberto anteriormente
            container_map={
                "POPUP_ITEM": "ZONE_NoName2",
            },
        )
        # Controle órfão que pode usar o mapping
        ctrl = make_control("BTN_X", "POPUP_ITEM.BTN_X")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is False
        assert props == {"Height": 30}
        assert ctx.propagated_matches == 1

    def test_propagated_match_nested_container(self, enricher, make_control):
        """Scenario: Múltiplos níveis de aninhamento."""
        ctx = MatchingContext(
            pdf_props={
                "ZONE_NoName2.CELL_1.EDT_CAMPO": {"Height": 24},
            },
            pdf_leaf_index={
                "EDT_CAMPO": ["ZONE_NoName2.CELL_1.EDT_CAMPO"],
            },
            container_map={
                "POPUP_ITEM": "ZONE_NoName2",
            },
        )
        # Este cenário precisa de ajuste - o algoritmo atual só substitui
        # o primeiro nível do container
        ctrl = make_control("EDT_CAMPO", "POPUP_ITEM.CELL_1.EDT_CAMPO")

        # O algoritmo atual NÃO vai fazer match porque:
        # - wwh_parent = "POPUP_ITEM.CELL_1" (não "POPUP_ITEM")
        # - Então não encontra no container_map
        # Este é um caso que pode ser melhorado no futuro
        props, is_orphan = enricher._match_control(ctrl, ctx)

        # Por enquanto, este caso resulta em match por leaf único
        assert is_orphan is False
        assert props == {"Height": 24}
        assert ctx.leaf_matches == 1

    # Casos especiais

    def test_no_pdf_data_all_orphans(self, enricher, make_control):
        """Scenario: Sem PDF disponível."""
        ctx = MatchingContext()  # Vazio
        ctrl = make_control("EDT_NOME", "ZONE.EDT_NOME")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is True
        assert props is None

    def test_control_not_in_pdf_is_orphan(self, enricher, make_control):
        """Controle que não existe no PDF é órfão."""
        ctx = MatchingContext(
            pdf_props={
                "ZONE.EDT_OUTRO": {"Height": 24},
            },
            pdf_leaf_index={
                "EDT_OUTRO": ["ZONE.EDT_OUTRO"],
            },
        )
        ctrl = make_control("EDT_INEXISTENTE", "ZONE.EDT_INEXISTENTE")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is True
        assert props is None


class TestMatchingStatistics:
    """Testes para estatísticas de matching."""

    @pytest.fixture
    def enricher(self, tmp_path):
        """Cria enricher para testes."""
        return ElementEnricher(
            pdf_docs_dir=tmp_path,
            project_dir=tmp_path,
        )

    @pytest.fixture
    def make_control(self):
        """Factory para criar ParsedControl."""
        def _make(name: str, full_path: str = None):
            ctrl = Mock(spec=ParsedControl)
            ctrl.name = name
            ctrl.full_path = full_path or name
            return ctrl
        return _make

    def test_statistics_accumulate(self, enricher, make_control):
        """Testa que estatísticas acumulam corretamente."""
        ctx = MatchingContext(
            pdf_props={
                "EDT_A": {"Height": 24},
                "ZONE_X.EDT_B": {"Height": 24},
                "ZONE_1.EDT_C": {"Height": 24},
                "ZONE_2.EDT_C": {"Height": 24},  # Ambíguo
            },
            pdf_leaf_index={
                "EDT_A": ["EDT_A"],
                "EDT_B": ["ZONE_X.EDT_B"],
                "EDT_C": ["ZONE_1.EDT_C", "ZONE_2.EDT_C"],
            },
        )

        # Match exato
        ctrl_a = make_control("EDT_A")
        enricher._match_control(ctrl_a, ctx)

        # Match por leaf
        ctrl_b = make_control("EDT_B", "POPUP.EDT_B")
        enricher._match_control(ctrl_b, ctx)

        # Ambíguo
        ctrl_c = make_control("EDT_C", "POPUP.EDT_C")
        enricher._match_control(ctrl_c, ctx)

        # Órfão
        ctrl_d = make_control("EDT_D", "ZONE.EDT_D")
        enricher._match_control(ctrl_d, ctx)

        assert ctx.exact_matches == 1
        assert ctx.leaf_matches == 1
        assert ctx.ambiguous == 1
        # propagated_matches permanece 0 porque não há mapping


class TestContainerControlsInParentPDF:
    """
    Testes para verificar que controles dentro de containers (POPUP, ZONE, etc.)
    fazem match usando o PDF do elemento pai.

    POPUPs e outros containers não são elementos separados - eles são controles
    dentro de páginas. O PDF da página pai lista todos os controles com paths
    completos como "POPUP_ITEM.EDT_NOME".
    """

    @pytest.fixture
    def enricher(self, tmp_path):
        """Cria enricher para testes."""
        return ElementEnricher(
            pdf_docs_dir=tmp_path,
            project_dir=tmp_path,
        )

    @pytest.fixture
    def make_control(self):
        """Factory para criar ParsedControl."""
        def _make(name: str, full_path: str = None):
            ctrl = Mock(spec=ParsedControl)
            ctrl.name = name
            ctrl.full_path = full_path or name
            return ctrl
        return _make

    def test_popup_control_matches_in_parent_context(self, enricher, make_control):
        """
        Controle dentro de POPUP faz match usando contexto único do elemento pai.

        O PDF da página pai lista: "POPUP_ITEM.EDT_NOME"
        O WWH tem: "POPUP_ITEM.EDT_NOME"
        Deve fazer match exato.
        """
        ctx = MatchingContext(
            pdf_props={
                "POPUP_ITEM.EDT_NOME": {"Height": 30, "Width": 340},
                "POPUP_ITEM.BTN_SALVAR": {"Height": 25, "Width": 100},
                "CELL_NoName1.EDT_CODIGO": {"Height": 24, "Width": 80},
            },
            pdf_leaf_index={
                "EDT_NOME": ["POPUP_ITEM.EDT_NOME"],
                "BTN_SALVAR": ["POPUP_ITEM.BTN_SALVAR"],
                "EDT_CODIGO": ["CELL_NoName1.EDT_CODIGO"],
            },
        )
        ctrl = make_control("EDT_NOME", "POPUP_ITEM.EDT_NOME")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is False
        assert props["Height"] == 30
        assert props["Width"] == 340
        assert ctx.exact_matches == 1

    def test_zone_control_matches_in_parent_context(self, enricher, make_control):
        """
        Controle dentro de ZONE faz match usando contexto único.
        """
        ctx = MatchingContext(
            pdf_props={
                "ZONE_NoName2.TABLE_LISTA.COL_ID": {"Width": 50},
                "ZONE_NoName2.TABLE_LISTA.COL_NOME": {"Width": 200},
            },
            pdf_leaf_index={
                "COL_ID": ["ZONE_NoName2.TABLE_LISTA.COL_ID"],
                "COL_NOME": ["ZONE_NoName2.TABLE_LISTA.COL_NOME"],
            },
        )
        ctrl = make_control("COL_ID", "ZONE_NoName2.TABLE_LISTA.COL_ID")

        props, is_orphan = enricher._match_control(ctrl, ctx)

        assert is_orphan is False
        assert props["Width"] == 50

    def test_multiple_containers_single_context(self, enricher, make_control):
        """
        Múltiplos containers (POPUP, ZONE, CELL) no mesmo contexto.
        """
        ctx = MatchingContext(
            pdf_props={
                "POPUP_ITEM.EDT_NOME": {"Height": 30},
                "ZONE_NoName2.BTN_PESQUISAR": {"Height": 25},
                "CELL_Header.STC_TITULO": {"Height": 20},
            },
            pdf_leaf_index={
                "EDT_NOME": ["POPUP_ITEM.EDT_NOME"],
                "BTN_PESQUISAR": ["ZONE_NoName2.BTN_PESQUISAR"],
                "STC_TITULO": ["CELL_Header.STC_TITULO"],
            },
        )

        # Testa cada tipo de container
        ctrl1 = make_control("EDT_NOME", "POPUP_ITEM.EDT_NOME")
        props1, orphan1 = enricher._match_control(ctrl1, ctx)
        assert orphan1 is False

        ctrl2 = make_control("BTN_PESQUISAR", "ZONE_NoName2.BTN_PESQUISAR")
        props2, orphan2 = enricher._match_control(ctrl2, ctx)
        assert orphan2 is False

        ctrl3 = make_control("STC_TITULO", "CELL_Header.STC_TITULO")
        props3, orphan3 = enricher._match_control(ctrl3, ctx)
        assert orphan3 is False

        assert ctx.exact_matches == 3


class TestBackwardCompatibility:
    """Testes de compatibilidade retroativa."""

    @pytest.fixture
    def enricher(self, tmp_path):
        """Cria enricher para testes."""
        return ElementEnricher(
            pdf_docs_dir=tmp_path,
            project_dir=tmp_path,
        )

    def test_no_pdf_no_crash(self, enricher):
        """Verifica que sem PDF o sistema não crasheia."""
        ctx = enricher._build_matching_context(None)
        assert ctx.pdf_props == {}
        assert ctx.pdf_leaf_index == {}

    def test_empty_control_properties_no_crash(self, enricher):
        """Verifica que PDF vazio não crasheia."""
        pdf_data = Mock(spec=ParsedPDFElement)
        pdf_data.control_properties = None

        ctx = enricher._build_matching_context(pdf_data)
        assert ctx.pdf_props == {}
