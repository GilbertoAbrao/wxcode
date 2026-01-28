"""
Testes de integração para extração de DataBinding.

Valida o fluxo completo de extração de binding sem necessidade
de conexão com MongoDB.
"""

import pytest

from wxcode.models.control import (
    Control,
    DataBindingInfo,
    DataBindingType,
)
from wxcode.models.element import ElementDependencies
from wxcode.parser.dependency_extractor import DependencyExtractor, TableUsage
from wxcode.parser.pdf_element_parser import PDFElementParser


class TestBindingExtractionIntegration:
    """Testes de integração para extração de binding."""

    def test_full_binding_extraction_flow(self):
        """
        Testa fluxo completo: PDF text → DataBindingInfo → TableUsage → ElementDependencies.
        """
        # 1. Simula texto de PDF com binding
        pdf_text = """
EDT_ClienteNome
Height
24
Width
200
Linked item : CLIENTE.nome
Visible
Yes

EDT_ClienteCPF
Height
24
Width
150
Linked item : CLIENTE.cpf
Visible
Yes

EDT_ProdutoDesc
Height
24
Width
300
Linked item : PRODUTO.descricao
Visible
Yes
"""
        # 2. Extrai bindings do PDF
        parser = PDFElementParser.__new__(PDFElementParser)
        bindings_found = []

        # Simula parsing por controle
        control_blocks = pdf_text.strip().split('\n\n')
        for block in control_blocks:
            if block.strip():
                binding = parser._extract_binding(block)
                if binding:
                    bindings_found.append(binding)

        assert len(bindings_found) == 3

        # 3. Cria mock controls com os bindings extraídos
        class MockControl:
            def __init__(self, name, binding):
                self.name = name
                self.data_binding = binding

        mock_controls = [
            MockControl('EDT_ClienteNome', bindings_found[0]),
            MockControl('EDT_ClienteCPF', bindings_found[1]),
            MockControl('EDT_ProdutoDesc', bindings_found[2]),
        ]

        # 4. Extrai TableUsage via DependencyExtractor
        extractor = DependencyExtractor()
        table_usages = extractor.extract_table_bindings(mock_controls)

        assert len(table_usages) == 3

        # 5. Obtém tabelas únicas
        unique_tables = extractor.get_unique_tables_from_bindings(mock_controls)
        assert len(unique_tables) == 2
        assert 'CLIENTE' in unique_tables
        assert 'PRODUTO' in unique_tables

        # 6. Adiciona a ElementDependencies
        deps = ElementDependencies()
        for table in unique_tables:
            deps.add_bound_table(table)

        assert len(deps.bound_tables) == 2
        assert 'CLIENTE' in deps.bound_tables
        assert 'PRODUTO' in deps.bound_tables

    def test_binding_types_in_integration(self):
        """Testa que diferentes tipos de binding são extraídos corretamente."""
        parser = PDFElementParser.__new__(PDFElementParser)

        test_cases = [
            ("Linked item : CLIENTE.nome", DataBindingType.SIMPLE, "CLIENTE", "nome"),
            ("File link : PEDIDO.data", DataBindingType.SIMPLE, "PEDIDO", "data"),
            ("Binding : :gsVariavel", DataBindingType.VARIABLE, None, None),
        ]

        for text, expected_type, expected_table, expected_field in test_cases:
            binding = parser._extract_binding(text)
            assert binding is not None, f"Falhou para: {text}"
            assert binding.binding_type == expected_type
            assert binding.table_name == expected_table
            assert binding.field_name == expected_field

    def test_table_usage_context(self):
        """Testa que TableUsage tem contexto correto."""
        extractor = DependencyExtractor()

        class MockControl:
            def __init__(self, name):
                self.name = name
                self.data_binding = DataBindingInfo(
                    table_name="CLIENTE",
                    field_name="email"
                )

        controls = [MockControl('EDT_Email')]
        usages = extractor.extract_table_bindings(controls)

        assert len(usages) == 1
        assert usages[0].context == "control:EDT_Email"
        assert usages[0].usage_type == "binding"
        assert usages[0].field_name == "email"

    def test_duplicate_tables_handled(self):
        """Testa que tabelas duplicadas são tratadas corretamente."""
        extractor = DependencyExtractor()

        class MockControl:
            def __init__(self, name, table, field):
                self.name = name
                self.data_binding = DataBindingInfo(
                    table_name=table,
                    field_name=field
                )

        controls = [
            MockControl('EDT_Nome', 'CLIENTE', 'nome'),
            MockControl('EDT_CPF', 'CLIENTE', 'cpf'),
            MockControl('EDT_Email', 'CLIENTE', 'email'),
            MockControl('EDT_Fone', 'CLIENTE', 'telefone'),
        ]

        usages = extractor.extract_table_bindings(controls)
        assert len(usages) == 4  # Todos os usos

        unique_tables = extractor.get_unique_tables_from_bindings(controls)
        assert len(unique_tables) == 1  # Apenas CLIENTE (único)
        assert unique_tables[0] == 'CLIENTE'

    def test_controls_without_binding_ignored(self):
        """Testa que controles sem binding são ignorados."""
        extractor = DependencyExtractor()

        class MockControlWithBinding:
            def __init__(self):
                self.name = 'EDT_Nome'
                self.data_binding = DataBindingInfo(
                    table_name='CLIENTE',
                    field_name='nome'
                )

        class MockControlWithoutBinding:
            def __init__(self):
                self.name = 'BTN_Salvar'
                self.data_binding = None

        class MockControlNoAttribute:
            def __init__(self):
                self.name = 'LBL_Titulo'
                # Sem atributo data_binding

        controls = [
            MockControlWithBinding(),
            MockControlWithoutBinding(),
            MockControlNoAttribute(),
        ]

        usages = extractor.extract_table_bindings(controls)
        assert len(usages) == 1
        assert usages[0].table_name == 'CLIENTE'


