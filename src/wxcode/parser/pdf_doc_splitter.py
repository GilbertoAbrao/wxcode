"""
PDF Documentation Splitter para projetos WebDev.

Processa PDFs de documentação grandes (3000+ páginas) em batches
e extrai cada elemento (Page, Report, Window) para um PDF individual.
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional

import fitz  # PyMuPDF


class ElementType(Enum):
    """Tipos de elementos do PDF."""
    PAGE = "page"
    REPORT = "report"
    WINDOW = "window"
    INTERNAL_WINDOW = "internal_window"
    QUERY = "query"
    UNKNOWN = "unknown"


@dataclass
class PDFElement:
    """Representa um elemento extraído do PDF."""
    name: str
    element_type: ElementType
    source_page: int
    end_page: int  # Página final (pode ter múltiplas páginas)
    screenshot_page: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "element_type": self.element_type.value,
            "source_page": self.source_page,
            "end_page": self.end_page,
            "screenshot_page": self.screenshot_page
        }


@dataclass
class ProcessingStats:
    """Estatísticas de processamento."""
    total_pages: int = 0
    pages_processed: int = 0
    elements_found: int = 0
    pages_extracted: int = 0
    reports_extracted: int = 0
    windows_extracted: int = 0
    queries_extracted: int = 0
    errors: list = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    @property
    def processing_time_seconds(self) -> float:
        """Retorna o tempo de processamento em segundos."""
        return self.end_time - self.start_time if self.end_time else 0


class PDFDocumentSplitter:
    """
    Processa PDF de documentação WebDev e extrai elementos individuais.

    Suporta PDFs grandes (3000+ páginas) através de processamento em batches.
    """

    # Padrões para identificar início de seções (Parts)
    # Suporta ambos formatos: "Part 2: Page" e "Part 2 › Page"
    PART_PATTERNS = {
        "Part 2: Page": ElementType.PAGE,
        "Part 2 › Page": ElementType.PAGE,
        "Part 2: Window": ElementType.WINDOW,
        "Part 2 › Window": ElementType.WINDOW,
        "Part 2: Internal window": ElementType.INTERNAL_WINDOW,
        "Part 2 › Internal window": ElementType.INTERNAL_WINDOW,
        "Part 3: Report": ElementType.REPORT,
        "Part 3 › Report": ElementType.REPORT,
        "Part 4: Query": ElementType.QUERY,
        "Part 4 › Query": ElementType.QUERY,
    }

    # Padrões para identificar títulos de elementos
    # NOTA: POPUPs, ZONEs, MENUs, TABs e outros containers NÃO são elementos.
    # Eles são controles dentro de páginas e seus dados estão no PDF da página pai.
    # Por isso não devem gerar PDFs separados.
    ELEMENT_TITLE_PATTERNS = [
        # Pages (elementos reais que aparecem no .wwp)
        (r'^PAGE_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^FORM_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^LIST_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^DASHBOARD_[A-Za-z0-9_]+$', ElementType.PAGE),
        # Reports
        (r'^RPT_[A-Za-z0-9_]+$', ElementType.REPORT),
        (r'^ETAT_[A-Za-z0-9_]+$', ElementType.REPORT),
        (r'^REL_[A-Za-z0-9_]+$', ElementType.REPORT),
        (r'^REPORT_[A-Za-z0-9_]+$', ElementType.REPORT),
        # Windows
        (r'^WIN_[A-Za-z0-9_]+$', ElementType.WINDOW),
        (r'^FEN_[A-Za-z0-9_]+$', ElementType.WINDOW),
        (r'^WINDOW_[A-Za-z0-9_]+$', ElementType.WINDOW),
        # Internal Windows
        (r'^IW_[A-Za-z0-9_]+$', ElementType.INTERNAL_WINDOW),
        (r'^FI_[A-Za-z0-9_]+$', ElementType.INTERNAL_WINDOW),
        # Queries
        (r'^QRY_[A-Za-z0-9_]+$', ElementType.QUERY),
        (r'^Migration_[A-Za-z0-9_]+$', ElementType.QUERY),
        (r'^Migrations_[A-Za-z0-9_]+$', ElementType.QUERY),
    ]

    # Textos a ignorar como títulos de elementos
    IGNORE_TEXTS = {
        'Image', 'Part', 'Table of Contents', 'Project',
        'Summary', 'Index', 'Contents', 'General', 'Properties',
        'Description', 'Code', 'Events', 'Controls', 'Processes',
    }

    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path,
        batch_size: int = 50,
        on_progress: Optional[callable] = None,
        known_elements: Optional[dict[str, str]] = None
    ):
        """
        Inicializa o splitter.

        Args:
            pdf_path: Caminho para o PDF de documentação
            output_dir: Diretório de saída para os PDFs extraídos
            batch_size: Número de páginas por batch (padrão: 50)
            on_progress: Callback para progresso (recebe: pages_done, total_pages)
            known_elements: Dict de elementos conhecidos {nome: source_type}.
                           Se fornecido, usa esses nomes em vez de padrões regex.
                           Exemplo: {"ESPELHO_CONTA_FITBANK": "page", "PAGE_Login": "page"}
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self.on_progress = on_progress
        self.known_elements = known_elements or {}

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        self.stats = ProcessingStats()
        self.elements: list[PDFElement] = []
        self._current_section: Optional[ElementType] = None

    def process(self) -> dict:
        """
        Processa o PDF completo em batches.

        Returns:
            Dicionário com manifest e estatísticas
        """
        self.stats.start_time = time.time()

        # Cria diretórios de saída
        self._create_output_dirs()

        # Abre o PDF
        doc = fitz.open(self.pdf_path)
        self.stats.total_pages = len(doc)

        try:
            # Processa em batches
            for batch_start in range(0, len(doc), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(doc))
                self._process_batch(doc, batch_start, batch_end)

                # Callback de progresso
                if self.on_progress:
                    self.on_progress(batch_end, len(doc))

            # Fecha o último elemento se ainda estiver aberto
            if self.elements and self.elements[-1].end_page == -1:
                self.elements[-1].end_page = len(doc) - 1

            # Extrai PDFs individuais para cada elemento encontrado
            self._extract_element_pdfs(doc)

        finally:
            doc.close()

        self.stats.end_time = time.time()

        # Gera manifest
        manifest = self._generate_manifest()

        return manifest

    def _create_output_dirs(self):
        """Cria estrutura de diretórios de saída."""
        (self.output_dir / "pages").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "windows").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "queries").mkdir(parents=True, exist_ok=True)

    def _process_batch(self, doc: fitz.Document, start: int, end: int):
        """
        Processa um batch de páginas.

        Args:
            doc: Documento PDF
            start: Página inicial (0-indexed)
            end: Página final (exclusive)
        """
        for page_num in range(start, end):
            page = doc[page_num]
            text = page.get_text().strip()
            lines = text.split('\n')

            self._analyze_page(page_num, lines)
            self.stats.pages_processed = page_num + 1

    def _analyze_page(self, page_num: int, lines: list[str]):
        """
        Analisa uma página do PDF.

        Args:
            page_num: Número da página (0-indexed)
            lines: Linhas de texto da página
        """
        # Extrai elemento do breadcrumb (linha 0) para evitar falsos positivos
        # Formato: "Part 2 › Page › ELEMENT_NAME › Section"
        breadcrumb_element = None
        if lines and ' › ' in lines[0]:
            parts = lines[0].split(' › ')
            if len(parts) >= 3:
                breadcrumb_element = parts[2].strip()

        for i, line in enumerate(lines):
            line = line.strip()

            # Verifica se é início de uma seção (Part)
            for part_name, element_type in self.PART_PATTERNS.items():
                if part_name in line:
                    self._current_section = element_type
                    break

            # Verifica se chegou em "Part 4: Table of Contents" ou similar (fim dos elementos)
            if "Table of Contents" in line or "Part 4:" in line or "Part 4 ›" in line:
                self._current_section = None

            # Ignora se não estamos em uma seção de elementos
            if self._current_section is None:
                continue

            # Verifica se é um título de elemento
            element_type = self._detect_element_title(line)
            if element_type:
                # Se o último elemento tem o mesmo nome, é continuação (não novo elemento)
                # Isso acontece quando o nome aparece no cabeçalho de páginas subsequentes
                if self.elements and self.elements[-1].name == line:
                    continue

                # Se o breadcrumb mostra um elemento diferente do detectado,
                # então o nome detectado é apenas um valor/referência, não um novo elemento
                # Ex: Query QRY_X aparece como valor de Caption de uma tabela dentro de PAGE_Y
                if breadcrumb_element and breadcrumb_element != line:
                    continue

                # Verifica se próxima linha é "Image"
                has_image = (i + 1 < len(lines) and
                            lines[i + 1].strip() == 'Image')

                # Fecha elemento anterior se existir
                if self.elements and self.elements[-1].end_page == -1:
                    self.elements[-1].end_page = page_num - 1
                    # Garante que end_page não seja menor que source_page
                    if self.elements[-1].end_page < self.elements[-1].source_page:
                        self.elements[-1].end_page = self.elements[-1].source_page

                # Adiciona novo elemento
                self.elements.append(PDFElement(
                    name=line,
                    element_type=element_type,
                    source_page=page_num,
                    end_page=-1,  # Será definido quando encontrar próximo elemento
                    screenshot_page=page_num if has_image else None
                ))
                self.stats.elements_found += 1

    # Mapeamento de source_type para ElementType
    SOURCE_TYPE_MAP = {
        "page": ElementType.PAGE,
        "report": ElementType.REPORT,
        "window": ElementType.WINDOW,
        "internal_window": ElementType.INTERNAL_WINDOW,
        "query": ElementType.QUERY,
    }

    def _detect_element_title(self, text: str) -> Optional[ElementType]:
        """
        Detecta se o texto é um título de elemento.

        Prioriza elementos conhecidos (do MongoDB) sobre padrões regex.

        Args:
            text: Texto a analisar

        Returns:
            ElementType se for um título, None caso contrário
        """
        # Ignora textos muito curtos ou muito longos
        if len(text) < 3 or len(text) > 100:
            return None

        # Ignora textos comuns
        if text in self.IGNORE_TEXTS:
            return None
        if text.startswith('Part '):
            return None

        # PRIORIDADE 1: Verifica se é um elemento conhecido (do MongoDB)
        if text in self.known_elements:
            source_type = self.known_elements[text]
            return self.SOURCE_TYPE_MAP.get(source_type, ElementType.PAGE)

        # PRIORIDADE 2: Fallback para padrões regex
        for pattern, element_type in self.ELEMENT_TITLE_PATTERNS:
            if re.match(pattern, text):
                return element_type

        return None

    def _extract_element_pdfs(self, doc: fitz.Document):
        """
        Extrai PDFs individuais para cada elemento.

        Args:
            doc: Documento PDF fonte
        """
        for element in self.elements:
            try:
                self._extract_single_element(doc, element)
            except Exception as e:
                self.stats.errors.append({
                    "element": element.name,
                    "error": str(e)
                })

    def _extract_single_element(self, doc: fitz.Document, element: PDFElement):
        """
        Extrai um único elemento para PDF.

        Args:
            doc: Documento PDF fonte
            element: Elemento a extrair
        """
        # Determina diretório de saída baseado no tipo
        type_dir = {
            ElementType.PAGE: "pages",
            ElementType.REPORT: "reports",
            ElementType.WINDOW: "windows",
            ElementType.INTERNAL_WINDOW: "windows",
        }.get(element.element_type, "pages")

        output_path = self.output_dir / type_dir / f"{element.name}.pdf"

        # Cria novo PDF com as páginas do elemento
        new_doc = fitz.open()

        start_page = element.source_page
        end_page = min(element.end_page + 1, len(doc))

        # Garante que start_page e end_page são válidos
        if start_page < 0:
            start_page = 0
        if end_page > len(doc):
            end_page = len(doc)
        if start_page >= end_page:
            end_page = start_page + 1

        for page_num in range(start_page, end_page):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        new_doc.save(str(output_path))
        new_doc.close()

        # Atualiza estatísticas
        if element.element_type == ElementType.PAGE:
            self.stats.pages_extracted += 1
        elif element.element_type == ElementType.REPORT:
            self.stats.reports_extracted += 1
        elif element.element_type in [ElementType.WINDOW, ElementType.INTERNAL_WINDOW]:
            self.stats.windows_extracted += 1
        elif element.element_type == ElementType.QUERY:
            self.stats.queries_extracted += 1

    def _generate_manifest(self) -> dict:
        """
        Gera manifest.json com índice de todos os elementos.

        Returns:
            Dicionário do manifest
        """
        manifest = {
            "source_pdf": self.pdf_path.name,
            "total_pages": self.stats.total_pages,
            "processed_at": datetime.now().isoformat(),
            "elements": {
                "pages": [],
                "reports": [],
                "windows": [],
                "queries": []
            },
            "stats": {
                "total_elements": len(self.elements),
                "pages": self.stats.pages_extracted,
                "reports": self.stats.reports_extracted,
                "windows": self.stats.windows_extracted,
                "queries": self.stats.queries_extracted,
                "processing_time_seconds": round(self.stats.processing_time_seconds, 2),
                "errors": self.stats.errors
            }
        }

        # Agrupa elementos por tipo
        for element in self.elements:
            type_key = {
                ElementType.PAGE: "pages",
                ElementType.REPORT: "reports",
                ElementType.WINDOW: "windows",
                ElementType.INTERNAL_WINDOW: "windows",
                ElementType.QUERY: "queries",
            }.get(element.element_type, "pages")

            type_dir = type_key  # Mesmo nome do diretório

            manifest["elements"][type_key].append({
                "name": element.name,
                "pdf_file": f"{type_dir}/{element.name}.pdf",
                "source_page": element.source_page + 1,  # 1-indexed para humanos
                "has_screenshot": element.screenshot_page is not None
            })

        # Salva manifest
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def iter_elements(self) -> Iterator[PDFElement]:
        """
        Itera sobre os elementos encontrados.

        Yields:
            PDFElement para cada elemento encontrado
        """
        yield from self.elements


def split_documentation_pdf(
    pdf_path: Path,
    output_dir: Path,
    batch_size: int = 50,
    on_progress: Optional[callable] = None,
    known_elements: Optional[dict[str, str]] = None
) -> dict:
    """
    Função de conveniência para processar PDF de documentação.

    Args:
        pdf_path: Caminho para o PDF
        output_dir: Diretório de saída
        batch_size: Páginas por batch
        on_progress: Callback de progresso
        known_elements: Dict de elementos conhecidos {nome: source_type}.
                       Se fornecido, usa esses nomes para detectar elementos.

    Returns:
        Manifest com índice dos elementos extraídos
    """
    splitter = PDFDocumentSplitter(
        pdf_path=pdf_path,
        output_dir=output_dir,
        batch_size=batch_size,
        on_progress=on_progress,
        known_elements=known_elements
    )
    return splitter.process()
