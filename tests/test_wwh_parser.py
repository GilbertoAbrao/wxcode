"""
Testes para o WWH Parser.

Valida extração de:
- Controles e hierarquia
- Eventos
- Procedures locais
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from wxcode.parser.wwh_parser import (
    WWHParser,
    ParsedPage,
    ParsedControl,
    ParsedEvent,
    ParsedLocalProcedure,
    ParsedLocalParameter,
)


class TestParsedLocalParameter:
    """Testes para ParsedLocalParameter."""

    def test_simple_parameter(self):
        """Testa criação de parâmetro simples."""
        param = ParsedLocalParameter(name="sCEP", type="string")
        assert param.name == "sCEP"
        assert param.type == "string"
        assert param.is_local is False
        assert param.default_value is None

    def test_local_parameter_with_default(self):
        """Testa parâmetro LOCAL com valor padrão."""
        param = ParsedLocalParameter(
            name="sNome",
            type="string",
            is_local=True,
            default_value='""'
        )
        assert param.is_local is True
        assert param.default_value == '""'


class TestParsedLocalProcedure:
    """Testes para ParsedLocalProcedure."""

    def test_procedure_defaults(self):
        """Testa valores padrão de procedure."""
        proc = ParsedLocalProcedure(name="Local_Display")
        assert proc.name == "Local_Display"
        assert proc.parameters == []
        assert proc.return_type is None
        assert proc.code == ""
        assert proc.code_lines == 0
        assert proc.is_internal is False

    def test_procedure_with_params_and_return(self):
        """Testa procedure com parâmetros e retorno."""
        proc = ParsedLocalProcedure(
            name="Local_Calcular",
            parameters=[
                ParsedLocalParameter(name="nValor1", type="int"),
                ParsedLocalParameter(name="nValor2", type="int"),
            ],
            return_type="int",
            code="PROCEDURE Local_Calcular(nValor1 is int, nValor2 is int): int\nRESULT nValor1 + nValor2",
            code_lines=2
        )
        assert len(proc.parameters) == 2
        assert proc.return_type == "int"
        assert proc.code_lines == 2


class TestWWHParserLocalProcedures:
    """Testes para extração de procedures locais."""

    def test_extract_simple_procedure(self):
        """Testa extração de procedure simples."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Display_Time()
Trace("Hora: " + TimeSys())
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert procs[0].name == "Local_Display_Time"
        assert procs[0].parameters == []
        assert procs[0].return_type is None

    def test_extract_procedure_with_params(self):
        """Testa extração de procedure com parâmetros."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Listar(bNovoPeriodo is boolean)
IF bNovoPeriodo THEN
    Trace("Novo período")
END
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert procs[0].name == "Local_Listar"
        assert len(procs[0].parameters) == 1
        assert procs[0].parameters[0].name == "bNovoPeriodo"
        assert procs[0].parameters[0].type == "boolean"

    def test_extract_procedure_with_return_type(self):
        """Testa extração de procedure com tipo de retorno."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Calcular(): int
RESULT 42
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert procs[0].name == "Local_Calcular"
        assert procs[0].return_type == "int"

    def test_extract_multiple_procedures(self):
        """Testa extração de múltiplas procedures."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Init()
Trace("Init")

PROCEDURE Local_Process(sInput is string): string
RESULT Upper(sInput)

PROCEDURE Local_Cleanup()
Trace("Cleanup")
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 3
        assert procs[0].name == "Local_Init"
        assert procs[1].name == "Local_Process"
        assert procs[2].name == "Local_Cleanup"

    def test_extract_internal_procedure(self):
        """Testa extração de INTERNAL PROCEDURE."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
INTERNAL PROCEDURE Local_Helper()
Trace("Helper")
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert procs[0].is_internal is True

    def test_extract_procedure_with_multiple_params(self):
        """Testa procedure com múltiplos parâmetros."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Enviar(sDestino is string, sAssunto is string, sCorpo is string): boolean
RESULT True
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert len(procs[0].parameters) == 3
        assert procs[0].parameters[0].name == "sDestino"
        assert procs[0].parameters[1].name == "sAssunto"
        assert procs[0].parameters[2].name == "sCorpo"
        assert procs[0].return_type == "boolean"

    def test_extract_procedure_with_default_value(self):
        """Testa procedure com parâmetro com valor padrão."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Format(sTexto is string, bMaiusculo is boolean = True): string
IF bMaiusculo THEN
    RESULT Upper(sTexto)
END
RESULT sTexto
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert len(procs[0].parameters) == 2
        assert procs[0].parameters[1].default_value == "True"

    def test_extract_empty_code(self):
        """Testa código vazio."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        procs = parser._extract_local_procedures("")
        assert procs == []

    def test_extract_no_procedures(self):
        """Testa código sem procedures."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
// Just some comments
IF bCondition THEN
    Trace("Test")
END
"""
        procs = parser._extract_local_procedures(code)
        assert procs == []

    def test_procedure_code_lines(self):
        """Testa contagem de linhas de código."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Complex()
nTotal = 0
FOR i = 1 TO 10
    nTotal += i
END
RESULT nTotal
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert procs[0].code_lines > 0

    def test_procedure_with_error_handling(self):
        """Testa detecção de tratamento de erros."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        code = """
PROCEDURE Local_Safe()
CASE ERROR:
    Trace("Erro: " + ErrorInfo())
END
"""
        procs = parser._extract_local_procedures(code)
        assert len(procs) == 1
        assert procs[0].has_error_handling is True


class TestWWHParserParameterParsing:
    """Testes para parsing de parâmetros."""

    def test_split_parameters_simple(self):
        """Testa split de parâmetros simples."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        params = parser._split_parameters("a, b, c")
        assert params == ["a", "b", "c"]

    def test_split_parameters_with_defaults(self):
        """Testa split de parâmetros com defaults."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        # Note: commas inside quotes are not handled (edge case)
        params = parser._split_parameters('a is string = "", b is int = 0')
        assert len(params) == 2
        assert 'a is string = ""' in params[0]
        assert 'b is int = 0' in params[1]

    def test_parse_single_parameter_simple(self):
        """Testa parsing de parâmetro simples."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        param = parser._parse_single_parameter("sNome is string")
        assert param.name == "sNome"
        assert param.type == "string"
        assert param.is_local is False

    def test_parse_single_parameter_local(self):
        """Testa parsing de parâmetro LOCAL."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        param = parser._parse_single_parameter("LOCAL sTemp is string")
        assert param.name == "sTemp"
        assert param.is_local is True

    def test_parse_single_parameter_with_default(self):
        """Testa parsing de parâmetro com default."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        param = parser._parse_single_parameter("nValor is int = 10")
        assert param.name == "nValor"
        assert param.type == "int"
        assert param.default_value == "10"

    def test_parse_single_parameter_no_type(self):
        """Testa parsing de parâmetro sem tipo."""
        parser = WWHParser.__new__(WWHParser)
        parser.file_path = Path("test.wwh")

        param = parser._parse_single_parameter("sNome")
        assert param.name == "sNome"
        assert param.type is None


class TestParsedPage:
    """Testes para ParsedPage."""

    def test_page_with_local_procedures(self):
        """Testa página com procedures locais."""
        page = ParsedPage(
            name="PAGE_Test",
            type_code=65538,
            local_procedures=[
                ParsedLocalProcedure(name="Local_Init"),
                ParsedLocalProcedure(name="Local_Process"),
            ]
        )
        assert len(page.local_procedures) == 2
        assert page.local_procedures[0].name == "Local_Init"
        assert page.local_procedures[1].name == "Local_Process"