class TestHyperFileCatalogIntegration:
    """Testes de integração do catálogo de funções H*."""

    def test_catalog_with_dependency_extractor(self):
        """Testa que funções H* do catálogo estão no regex do extractor."""
        from wxcode.transpiler.hyperfile_catalog import HFUNCTION_CATALOG

        extractor = DependencyExtractor()

        # Funções principais que devem ser reconhecidas
        critical_functions = [
            'HReadFirst', 'HReadNext', 'HAdd', 'HModify',
            'HDelete', 'HReadSeekFirst', 'HExecuteQuery'
        ]

        for func_name in critical_functions:
            assert func_name in HFUNCTION_CATALOG, \
                f"{func_name} não está no catálogo"

            # Testa que o regex do extractor reconhece a função
            test_code = f'{func_name}(CLIENTE, NOME)'
            deps = extractor.extract(test_code)
            assert 'CLIENTE' in deps.uses_files, \
                f"Extractor não reconheceu {func_name}"

    def test_buffer_behavior_completeness(self):
        """Testa que todas funções têm comportamento de buffer definido."""
        from wxcode.transpiler.hyperfile_catalog import (
            HFUNCTION_CATALOG,
            BufferBehavior
        )

        for name, func in HFUNCTION_CATALOG.items():
            assert func.behavior in BufferBehavior, \
                f"{name} tem behavior inválido"


class TestDataBindingModelIntegration:
    """Testes de integração do model DataBindingInfo."""

    def test_databinding_serialization_roundtrip(self):
        """Testa serialização e deserialização."""
        original = DataBindingInfo(
            binding_type=DataBindingType.SIMPLE,
            table_name="CLIENTE",
            field_name="nome",
            source="pdf",
            raw_value="CLIENTE.nome"
        )

        # Serializa
        data = original.model_dump()

        # Deserializa
        restored = DataBindingInfo(**data)

        assert restored.binding_type == original.binding_type
        assert restored.table_name == original.table_name
        assert restored.field_name == original.field_name
        assert restored.full_binding == original.full_binding

    def test_element_dependencies_with_bindings(self):
        """Testa ElementDependencies com bound_tables."""
        deps = ElementDependencies()

        # Adiciona data_files (de código)
        deps.data_files.extend(['CLIENTE', 'PEDIDO'])

        # Adiciona bound_tables (de controles)
        deps.add_bound_table('CLIENTE')  # duplicado
        deps.add_bound_table('PRODUTO')  # novo

        # Verifica que bound_tables é independente de data_files
        assert len(deps.data_files) == 2
        assert len(deps.bound_tables) == 2

        # Verifica que não há duplicatas em bound_tables
        deps.add_bound_table('PRODUTO')
        assert len(deps.bound_tables) == 2
