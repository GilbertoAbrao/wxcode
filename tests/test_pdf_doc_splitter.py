"""
Testes para o PDF Documentation Splitter.
"""

import json
from pathlib import Path

import pytest

from wxcode.parser.pdf_doc_splitter import (
    PDFDocumentSplitter,
    ElementType,
    PDFElement,
    ProcessingStats,
    split_documentation_pdf,
)


class TestElementType:
    """Testes para ElementType."""

    def test_element_type_values(self):
        """Testa valores do enum."""
        assert ElementType.PAGE.value == "page"
        assert ElementType.REPORT.value == "report"
        assert ElementType.WINDOW.value == "window"
        assert ElementType.INTERNAL_WINDOW.value == "internal_window"
        assert ElementType.UNKNOWN.value == "unknown"


class TestPDFElement:
    """Testes para PDFElement."""

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        element = PDFElement(
            name="PAGE_Login",
            element_type=ElementType.PAGE,
            source_page=10,
            end_page=15,
            screenshot_page=11
        )

        result = element.to_dict()

        assert result["name"] == "PAGE_Login"
        assert result["element_type"] == "page"
        assert result["source_page"] == 10
        assert result["end_page"] == 15
        assert result["screenshot_page"] == 11

    def test_to_dict_without_screenshot(self):
        """Testa conversão sem screenshot."""
        element = PDFElement(
            name="RPT_Extrato",
            element_type=ElementType.REPORT,
            source_page=100,
            end_page=105
        )

        result = element.to_dict()

        assert result["screenshot_page"] is None


class TestProcessingStats:
    """Testes para ProcessingStats."""

    def test_default_values(self):
        """Testa valores padrão."""
        stats = ProcessingStats()

        assert stats.total_pages == 0
        assert stats.pages_processed == 0
        assert stats.elements_found == 0
        assert stats.pages_extracted == 0
        assert stats.reports_extracted == 0
        assert stats.windows_extracted == 0
        assert stats.errors == []
        assert stats.processing_time_seconds == 0

    def test_processing_time_calculation(self):
        """Testa cálculo do tempo de processamento."""
        stats = ProcessingStats()
        stats.start_time = 100.0
        stats.end_time = 125.5

        assert stats.processing_time_seconds == 25.5


class TestPDFDocumentSplitter:
    """Testes para PDFDocumentSplitter."""

    @pytest.fixture
    def sample_pdf(self) -> Path:
        """PDF de exemplo para testes."""
        return Path("project-refs/Linkpay_ADM/Documentation_Linkpay_ADM.pdf")

    def test_init_with_invalid_path(self, tmp_path: Path):
        """Testa inicialização com caminho inválido."""
        with pytest.raises(FileNotFoundError):
            PDFDocumentSplitter(
                pdf_path=tmp_path / "nao_existe.pdf",
                output_dir=tmp_path / "output"
            )

    def test_detect_element_title_page(self):
        """Testa detecção de títulos de página."""
        # Cria instância sem chamar __init__ para testar apenas o método
        splitter = object.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS
        splitter.IGNORE_TEXTS = PDFDocumentSplitter.IGNORE_TEXTS

        assert splitter._detect_element_title("PAGE_Login") == ElementType.PAGE
        assert splitter._detect_element_title("FORM_Cliente") == ElementType.PAGE
        assert splitter._detect_element_title("LIST_Pedidos") == ElementType.PAGE
        assert splitter._detect_element_title("DASHBOARD_Admin") == ElementType.PAGE
        assert splitter._detect_element_title("POPUP_Confirmacao") == ElementType.PAGE
        assert splitter._detect_element_title("MENU_Principal") == ElementType.PAGE

    def test_detect_element_title_report(self):
        """Testa detecção de títulos de relatório."""
        splitter = object.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS
        splitter.IGNORE_TEXTS = PDFDocumentSplitter.IGNORE_TEXTS

        assert splitter._detect_element_title("RPT_Extrato") == ElementType.REPORT
        assert splitter._detect_element_title("ETAT_Fatura") == ElementType.REPORT
        assert splitter._detect_element_title("REL_Vendas") == ElementType.REPORT
        assert splitter._detect_element_title("REPORT_Mensal") == ElementType.REPORT

    def test_detect_element_title_window(self):
        """Testa detecção de títulos de janela."""
        splitter = object.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS
        splitter.IGNORE_TEXTS = PDFDocumentSplitter.IGNORE_TEXTS

        assert splitter._detect_element_title("WIN_Principal") == ElementType.WINDOW
        assert splitter._detect_element_title("FEN_Config") == ElementType.WINDOW
        assert splitter._detect_element_title("WINDOW_Login") == ElementType.WINDOW

    def test_detect_element_title_internal_window(self):
        """Testa detecção de títulos de janela interna."""
        splitter = object.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS
        splitter.IGNORE_TEXTS = PDFDocumentSplitter.IGNORE_TEXTS

        assert splitter._detect_element_title("IW_Detalhe") == ElementType.INTERNAL_WINDOW
        assert splitter._detect_element_title("FI_Lista") == ElementType.INTERNAL_WINDOW

    def test_detect_element_title_invalid(self):
        """Testa que textos inválidos não são detectados."""
        splitter = object.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS
        splitter.IGNORE_TEXTS = PDFDocumentSplitter.IGNORE_TEXTS

        # Textos ignorados
        assert splitter._detect_element_title("Image") is None
        assert splitter._detect_element_title("Part 2: Page") is None
        assert splitter._detect_element_title("Table of Contents") is None
        assert splitter._detect_element_title("Project") is None
        assert splitter._detect_element_title("Summary") is None

        # Textos muito curtos ou longos
        assert splitter._detect_element_title("ab") is None
        assert splitter._detect_element_title("a" * 101) is None

        # Textos que não seguem o padrão
        assert splitter._detect_element_title("AlgumaCoisa") is None
        assert splitter._detect_element_title("page_login") is None  # minúsculo

    def test_create_output_dirs(self, tmp_path: Path):
        """Testa criação de diretórios de saída."""
        splitter = object.__new__(PDFDocumentSplitter)
        splitter.output_dir = tmp_path / "output"

        splitter._create_output_dirs()

        assert (tmp_path / "output" / "pages").is_dir()
        assert (tmp_path / "output" / "reports").is_dir()
        assert (tmp_path / "output" / "windows").is_dir()


