"""
Testes para o WDG Parser (parser de procedures).
"""

import pytest
from pathlib import Path

from wxcode.parser.wdg_parser import (
    WdgParser,
    parse_wdg_file,
    ParsedProcedure,
    ParsedParameter,
    ParsedDependencies,
    ParsedStructure,
    ParsedProcedureSet,
)


class TestParsedParameter:
    """Testes para ParsedParameter."""

    def test_simple_parameter(self):
        """Testa criação de parâmetro simples."""
        param = ParsedParameter(name="sCEP", type="string")
        assert param.name == "sCEP"
        assert param.type == "string"
        assert param.is_local is False
        assert param.default_value is None

    def test_local_parameter_with_default(self):
        """Testa parâmetro LOCAL com valor padrão."""
        param = ParsedParameter(
            name="sNome",
            type="string",
            is_local=True,
            default_value='""'
        )
        assert param.is_local is True
        assert param.default_value == '""'


class TestParsedDependencies:
    """Testes para ParsedDependencies."""

    def test_empty_dependencies(self):
        """Testa dependências vazias."""
        deps = ParsedDependencies()
        assert deps.calls_procedures == []
        assert deps.uses_files == []
        assert deps.uses_apis == []
        assert deps.uses_queries == []

    def test_with_dependencies(self):
        """Testa dependências preenchidas."""
        deps = ParsedDependencies(
            calls_procedures=["ValidaCPF", "FormataCNPJ"],
            uses_files=["CLIENTE", "PEDIDO"],
            uses_apis=["REST"],
            uses_queries=["qBuscaCliente"]
        )
        assert len(deps.calls_procedures) == 2
        assert "CLIENTE" in deps.uses_files
        assert "REST" in deps.uses_apis


class TestParsedProcedure:
    """Testes para ParsedProcedure."""

    def test_procedure_defaults(self):
        """Testa valores padrão de procedure."""
        proc = ParsedProcedure(name="TestProc")
        assert proc.name == "TestProc"
        assert proc.type_code == 15
        assert proc.parameters == []
        assert proc.return_type is None
        assert proc.code == ""
        assert proc.is_public is True
        assert proc.is_internal is False


class TestParsedProcedureSet:
    """Testes para ParsedProcedureSet."""

    def test_total_procedures(self):
        """Testa contagem de procedures."""
        proc_set = ParsedProcedureSet(
            name="Util",
            procedures=[
                ParsedProcedure(name="Proc1", code_lines=10),
                ParsedProcedure(name="Proc2", code_lines=20),
                ParsedProcedure(name="Proc3", code_lines=15),
            ]
        )
        assert proc_set.total_procedures == 3

    def test_total_code_lines(self):
        """Testa soma de linhas de código."""
        proc_set = ParsedProcedureSet(
            name="Util",
            procedures=[
                ParsedProcedure(name="Proc1", code_lines=10),
                ParsedProcedure(name="Proc2", code_lines=20),
            ]
        )
        assert proc_set.total_code_lines == 30


