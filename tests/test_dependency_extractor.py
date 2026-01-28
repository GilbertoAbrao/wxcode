"""
Testes para o DependencyExtractor.

Valida extração de:
- Chamadas de procedures
- Operações HyperFile
- Uso de classes
- Chamadas de APIs REST
"""

import pytest

from wxcode.parser.dependency_extractor import (
    DependencyExtractor,
    ExtractedDependencies,
)


class TestExtractedDependencies:
    """Testes para ExtractedDependencies."""

    def test_empty_dependencies(self):
        """Testa dependências vazias."""
        deps = ExtractedDependencies()
        assert deps.calls_procedures == []
        assert deps.uses_files == []
        assert deps.uses_classes == []
        assert deps.uses_apis == []
        assert deps.total_count == 0
        assert deps.is_empty() is True

    def test_with_dependencies(self):
        """Testa dependências preenchidas."""
        deps = ExtractedDependencies(
            calls_procedures=["ValidaCPF", "FormataCNPJ"],
            uses_files=["CLIENTE", "PEDIDO"],
            uses_classes=["classUsuario"],
            uses_apis=["REST"]
        )
        assert len(deps.calls_procedures) == 2
        assert "CLIENTE" in deps.uses_files
        assert "classUsuario" in deps.uses_classes
        assert deps.total_count == 6
        assert deps.is_empty() is False


class TestDependencyExtractorProcedureCalls:
    """Testes para extração de chamadas de procedures."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_simple_procedure_call(self):
        """Testa chamada de procedure simples."""
        code = "resultado = BuscaCEP(sCEP)"
        deps = self.extractor.extract(code)
        assert "BuscaCEP" in deps.calls_procedures

    def test_multiple_procedure_calls(self):
        """Testa múltiplas chamadas de procedures."""
        code = """
        sResultado = ValidaCPF(sCPF)
        IF sResultado <> "" THEN
            FormataCNPJ(sCNPJ)
            EnviaEmail(sDestinatario, sAssunto, sCorpo)
        END
        """
        deps = self.extractor.extract(code)
        assert "ValidaCPF" in deps.calls_procedures
        assert "FormataCNPJ" in deps.calls_procedures
        assert "EnviaEmail" in deps.calls_procedures

    def test_ignores_builtin_functions(self):
        """Testa que funções built-in são ignoradas."""
        code = """
        nLen = Length(sTexto)
        sLeft = Left(sTexto, 5)
        nVal = Val(sNumero)
        IF Contains(sTexto, "teste") THEN
            ArrayAdd(arrItems, sItem)
        END
        """
        deps = self.extractor.extract(code)
        assert "Length" not in deps.calls_procedures
        assert "Left" not in deps.calls_procedures
        assert "Val" not in deps.calls_procedures
        assert "Contains" not in deps.calls_procedures
        assert "ArrayAdd" not in deps.calls_procedures

    def test_ignores_control_structures(self):
        """Testa que estruturas de controle são ignoradas."""
        code = """
        IF bCondition THEN
            RESULT True
        ELSE
            RETURN False
        END
        FOR i = 1 TO 10
            SWITCH nOpcao
                CASE 1
                    BREAK
            END
        END
        """
        deps = self.extractor.extract(code)
        assert "IF" not in deps.calls_procedures
        assert "FOR" not in deps.calls_procedures
        assert "SWITCH" not in deps.calls_procedures

    def test_empty_code(self):
        """Testa código vazio."""
        deps = self.extractor.extract("")
        assert deps.is_empty()

    def test_none_code(self):
        """Testa código None."""
        deps = self.extractor.extract(None)
        assert deps.is_empty()


class TestDependencyExtractorHyperFile:
    """Testes para extração de operações HyperFile."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_hreadseekfirst(self):
        """Testa HReadSeekFirst."""
        code = "HReadSeekFirst(Cliente, CPF, sCPF)"
        deps = self.extractor.extract(code)
        assert "Cliente" in deps.uses_files

    def test_hreadfirst(self):
        """Testa HReadFirst."""
        code = "HReadFirst(Pedido, DataPedido)"
        deps = self.extractor.extract(code)
        assert "Pedido" in deps.uses_files

    def test_hadd(self):
        """Testa HAdd."""
        code = "HAdd(Usuario)"
        deps = self.extractor.extract(code)
        assert "Usuario" in deps.uses_files

    def test_hmodify(self):
        """Testa HModify."""
        code = "HModify(Produto)"
        deps = self.extractor.extract(code)
        assert "Produto" in deps.uses_files

    def test_hdelete(self):
        """Testa HDelete."""
        code = "HDelete(ItemPedido)"
        deps = self.extractor.extract(code)
        assert "ItemPedido" in deps.uses_files

    def test_multiple_operations(self):
        """Testa múltiplas operações HyperFile."""
        code = """
        HReadSeekFirst(Cliente, CPF, sCPF)
        IF HFound(Cliente) THEN
            HReadFirst(Pedido, ClienteID, Cliente.ID)
            WHILE NOT HOut(Pedido)
                HAdd(ItemLog)
                HReadNext(Pedido, ClienteID)
            END
        END
        """
        deps = self.extractor.extract(code)
        assert "Cliente" in deps.uses_files
        assert "Pedido" in deps.uses_files
        assert "ItemLog" in deps.uses_files

    def test_ignores_query_variables(self):
        """Testa que variáveis de query são ignoradas."""
        code = """
        HExecuteQuery(qsql)
        HExecuteQuery(query)
        HExecuteQuery(ds)
        """
        deps = self.extractor.extract(code)
        assert "qsql" not in deps.uses_files
        assert "query" not in deps.uses_files
        assert "ds" not in deps.uses_files