class TestSplitDocumentationPDF:
    """Testes de integração para split_documentation_pdf."""

    @pytest.fixture
    def sample_pdf(self) -> Path:
        """PDF de exemplo para testes."""
        return Path("project-refs/Linkpay_ADM/Documentation_Linkpay_ADM.pdf")

    def test_process_real_pdf(self, sample_pdf: Path, tmp_path: Path):
        """Testa processamento de PDF real."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        result = split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=20  # Batch menor para teste mais rápido
        )

        # Verifica estrutura do resultado
        assert "source_pdf" in result
        assert "elements" in result
        assert "stats" in result
        assert "total_pages" in result
        assert "processed_at" in result

        # Verifica estrutura de elements
        assert "pages" in result["elements"]
        assert "reports" in result["elements"]
        assert "windows" in result["elements"]

        # Verifica estatísticas
        assert result["stats"]["total_elements"] >= 0
        assert result["stats"]["processing_time_seconds"] > 0

        # Verifica que criou arquivos
        assert (tmp_path / "manifest.json").exists()
        assert (tmp_path / "pages").is_dir()
        assert (tmp_path / "reports").is_dir()
        assert (tmp_path / "windows").is_dir()

        # Verifica conteúdo do manifest
        with open(tmp_path / "manifest.json") as f:
            manifest = json.load(f)
            assert manifest == result

    def test_process_with_progress(self, sample_pdf: Path, tmp_path: Path):
        """Testa callback de progresso."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        progress_calls: list[tuple[int, int]] = []

        def on_progress(done: int, total: int) -> None:
            progress_calls.append((done, total))

        split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=10,
            on_progress=on_progress
        )

        # Deve ter chamado o callback várias vezes
        assert len(progress_calls) > 0

        # Último call deve ter done == total
        last_done, last_total = progress_calls[-1]
        assert last_done == last_total

        # Valores devem ser crescentes
        for i in range(1, len(progress_calls)):
            assert progress_calls[i][0] >= progress_calls[i - 1][0]

    def test_manifest_structure(self, sample_pdf: Path, tmp_path: Path):
        """Testa estrutura do manifest gerado."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        result = split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=50
        )

        # Verifica estrutura completa do stats
        assert "total_elements" in result["stats"]
        assert "pages" in result["stats"]
        assert "reports" in result["stats"]
        assert "windows" in result["stats"]
        assert "processing_time_seconds" in result["stats"]
        assert "errors" in result["stats"]

        # Verifica que errors é uma lista
        assert isinstance(result["stats"]["errors"], list)

        # Se encontrou elementos, verifica estrutura
        if result["elements"]["pages"]:
            page = result["elements"]["pages"][0]
            assert "name" in page
            assert "pdf_file" in page
            assert "source_page" in page
            assert "has_screenshot" in page

            # source_page deve ser 1-indexed (para humanos)
            assert page["source_page"] >= 1

    def test_extracted_pdfs_exist(self, sample_pdf: Path, tmp_path: Path):
        """Testa que os PDFs extraídos existem."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        result = split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=50
        )

        # Verifica que cada PDF listado existe
        for page in result["elements"]["pages"]:
            pdf_path = tmp_path / page["pdf_file"]
            assert pdf_path.exists(), f"PDF não encontrado: {pdf_path}"

        for report in result["elements"]["reports"]:
            pdf_path = tmp_path / report["pdf_file"]
            assert pdf_path.exists(), f"PDF não encontrado: {pdf_path}"

        for window in result["elements"]["windows"]:
            pdf_path = tmp_path / window["pdf_file"]
            assert pdf_path.exists(), f"PDF não encontrado: {pdf_path}"
