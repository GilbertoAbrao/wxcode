"""
Testes para o Project Element Mapper.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from beanie import PydanticObjectId

from wxcode.parser.line_reader import LineContext, read_lines, count_lines
from wxcode.parser.project_mapper import (
    ProjectElementMapper,
    MappingStats,
    ElementInfo,
    ParserState,
    WINDEV_TYPE_MAP,
    EXTENSION_TYPE_MAP,
    TYPE_LAYER_MAP,
)
from wxcode.models import ElementType, ElementLayer


class TestLineContext:
    """Testes para LineContext."""

    def test_is_list_item_true(self):
        """Testa detecção de item de lista."""
        ctx = LineContext(1, "  -", 2, "-")
        assert ctx.is_list_item is True

    def test_is_list_item_false(self):
        """Testa que linha normal não é item de lista."""
        ctx = LineContext(1, "  name : test", 2, "name : test")
        assert ctx.is_list_item is False

    def test_is_key_value_true(self):
        """Testa detecção de par chave:valor."""
        ctx = LineContext(1, "  name : test", 2, "name : test")
        assert ctx.is_key_value is True

    def test_is_key_value_false(self):
        """Testa que item de lista não é chave:valor."""
        ctx = LineContext(1, "  -", 2, "-")
        assert ctx.is_key_value is False

    def test_parse_key_value_with_quotes(self):
        """Testa parsing de valor com aspas."""
        ctx = LineContext(1, '  name : "MeuProjeto"', 2, 'name : "MeuProjeto"')
        key, value = ctx.parse_key_value()
        assert key == "name"
        assert value == "MeuProjeto"

    def test_parse_key_value_without_quotes(self):
        """Testa parsing de valor sem aspas."""
        ctx = LineContext(1, "  type : 65538", 2, "type : 65538")
        key, value = ctx.parse_key_value()
        assert key == "type"
        assert value == "65538"

    def test_parse_key_value_empty(self):
        """Testa parsing de linha sem chave:valor."""
        ctx = LineContext(1, "  -", 2, "-")
        key, value = ctx.parse_key_value()
        assert key == ""
        assert value == ""


class TestElementInfo:
    """Testes para ElementInfo."""

    def test_is_valid_true(self):
        """Testa elemento válido."""
        info = ElementInfo(name="PAGE_Login", physical_name=".\\PAGE_Login.wwh")
        assert info.is_valid() is True

    def test_is_valid_missing_name(self):
        """Testa elemento sem nome."""
        info = ElementInfo(name="", physical_name=".\\PAGE_Login.wwh")
        assert info.is_valid() is False

    def test_is_valid_missing_physical_name(self):
        """Testa elemento sem physical_name."""
        info = ElementInfo(name="PAGE_Login", physical_name="")
        assert info.is_valid() is False

    def test_excluded_from_default_empty(self):
        """Testa que excluded_from é lista vazia por padrão."""
        info = ElementInfo(name="PAGE_Login", physical_name=".\\PAGE_Login.wwh")
        assert info.excluded_from == []

    def test_excluded_from_with_values(self):
        """Testa excluded_from com valores."""
        info = ElementInfo(
            name="PAGE_Login",
            physical_name=".\\PAGE_Login.wwh",
            excluded_from=["config-id-1", "config-id-2"]
        )
        assert len(info.excluded_from) == 2
        assert "config-id-1" in info.excluded_from
        assert "config-id-2" in info.excluded_from


class TestMappingStats:
    """Testes para MappingStats."""

    def test_progress_percent(self):
        """Testa cálculo de progresso."""
        stats = MappingStats(total_lines=1000, lines_processed=500)
        assert stats.progress_percent == 50.0

    def test_progress_percent_zero_total(self):
        """Testa progresso com zero linhas."""
        stats = MappingStats(total_lines=0, lines_processed=0)
        assert stats.progress_percent == 0

    def test_duration_seconds(self):
        """Testa cálculo de duração."""
        from datetime import datetime, timedelta

        stats = MappingStats()
        stats.start_time = datetime.now()
        stats.end_time = stats.start_time + timedelta(seconds=10)

        assert stats.duration_seconds == 10.0


class TestTypeMappings:
    """Testes para mapeamentos de tipos."""

    def test_windev_type_map_page(self):
        """Testa mapeamento de tipo numérico para PAGE."""
        assert WINDEV_TYPE_MAP[65538] == ElementType.PAGE

    def test_windev_type_map_procedure_group(self):
        """Testa mapeamento de tipo numérico para PROCEDURE_GROUP."""
        assert WINDEV_TYPE_MAP[7] == ElementType.PROCEDURE_GROUP

    def test_windev_type_map_class(self):
        """Testa mapeamento de tipo numérico para CLASS."""
        assert WINDEV_TYPE_MAP[4] == ElementType.CLASS

    def test_extension_type_map_wwh(self):
        """Testa mapeamento de extensão .wwh para PAGE."""
        assert EXTENSION_TYPE_MAP[".wwh"] == ElementType.PAGE

    def test_extension_type_map_wdg(self):
        """Testa mapeamento de extensão .wdg para PROCEDURE_GROUP."""
        assert EXTENSION_TYPE_MAP[".wdg"] == ElementType.PROCEDURE_GROUP

    def test_type_layer_map_page(self):
        """Testa mapeamento de PAGE para camada UI."""
        assert TYPE_LAYER_MAP[ElementType.PAGE] == ElementLayer.UI

    def test_type_layer_map_query(self):
        """Testa mapeamento de QUERY para camada SCHEMA."""
        assert TYPE_LAYER_MAP[ElementType.QUERY] == ElementLayer.SCHEMA

    def test_type_layer_map_class(self):
        """Testa mapeamento de CLASS para camada DOMAIN."""
        assert TYPE_LAYER_MAP[ElementType.CLASS] == ElementLayer.DOMAIN


class TestProjectElementMapper:
    """Testes para ProjectElementMapper."""

    @pytest.fixture
    def sample_wwp(self, tmp_path):
        """Cria arquivo .wwp de teste."""
        content = '''#To edit and compare internal_properties
project :
 name : "TestProject"
 major_version : 28
 minor_version : 0
 type : 4097
 configurations :
  -
   name : "Config1"
   configuration_id : "test-id-1"
   type : 0
  -
   name : "Config2"
   configuration_id : "test-id-2"
   type : 1
 elements :
  -
   name : "PAGE_Login"
   identifier : "elem-1"
   type : 65538
   physical_name : ".\\PAGE_Login.wwh"
  -
   name : "ServerProcedures"
   identifier : "elem-2"
   type : 7
   physical_name : ".\\ServerProcedures.wdg"
  -
   name : "classUsuario"
   identifier : "elem-3"
   type : 4
   physical_name : ".\\classUsuario.wdc"
 analysis : ".\\BD.ana\\BD.wda"
'''
        wwp_file = tmp_path / "TestProject.wwp"
        wwp_file.write_text(content)
        return wwp_file

    def test_init_with_valid_file(self, sample_wwp):
        """Testa inicialização com arquivo válido."""
        mapper = ProjectElementMapper(sample_wwp)
        assert mapper.project_file == sample_wwp
        assert mapper.stats.total_lines == 0

    def test_init_with_invalid_file(self, tmp_path):
        """Testa inicialização com arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            ProjectElementMapper(tmp_path / "nao_existe.wwp")

    def test_init_with_invalid_extension(self, tmp_path):
        """Testa inicialização com extensão inválida."""
        invalid_file = tmp_path / "projeto.txt"
        invalid_file.write_text("conteudo")

        with pytest.raises(ValueError):
            ProjectElementMapper(invalid_file)

    @pytest.mark.asyncio
    async def test_extract_project_metadata(self, sample_wwp):
        """Testa extração de metadados do projeto."""
        mapper = ProjectElementMapper(sample_wwp)
        await mapper._extract_project_metadata()

        assert mapper._project_data["name"] == "TestProject"
        assert mapper._project_data["major_version"] == 28
        assert mapper._project_data["minor_version"] == 0
        assert mapper._project_data["type"] == 4097

    @pytest.mark.asyncio
    async def test_count_lines(self, sample_wwp):
        """Testa contagem de linhas."""
        count = await count_lines(sample_wwp)
        assert count > 0

    @pytest.mark.asyncio
    async def test_read_lines_streaming(self, sample_wwp):
        """Testa leitura em streaming."""
        lines = []
        async for ctx in read_lines(sample_wwp):
            lines.append(ctx)

        assert len(lines) > 0
        assert lines[0].line_number == 1

    @pytest.mark.skip(reason="Requer MongoDB inicializado para criar Element Document")
    def test_create_element(self, sample_wwp):
        """Testa criação de elemento."""
        mapper = ProjectElementMapper(sample_wwp)

        # Mock do project com PydanticObjectId válido
        project = MagicMock()
        project.id = PydanticObjectId()

        info = ElementInfo(
            name="PAGE_Login",
            identifier="elem-1",
            windev_type=65538,
            physical_name=".\\PAGE_Login.wwh"
        )

        element = mapper._create_element(project, info)

        assert element is not None
        assert element.source_name == "PAGE_Login"
        assert element.source_type == ElementType.PAGE
        assert element.layer == ElementLayer.UI

    @pytest.mark.skip(reason="Requer MongoDB inicializado para criar Element Document")
    def test_create_element_by_extension(self, sample_wwp):
        """Testa criação de elemento usando extensão como fallback."""
        mapper = ProjectElementMapper(sample_wwp)

        project = MagicMock()
        project.id = PydanticObjectId()

        info = ElementInfo(
            name="RPT_Extrato",
            identifier="elem-4",
            windev_type=None,  # Sem tipo numérico
            physical_name=".\\RPT_Extrato.wde"
        )

        element = mapper._create_element(project, info)

        assert element is not None
        assert element.source_type == ElementType.REPORT
        assert element.layer == ElementLayer.UI

    def test_create_element_invalid(self, sample_wwp):
        """Testa criação de elemento inválido."""
        mapper = ProjectElementMapper(sample_wwp)

        project = MagicMock()
        project.id = PydanticObjectId()

        info = ElementInfo(
            name="",
            identifier="",
            windev_type=None,
            physical_name=""
        )

        element = mapper._create_element(project, info)
        assert element is None