class TestDependencyExtractorClasses:
    """Testes para extração de uso de classes."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_class_usage(self):
        """Testa uso de classe."""
        code = "objUsuario is classUsuario"
        deps = self.extractor.extract(code)
        assert "classUsuario" in deps.uses_classes

    def test_class_dynamic(self):
        """Testa instanciação dinâmica."""
        code = "obj is dynamic classConfig"
        deps = self.extractor.extract(code)
        assert "classConfig" in deps.uses_classes

    def test_underscore_class(self):
        """Testa classe com prefixo underscore."""
        code = "helper is _classHelper"
        deps = self.extractor.extract(code)
        assert "_classHelper" in deps.uses_classes

    def test_multiple_classes(self):
        """Testa múltiplas classes."""
        code = """
        objUsuario is classUsuario
        objConfig is classConfig
        objPedido is classPedido
        """
        deps = self.extractor.extract(code)
        assert "classUsuario" in deps.uses_classes
        assert "classConfig" in deps.uses_classes
        assert "classPedido" in deps.uses_classes


class TestDependencyExtractorAPIs:
    """Testes para extração de chamadas de APIs REST."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_restsend(self):
        """Testa RESTSend."""
        code = "RESTSend(cRequest)"
        deps = self.extractor.extract(code)
        assert "REST" in deps.uses_apis

    def test_httprequest(self):
        """Testa HTTPRequest."""
        code = 'HTTPRequest("https://api.exemplo.com")'
        deps = self.extractor.extract(code)
        assert "REST" in deps.uses_apis

    def test_httpsend(self):
        """Testa HTTPSend."""
        code = "HTTPSend(oRequest)"
        deps = self.extractor.extract(code)
        assert "REST" in deps.uses_apis


class TestDependencyExtractorMerge:
    """Testes para merge de dependências."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_merge_empty(self):
        """Testa merge de dependências vazias."""
        deps1 = ExtractedDependencies()
        deps2 = ExtractedDependencies()
        merged = self.extractor.merge(deps1, deps2)
        assert merged.is_empty()

    def test_merge_distinct(self):
        """Testa merge de dependências distintas."""
        deps1 = ExtractedDependencies(
            calls_procedures=["ProcA"],
            uses_files=["CLIENTE"]
        )
        deps2 = ExtractedDependencies(
            calls_procedures=["ProcB"],
            uses_files=["PEDIDO"]
        )
        merged = self.extractor.merge(deps1, deps2)
        assert "ProcA" in merged.calls_procedures
        assert "ProcB" in merged.calls_procedures
        assert "CLIENTE" in merged.uses_files
        assert "PEDIDO" in merged.uses_files

    def test_merge_duplicates(self):
        """Testa merge sem duplicatas."""
        deps1 = ExtractedDependencies(
            calls_procedures=["ProcA", "ProcB"],
            uses_files=["CLIENTE"]
        )
        deps2 = ExtractedDependencies(
            calls_procedures=["ProcB", "ProcC"],
            uses_files=["CLIENTE", "PEDIDO"]
        )
        merged = self.extractor.merge(deps1, deps2)
        assert merged.calls_procedures.count("ProcB") == 1
        assert merged.uses_files.count("CLIENTE") == 1

    def test_extract_and_merge(self):
        """Testa extract_and_merge."""
        code1 = "ValidaCPF(sCPF)"
        code2 = "HReadSeekFirst(Cliente, CPF, sCPF)"
        code3 = "obj is classUsuario"

        deps = self.extractor.extract_and_merge(code1, code2, code3)
        assert "ValidaCPF" in deps.calls_procedures
        assert "Cliente" in deps.uses_files
        assert "classUsuario" in deps.uses_classes


class TestDependencyExtractorRealCode:
    """Testes com código real WLanguage."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_complex_procedure(self):
        """Testa procedure complexa."""
        code = """
PROCEDURE BuscaClientePorCPF(sCPF is string): boolean
// Busca cliente pelo CPF
sCliente is classCliente

HReadSeekFirst(Cliente, CPF, sCPF)
IF HFound(Cliente) THEN
    sCliente.ID = Cliente.ID
    sCliente.Nome = Cliente.Nome

    // Valida dados
    IF NOT ValidaCPF(sCPF) THEN
        Trace("CPF inválido")
        RESULT False
    END

    // Envia notificação
    EnviaNotificacao(sCliente.Email, "Login detectado")

    RESULT True
END

RESULT False
        """
        deps = self.extractor.extract(code)

        # Procedures chamadas
        assert "ValidaCPF" in deps.calls_procedures
        assert "EnviaNotificacao" in deps.calls_procedures
        # Built-in ignorado
        assert "Trace" not in deps.calls_procedures

        # HyperFile
        assert "Cliente" in deps.uses_files

        # Classes
        assert "classCliente" in deps.uses_classes

    def test_event_code(self):
        """Testa código de evento de controle."""
        code = """
// OnClick do botão Salvar
IF EDT_Nome = "" THEN
    Error("Nome obrigatório")
    SetFocus(EDT_Nome)
    RETURN
END

objProduto is classProduto
objProduto.Nome = EDT_Nome
objProduto.Preco = Val(EDT_Preco)

IF SalvarProduto(objProduto) THEN
    HAdd(LogOperacao)
    PageDisplay(PAGE_Lista)
END
        """
        deps = self.extractor.extract(code)

        assert "SalvarProduto" in deps.calls_procedures
        assert "LogOperacao" in deps.uses_files
        assert "classProduto" in deps.uses_classes
        # Built-ins ignorados
        assert "Error" not in deps.calls_procedures
        assert "Val" not in deps.calls_procedures
