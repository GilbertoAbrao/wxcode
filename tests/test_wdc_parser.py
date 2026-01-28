"""
Testes do WdcParser.
"""

import pytest
import tempfile
from pathlib import Path

from wxcode.parser.wdc_parser import WdcParser, ParsedClass


# Fixture: Classe simples
SIMPLE_CLASS_WDC = """#To edit and compare internal_properties, use WINDEV integrated tools.
info :
 name : TestClass
 type : 4
class :
 identifier : 0x123456789
 code_elements :
  type_code : 10
  p_codes :
   -
     code : |1+
      TestClass is a Class

      	Nome is string
      	Idade is int = 0

      end
     type : 131072
 procedures :
  -
    name : GetNome
    type_code : 12
    code : |1+
     procedure GetNome(): string

     RESULT Nome
"""

# Fixture: Classe com herança
INHERITED_CLASS_WDC = """#To edit and compare internal_properties, use WINDEV integrated tools.
info :
 name : ChildClass
 type : 4
class :
 identifier : 0x987654321
 code_elements :
  type_code : 10
  p_codes :
   -
     code : |1+
      ChildClass is a Class

      	inherits ParentClass

      	PUBLIC
      	PublicField is string

      	PRIVATE
      	PrivateField is int

      	PROTECTED
      	ProtectedField is boolean = True

      end
     type : 131072
 procedures :
  -
    name : Constructor
    type_code : 27
    code : |1+
     procedure Constructor()

  -
    name : Destructor
    type_code : 28
    code : |1+
     procedure Destructor()

  -
    name : ProtectedMethod
    type_code : 12
    code : |1+
     procedure protected ProtectedMethod(): string

     RESULT ""
"""

# Fixture: Classe abstrata
ABSTRACT_CLASS_WDC = """#To edit and compare internal_properties, use WINDEV integrated tools.
info :
 name : AbstractBase
 type : 4
class :
 identifier : 0xabc123def
 code_elements :
  type_code : 10
  p_codes :
   -
     code : |1+
      AbstractBase is a Class, abstract

      	Id is int

      end
     type : 131072
 procedures :
  -
    name : Save
    type_code : 12
    code : |1+
     procedure public Save(): boolean

     RESULT True
"""


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_wdc_file(temp_dir):
    """Cria arquivo .wdc com classe simples."""
    wdc_path = temp_dir / "TestClass.wdc"
    wdc_path.write_text(SIMPLE_CLASS_WDC, encoding="iso-8859-1")
    return wdc_path


@pytest.fixture
def inherited_wdc_file(temp_dir):
    """Cria arquivo .wdc com herança."""
    wdc_path = temp_dir / "ChildClass.wdc"
    wdc_path.write_text(INHERITED_CLASS_WDC, encoding="iso-8859-1")
    return wdc_path


@pytest.fixture
def abstract_wdc_file(temp_dir):
    """Cria arquivo .wdc com classe abstrata."""
    wdc_path = temp_dir / "AbstractBase.wdc"
    wdc_path.write_text(ABSTRACT_CLASS_WDC, encoding="iso-8859-1")
    return wdc_path


class TestWdcParserInit:
    """Testes de inicialização do parser."""

    def test_init_with_valid_file(self, simple_wdc_file):
        """Deve inicializar com arquivo válido."""
        parser = WdcParser(simple_wdc_file)
        assert parser.wdc_path == simple_wdc_file

    def test_init_with_nonexistent_file(self, temp_dir):
        """Deve lançar FileNotFoundError com arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            WdcParser(temp_dir / "nonexistent.wdc")

    def test_init_with_wrong_extension(self, temp_dir):
        """Deve lançar ValueError com extensão errada."""
        wrong_file = temp_dir / "test.txt"
        wrong_file.write_text("test")
        with pytest.raises(ValueError):
            WdcParser(wrong_file)


class TestClassDefinition:
    """Testes de parsing da definição da classe."""

    def test_parse_class_name(self, simple_wdc_file):
        """Deve extrair nome da classe."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()
        assert result.name == "TestClass"

    def test_parse_identifier(self, simple_wdc_file):
        """Deve extrair identifier."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()
        assert result.identifier == "0x123456789"

    def test_parse_abstract_class(self, abstract_wdc_file):
        """Deve detectar classe abstrata."""
        parser = WdcParser(abstract_wdc_file)
        result = parser.parse()
        assert result.is_abstract is True
        assert result.name == "AbstractBase"

    def test_parse_non_abstract_class(self, simple_wdc_file):
        """Deve detectar classe não-abstrata."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()
        assert result.is_abstract is False

    def test_parse_inheritance(self, inherited_wdc_file):
        """Deve detectar herança."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()
        assert result.inherits_from == "ParentClass"

    def test_parse_no_inheritance(self, simple_wdc_file):
        """Deve detectar ausência de herança."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()
        assert result.inherits_from is None