class TestWdgParser:
    """Testes para WdgParser."""

    @pytest.fixture
    def sample_wdg(self, tmp_path):
        """Cria arquivo .wdg de teste."""
        content = '''#To edit and compare internal_properties
info :
 name : TestProcedures
 major_version : 28
 minor_version : 0
 type : 7
procedure_set :
 identifier : 0x123456
 code_elements :
  type_code : 31
  p_codes :
   -
     code : |1+

      STTest is structure

      	Nome is string
      	Valor is int

      end

     type : 720896
  procedures :
   -
     name : BuscaCEP
     procedure_id : 12345
     type_code : 15
     code : |1+
      PROCEDURE BuscaCEP(sCEP is string): JSON

      cMyRequest is restRequest
      cMyRequest..URL = "https://api.test.com"
      cMyResponse is restResponse = RESTSend(cMyRequest)

      RESULT cMyResponse.Content

     type : 458752
   -
     name : ValidaCPF
     procedure_id : 12346
     type_code : 15
     code : |1+
      PROCEDURE ValidaCPF(LOCAL sCPF is string): boolean

      HReadFirst(CLIENTE)

      IF HFound(CLIENTE) THEN
          RESULT True
      END

      RESULT False

     type : 458752
   -
     name : ProcessaDados
     procedure_id : 12347
     type_code : 15
     code : |1+
      PROCEDURE ProcessaDados(nId is int, sNome is string = "", bAtivo is boolean = True)

      ValidaCPF("12345678901")
      HAdd(PEDIDO)

     type : 458752
  procedure_templates : []
  property_templates : []
'''
        wdg_file = tmp_path / "TestProcedures.wdg"
        wdg_file.write_text(content)
        return wdg_file

    def test_init_with_valid_file(self, sample_wdg):
        """Testa inicialização com arquivo válido."""
        parser = WdgParser(sample_wdg)
        assert parser.file_path == sample_wdg

    def test_init_with_invalid_file(self, tmp_path):
        """Testa inicialização com arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            WdgParser(tmp_path / "nao_existe.wdg")

    def test_parse_basic(self, sample_wdg):
        """Testa parsing básico."""
        result = parse_wdg_file(sample_wdg)

        assert result.name == "TestProcedures"
        assert result.total_procedures == 3

    def test_parse_procedure_signature(self, sample_wdg):
        """Testa extração de assinatura de procedure."""
        result = parse_wdg_file(sample_wdg)

        # Encontra BuscaCEP
        busca_cep = next((p for p in result.procedures if p.name == "BuscaCEP"), None)
        assert busca_cep is not None
        assert busca_cep.return_type == "JSON"
        assert len(busca_cep.parameters) == 1
        assert busca_cep.parameters[0].name == "sCEP"
        assert busca_cep.parameters[0].type == "string"

    def test_parse_procedure_with_local_param(self, sample_wdg):
        """Testa procedure com parâmetro LOCAL."""
        result = parse_wdg_file(sample_wdg)

        valida_cpf = next((p for p in result.procedures if p.name == "ValidaCPF"), None)
        assert valida_cpf is not None
        assert valida_cpf.return_type == "boolean"
        assert len(valida_cpf.parameters) == 1
        assert valida_cpf.parameters[0].is_local is True

    def test_parse_procedure_with_defaults(self, sample_wdg):
        """Testa procedure com valores padrão."""
        result = parse_wdg_file(sample_wdg)

        proc_dados = next((p for p in result.procedures if p.name == "ProcessaDados"), None)
        assert proc_dados is not None
        assert len(proc_dados.parameters) == 3

        # Parâmetro com default string
        param_nome = next((p for p in proc_dados.parameters if p.name == "sNome"), None)
        assert param_nome is not None
        assert param_nome.default_value == '""'

        # Parâmetro com default boolean
        param_ativo = next((p for p in proc_dados.parameters if p.name == "bAtivo"), None)
        assert param_ativo is not None
        assert param_ativo.default_value == "True"

    def test_parse_dependencies_rest(self, sample_wdg):
        """Testa extração de dependências REST."""
        result = parse_wdg_file(sample_wdg)

        busca_cep = next((p for p in result.procedures if p.name == "BuscaCEP"), None)
        assert busca_cep is not None
        assert "REST" in busca_cep.dependencies.uses_apis

    def test_parse_dependencies_hyperfile(self, sample_wdg):
        """Testa extração de dependências HyperFile."""
        result = parse_wdg_file(sample_wdg)

        valida_cpf = next((p for p in result.procedures if p.name == "ValidaCPF"), None)
        assert valida_cpf is not None
        assert "CLIENTE" in valida_cpf.dependencies.uses_files

    def test_parse_dependencies_procedure_calls(self, sample_wdg):
        """Testa extração de chamadas de procedures."""
        result = parse_wdg_file(sample_wdg)

        proc_dados = next((p for p in result.procedures if p.name == "ProcessaDados"), None)
        assert proc_dados is not None
        assert "ValidaCPF" in proc_dados.dependencies.calls_procedures
        assert "PEDIDO" in proc_dados.dependencies.uses_files

    def test_parse_structures(self, sample_wdg):
        """Testa extração de estruturas."""
        result = parse_wdg_file(sample_wdg)

        assert len(result.structures) == 1
        assert result.structures[0].name == "STTest"
        assert len(result.structures[0].fields) == 2


class TestWdgParserEdgeCases:
    """Testes para casos especiais do WdgParser."""

    @pytest.fixture
    def edge_case_wdg(self, tmp_path):
        """Cria arquivo .wdg com casos especiais."""
        content = '''info :
 name : EdgeCases
 type : 7
procedure_set :
 code_elements :
  procedures :
   -
     name : NoReturnType
     type_code : 15
     code : |1+
      PROCEDURE NoReturnType(a, b, c)

      Info("Sem tipos")

     type : 458752
   -
     name : TupleReturn
     type_code : 15
     code : |1+
      PROCEDURE TupleReturn(): (string, int)

      RESULT ("ok", 200)

     type : 458752
   -
     name : ComplexTypes
     type_code : 15
     code : |1+
      PROCEDURE ComplexTypes(vRequest is httpRequest, vResponse is httpResponse)

      Info(vRequest.URL)

     type : 458752
   -
     name : InternalProc
     type_code : 15
     code : |1+
      INTERNAL PROCEDURE InternalProc(sData is string)

      Trace(sData)

     type : 458752
  procedure_templates : []
'''
        wdg_file = tmp_path / "EdgeCases.wdg"
        wdg_file.write_text(content)
        return wdg_file

    def test_procedure_without_types(self, edge_case_wdg):
        """Testa procedure sem tipos nos parâmetros."""
        result = parse_wdg_file(edge_case_wdg)

        no_return = next((p for p in result.procedures if p.name == "NoReturnType"), None)
        assert no_return is not None
        assert no_return.return_type is None
        assert len(no_return.parameters) == 3

        for param in no_return.parameters:
            assert param.type is None

    def test_procedure_tuple_return(self, edge_case_wdg):
        """Testa procedure com retorno de tupla."""
        result = parse_wdg_file(edge_case_wdg)

        tuple_ret = next((p for p in result.procedures if p.name == "TupleReturn"), None)
        assert tuple_ret is not None
        assert tuple_ret.return_type == "(string, int)"

    def test_procedure_complex_types(self, edge_case_wdg):
        """Testa procedure com tipos complexos."""
        result = parse_wdg_file(edge_case_wdg)

        complex_types = next((p for p in result.procedures if p.name == "ComplexTypes"), None)
        assert complex_types is not None
        assert len(complex_types.parameters) == 2
        assert complex_types.parameters[0].type == "httpRequest"
        assert complex_types.parameters[1].type == "httpResponse"

    def test_internal_procedure(self, edge_case_wdg):
        """Testa detecção de INTERNAL PROCEDURE."""
        result = parse_wdg_file(edge_case_wdg)

        internal = next((p for p in result.procedures if p.name == "InternalProc"), None)
        assert internal is not None
        assert internal.is_internal is True


class TestIntegrationWithRealFile:
    """Testes de integração com arquivo real."""

    @pytest.fixture
    def real_wdg(self):
        """Arquivo .wdg real do projeto de referência."""
        return Path("project-refs/Linkpay_ADM/Util.wdg")

    def test_parse_real_file(self, real_wdg):
        """Testa parsing de arquivo real."""
        if not real_wdg.exists():
            pytest.skip("Arquivo de referência não disponível")

        result = parse_wdg_file(real_wdg)

        assert result.name == "Util"
        assert result.total_procedures > 0

        print(f"\nProcedures encontradas: {result.total_procedures}")
        print(f"Linhas de código: {result.total_code_lines:,}")
        print(f"Estruturas: {len(result.structures)}")

    def test_real_file_procedures_have_signatures(self, real_wdg):
        """Verifica que procedures reais têm assinaturas parseadas."""
        if not real_wdg.exists():
            pytest.skip("Arquivo de referência não disponível")

        result = parse_wdg_file(real_wdg)

        # Pelo menos algumas procedures devem ter parâmetros
        procs_with_params = [p for p in result.procedures if len(p.parameters) > 0]
        assert len(procs_with_params) > 0

        print(f"\nProcedures com parâmetros: {len(procs_with_params)}")

    def test_real_file_dependencies(self, real_wdg):
        """Verifica extração de dependências em arquivo real."""
        if not real_wdg.exists():
            pytest.skip("Arquivo de referência não disponível")

        result = parse_wdg_file(real_wdg)

        # Conta dependências
        total_proc_calls = sum(len(p.dependencies.calls_procedures) for p in result.procedures)
        total_file_uses = sum(len(p.dependencies.uses_files) for p in result.procedures)
        total_api_uses = sum(len(p.dependencies.uses_apis) for p in result.procedures)

        print(f"\nChamadas de procedures: {total_proc_calls}")
        print(f"Arquivos HyperFile: {total_file_uses}")
        print(f"APIs externas: {total_api_uses}")

        # Deve ter algumas dependências
        assert total_proc_calls > 0 or total_file_uses > 0

    def test_busca_cep_procedure(self, real_wdg):
        """Testa procedure BuscaCEP específica do arquivo real."""
        if not real_wdg.exists():
            pytest.skip("Arquivo de referência não disponível")

        result = parse_wdg_file(real_wdg)

        busca_cep = next((p for p in result.procedures if p.name == "BuscaCEP"), None)
        assert busca_cep is not None
        assert busca_cep.return_type == "JSON"
        assert "REST" in busca_cep.dependencies.uses_apis

        print(f"\nBuscaCEP:")
        print(f"  Parâmetros: {[(p.name, p.type) for p in busca_cep.parameters]}")
        print(f"  Retorno: {busca_cep.return_type}")
        print(f"  APIs: {busca_cep.dependencies.uses_apis}")