class TestElementConfigurationParsing:
    """Testes para parsing de configurations aninhadas em elementos."""

    @pytest.fixture
    def wwp_with_element_configs(self, tmp_path):
        """Cria arquivo .wwp com elementos que têm configurations."""
        content = '''#To edit and compare internal_properties
project :
 name : "TestProject"
 major_version : 28
 configurations :
  -
   name : "Producao"
   configuration_id : "917926033879572243"
   type : 2
  -
   name : "Staging"
   configuration_id : "13051986534836779703"
   type : 2
  -
   name : "Debug"
   configuration_id : "5382749985095619094"
   type : 2
 elements :
  -
   name : PAGE_Login
   identifier : 0x4f8875dc006ef2e4
   physical_name : .\\PAGE_Login.wwh
   type : 65538
   configurations :
    -
      configuration_id : 13051986534836779703
      excluded : true
    -
      configuration_id : 917926033879572243
  -
   name : PAGE_PRINCIPAL
   identifier : 0x4f8875dc006ef2e5
   physical_name : .\\PAGE_PRINCIPAL.wwh
   type : 65538
  -
   name : PAGE_ADMIN
   identifier : 0x4f8875dc006ef2e6
   physical_name : .\\PAGE_ADMIN.wwh
   type : 65538
   configurations :
    -
      configuration_id : 13051986534836779703
      excluded : true
    -
      configuration_id : 917926033879572243
      excluded : true
    -
      configuration_id : 5382749985095619094
      excluded : true
'''
        wwp_file = tmp_path / "TestProject.wwp"
        wwp_file.write_text(content)
        return wwp_file

    @pytest.mark.asyncio
    async def test_parse_element_excluded_from_one_config(self, wwp_with_element_configs):
        """Testa parsing de elemento excluído de uma configuração."""
        mapper = ProjectElementMapper(wwp_with_element_configs)

        # Simula streaming para capturar elementos
        elements_info: list[ElementInfo] = []
        mapper._state = ParserState.INITIAL

        from wxcode.parser.line_reader import read_lines

        async for ctx in read_lines(wwp_with_element_configs):
            # Detecta seção elements
            if ctx.stripped == "elements :" and ctx.indent < 3:
                mapper._state = ParserState.IN_ELEMENTS
                mapper._section_indent = ctx.indent
                mapper._element_indent = -1
                continue

            if mapper._state in [ParserState.IN_ELEMENTS, ParserState.IN_ELEMENT_CONFIGS]:
                # Simula _process_element_line sem MongoDB
                if ctx.is_list_item:
                    if mapper._element_indent == -1:
                        mapper._element_indent = ctx.indent

                    if ctx.indent != mapper._element_indent:
                        if mapper._state == ParserState.IN_ELEMENT_CONFIGS:
                            mapper._process_element_config_item(ctx)
                        continue

                    # Salva elemento anterior
                    if mapper._current_element.is_valid():
                        elements_info.append(mapper._current_element)
                    mapper._current_element = ElementInfo()
                    mapper._state = ParserState.IN_ELEMENTS
                    mapper._element_config_indent = -1
                    mapper._current_element_config_id = ""
                    mapper._in_element_config_item = False
                    continue

                # Detecta configurations aninhada
                if ctx.stripped == "configurations :" and ctx.indent > mapper._element_indent:
                    mapper._state = ParserState.IN_ELEMENT_CONFIGS
                    mapper._element_config_indent = ctx.indent
                    continue

                if mapper._state == ParserState.IN_ELEMENT_CONFIGS:
                    mapper._process_element_config_line(ctx)
                    continue

                if ctx.is_key_value:
                    key, value = ctx.parse_key_value()
                    if key == "name":
                        mapper._current_element.name = value
                    elif key == "identifier":
                        mapper._current_element.identifier = value
                    elif key == "type":
                        mapper._current_element.windev_type = int(value) if value else None
                    elif key == "physical_name":
                        mapper._current_element.physical_name = value

        # Salva último elemento
        if mapper._current_element.is_valid():
            elements_info.append(mapper._current_element)

        # Verifica elementos parseados
        assert len(elements_info) == 3

        # PAGE_Login excluída de 1 config (Staging)
        page_login = next(e for e in elements_info if e.name == "PAGE_Login")
        assert len(page_login.excluded_from) == 1
        assert "13051986534836779703" in page_login.excluded_from

        # PAGE_PRINCIPAL sem exclusões
        page_principal = next(e for e in elements_info if e.name == "PAGE_PRINCIPAL")
        assert len(page_principal.excluded_from) == 0

        # PAGE_ADMIN excluída de 3 configs
        page_admin = next(e for e in elements_info if e.name == "PAGE_ADMIN")
        assert len(page_admin.excluded_from) == 3
        assert "13051986534836779703" in page_admin.excluded_from
        assert "917926033879572243" in page_admin.excluded_from
        assert "5382749985095619094" in page_admin.excluded_from

    @pytest.mark.asyncio
    async def test_parse_element_without_configurations(self, wwp_with_element_configs):
        """Testa que elementos sem seção configurations têm excluded_from vazio."""
        mapper = ProjectElementMapper(wwp_with_element_configs)

        elements_info: list[ElementInfo] = []
        mapper._state = ParserState.INITIAL

        from wxcode.parser.line_reader import read_lines

        async for ctx in read_lines(wwp_with_element_configs):
            if ctx.stripped == "elements :" and ctx.indent < 3:
                mapper._state = ParserState.IN_ELEMENTS
                mapper._section_indent = ctx.indent
                mapper._element_indent = -1
                continue

            if mapper._state in [ParserState.IN_ELEMENTS, ParserState.IN_ELEMENT_CONFIGS]:
                if ctx.is_list_item:
                    if mapper._element_indent == -1:
                        mapper._element_indent = ctx.indent

                    if ctx.indent != mapper._element_indent:
                        if mapper._state == ParserState.IN_ELEMENT_CONFIGS:
                            mapper._process_element_config_item(ctx)
                        continue

                    if mapper._current_element.is_valid():
                        elements_info.append(mapper._current_element)
                    mapper._current_element = ElementInfo()
                    mapper._state = ParserState.IN_ELEMENTS
                    mapper._element_config_indent = -1
                    mapper._current_element_config_id = ""
                    mapper._in_element_config_item = False
                    continue

                if ctx.stripped == "configurations :" and ctx.indent > mapper._element_indent:
                    mapper._state = ParserState.IN_ELEMENT_CONFIGS
                    mapper._element_config_indent = ctx.indent
                    continue

                if mapper._state == ParserState.IN_ELEMENT_CONFIGS:
                    mapper._process_element_config_line(ctx)
                    continue

                if ctx.is_key_value:
                    key, value = ctx.parse_key_value()
                    if key == "name":
                        mapper._current_element.name = value
                    elif key == "physical_name":
                        mapper._current_element.physical_name = value

        if mapper._current_element.is_valid():
            elements_info.append(mapper._current_element)

        # PAGE_PRINCIPAL não tem seção configurations
        page_principal = next(e for e in elements_info if e.name == "PAGE_PRINCIPAL")
        assert page_principal.excluded_from == []


