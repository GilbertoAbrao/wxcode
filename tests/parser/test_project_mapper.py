"""Testes para ProjectElementMapper."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from wxcode.parser.project_mapper import ProjectElementMapper


class TestReadSourceFile:
    """Testes para o método _read_source_file."""

    def test_read_source_file_exists(self):
        """Deve ler arquivo existente com sucesso."""
        with TemporaryDirectory() as tmpdir:
            # Criar arquivo de teste
            test_file = Path(tmpdir) / "test.wdg"
            test_content = "// Código WLanguage de teste\nPROCEDURE Test()\nEND"
            test_file.write_text(test_content, encoding='utf-8')

            # Criar mapper apontando para o diretório temporário
            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            # Ler arquivo
            content = mapper._read_source_file(test_file)

            # Verificar conteúdo
            assert content == test_content
            assert len(content) > 0

    def test_read_source_file_missing(self):
        """Deve retornar string vazia para arquivo inexistente."""
        with TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            # Arquivo que não existe
            missing_file = Path(tmpdir) / "missing.wdg"

            # Ler arquivo inexistente
            content = mapper._read_source_file(missing_file)

            # Deve retornar string vazia
            assert content == ""

    def test_read_source_file_with_utf8_errors(self):
        """Deve substituir caracteres inválidos ao ler arquivo."""
        with TemporaryDirectory() as tmpdir:
            # Criar arquivo com bytes inválidos em UTF-8
            test_file = Path(tmpdir) / "test.wdg"
            # Escrever bytes que não são UTF-8 válido
            test_file.write_bytes(b"Valid text\xff\xfe\nMore text")

            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            # Ler arquivo - deve substituir caracteres inválidos
            content = mapper._read_source_file(test_file)

            # Deve retornar conteúdo (com caracteres substituídos)
            assert content != ""
            assert "Valid text" in content
            assert "More text" in content

    def test_read_source_file_error(self):
        """Deve retornar string vazia e logar warning em caso de erro."""
        with TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            test_file = Path(tmpdir) / "test.wdg"
            test_file.touch()

            # Mock read_text para simular exceção
            with patch.object(Path, 'read_text', side_effect=PermissionError("Access denied")):
                with patch('wxcode.parser.project_mapper.logger') as mock_logger:
                    content = mapper._read_source_file(test_file)

                    # Deve retornar string vazia
                    assert content == ""

                    # Deve ter logado warning
                    mock_logger.warning.assert_called_once()
                    warning_msg = mock_logger.warning.call_args[0][0]
                    assert "Erro ao ler" in warning_msg
                    assert str(test_file) in warning_msg

    def test_read_source_file_large_file(self):
        """Deve ler arquivo grande sem problemas."""
        with TemporaryDirectory() as tmpdir:
            # Criar arquivo grande (> 1MB)
            test_file = Path(tmpdir) / "test.wdg"
            large_content = "// Linha de código\n" * 50000  # ~800KB
            test_file.write_text(large_content, encoding='utf-8')

            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            # Ler arquivo grande
            content = mapper._read_source_file(test_file)

            # Verificar que leu todo o conteúdo
            assert content == large_content
            assert len(content) > 800_000

    def test_read_source_file_empty_file(self):
        """Deve retornar string vazia para arquivo vazio."""
        with TemporaryDirectory() as tmpdir:
            # Criar arquivo vazio
            test_file = Path(tmpdir) / "test.wdg"
            test_file.touch()

            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            # Ler arquivo vazio
            content = mapper._read_source_file(test_file)

            # Deve retornar string vazia (não None ou erro)
            assert content == ""
            assert isinstance(content, str)

    def test_read_source_file_with_special_chars(self):
        """Deve ler arquivo com caracteres especiais corretamente."""
        with TemporaryDirectory() as tmpdir:
            # Criar arquivo com caracteres especiais
            test_file = Path(tmpdir) / "test.wdg"
            test_content = "// Código com acentuação: José, André, Ação\n// Símbolos: © ® € £ ¥\n"
            test_file.write_text(test_content, encoding='utf-8')

            project_file = Path(tmpdir) / "projeto.wwp"
            project_file.touch()
            mapper = ProjectElementMapper(project_file)

            # Ler arquivo
            content = mapper._read_source_file(test_file)

            # Verificar que manteve caracteres especiais
            assert content == test_content
            assert "José" in content
            assert "André" in content
            assert "©" in content
            assert "€" in content