class TestMembers:
    """Testes de parsing de membros."""

    def test_parse_simple_members(self, simple_wdc_file):
        """Deve extrair membros simples."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()

        assert len(result.members) == 2
        assert result.members[0].name == "Nome"
        assert result.members[0].type == "string"
        assert result.members[0].visibility == "public"

    def test_parse_member_with_default(self, simple_wdc_file):
        """Deve extrair valor padrão."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()

        idade_member = [m for m in result.members if m.name == "Idade"][0]
        assert idade_member.default_value == "0"

    def test_parse_visibility_blocks(self, inherited_wdc_file):
        """Deve respeitar blocos de visibilidade."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        assert len(result.members) == 3

        public_member = [m for m in result.members if m.name == "PublicField"][0]
        assert public_member.visibility == "public"

        private_member = [m for m in result.members if m.name == "PrivateField"][0]
        assert private_member.visibility == "private"

        protected_member = [m for m in result.members if m.name == "ProtectedField"][0]
        assert protected_member.visibility == "protected"
        assert protected_member.default_value == "True"


class TestMethods:
    """Testes de parsing de métodos."""

    def test_parse_method(self, simple_wdc_file):
        """Deve extrair método normal."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()

        assert len(result.methods) == 1
        assert result.methods[0].name == "GetNome"
        assert result.methods[0].method_type == "method"
        assert result.methods[0].return_type == "string"

    def test_parse_constructor(self, inherited_wdc_file):
        """Deve identificar Constructor."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        constructor = [m for m in result.methods if m.name == "Constructor"][0]
        assert constructor.method_type == "constructor"
        assert constructor.type_code == 27

    def test_parse_destructor(self, inherited_wdc_file):
        """Deve identificar Destructor."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        destructor = [m for m in result.methods if m.name == "Destructor"][0]
        assert destructor.method_type == "destructor"
        assert destructor.type_code == 28

    def test_parse_method_visibility(self, inherited_wdc_file):
        """Deve extrair visibilidade de métodos."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        protected_method = [m for m in result.methods if m.name == "ProtectedMethod"][0]
        assert protected_method.visibility == "protected"

    def test_parse_method_code_lines(self, abstract_wdc_file):
        """Deve contar linhas de código."""
        parser = WdcParser(abstract_wdc_file)
        result = parser.parse()

        save_method = [m for m in result.methods if m.name == "Save"][0]
        assert save_method.code_lines > 0


class TestDependencies:
    """Testes de extração de dependências."""

    def test_extract_inheritance_dependency(self, inherited_wdc_file):
        """Deve adicionar classe pai às dependências."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        assert "ParentClass" in result.dependencies.uses_classes

    def test_no_dependencies_for_simple_class(self, simple_wdc_file):
        """Deve não ter dependências em classe simples."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()

        assert len(result.dependencies.uses_classes) == 0
        assert len(result.dependencies.uses_files) == 0


class TestProperties:
    """Testes de propriedades calculadas."""

    def test_total_members(self, inherited_wdc_file):
        """Deve calcular total de membros."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        assert result.total_members == 3

    def test_total_methods(self, inherited_wdc_file):
        """Deve calcular total de métodos."""
        parser = WdcParser(inherited_wdc_file)
        result = parser.parse()

        assert result.total_methods == 3

    def test_total_code_lines(self, abstract_wdc_file):
        """Deve calcular total de linhas de código."""
        parser = WdcParser(abstract_wdc_file)
        result = parser.parse()

        assert result.total_code_lines > 0


class TestEncoding:
    """Testes de encoding."""

    def test_parse_iso_8859_1(self, simple_wdc_file):
        """Deve ler arquivo em ISO-8859-1."""
        parser = WdcParser(simple_wdc_file)
        result = parser.parse()

        assert result.name == "TestClass"