class TestIntegrationWithRealFile:
    """Testes de integração com arquivo real."""

    @pytest.fixture
    def real_wwp(self):
        """Arquivo .wwp real do projeto de referência."""
        return Path("project-refs/Linkpay_ADM/Linkpay_ADM.wwp")

    @pytest.mark.asyncio
    async def test_count_lines_real_file(self, real_wwp):
        """Testa contagem de linhas em arquivo real."""
        if not real_wwp.exists():
            pytest.skip("Arquivo de referência não disponível")

        count = await count_lines(real_wwp)

        assert count > 0
        print(f"\nLinhas no arquivo real: {count:,}")

    @pytest.mark.asyncio
    async def test_streaming_performance(self, real_wwp):
        """Testa performance do streaming."""
        if not real_wwp.exists():
            pytest.skip("Arquivo de referência não disponível")

        import time
        start = time.time()

        elements_found = 0
        in_elements = False

        async for ctx in read_lines(real_wwp):
            if ctx.stripped == "elements :":
                in_elements = True
            elif in_elements and ctx.is_list_item:
                elements_found += 1

        elapsed = time.time() - start

        print(f"\nElementos encontrados: {elements_found:,}")
        print(f"Tempo de streaming: {elapsed:.2f}s")

        # Deve ser rápido mesmo para arquivos grandes
        assert elapsed < 30  # máximo 30 segundos

    @pytest.mark.asyncio
    async def test_extract_metadata_real_file(self, real_wwp):
        """Testa extração de metadados de arquivo real."""
        if not real_wwp.exists():
            pytest.skip("Arquivo de referência não disponível")

        mapper = ProjectElementMapper(real_wwp)
        await mapper._extract_project_metadata()

        assert mapper._project_data.get("name") is not None
        print(f"\nProjeto: {mapper._project_data.get('name')}")
        print(f"Versão: {mapper._project_data.get('major_version')}.{mapper._project_data.get('minor_version')}")
