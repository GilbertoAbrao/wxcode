"""
Parser para extrair propriedades visuais dos PDFs de documentação.

Extrai propriedades como dimensões, posição, estilo, etc.
NÃO é fonte de tipos de controles - isso vem do WWHParser.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import fitz  # PyMuPDF

from wxcode.models.control import DataBindingInfo, DataBindingType


@dataclass
class ParsedPDFElement:
    """Resultado do parsing de um PDF de elemento."""
    element_name: str
    general_properties: dict[str, Any] = field(default_factory=dict)
    control_properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    screenshot_path: Optional[str] = None
    total_pages: int = 0
    raw_text: str = ""


class PDFElementParser:
    """
    Extrai propriedades VISUAIS dos PDFs de documentação.

    Não é fonte de tipos - apenas propriedades como dimensões, posição, estilo.
    """

    # Padrões para identificar nomes de controles
    # Aceita: POPUP_ITEM, Popup_AlterarBoleto, EDT_NOME
    CONTROL_NAME_PATTERN = re.compile(
        r'^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*$'
    )

    # Padrões para extrair informação de DataBinding
    # Suporta: inglês, francês, português
    BINDING_PATTERNS = [
        re.compile(r"Linked\s+item\s*[:\-]\s*(.+)", re.IGNORECASE),
        re.compile(r"File\s+link\s*[:\-]\s*(.+)", re.IGNORECASE),
        re.compile(r"Rubrique\s+fichier\s*[:\-]\s*(.+)", re.IGNORECASE),  # Francês
        re.compile(r"Binding\s*[:\-]\s*(.+)", re.IGNORECASE),
        re.compile(r"Item\s+li[ée]\s*[:\-]\s*(.+)", re.IGNORECASE),  # Francês alt
        re.compile(r"Data\s*binding\s*[:\-]\s*(.+)", re.IGNORECASE),
    ]

    # Propriedades conhecidas para parsing
    KNOWN_PROPERTIES = {
        'Height', 'Width', 'X position', 'Y position',
        'Visible', 'Enabled', 'Style', 'Tooltip', 'HTMLClass',
        'Input type', 'Tab order', 'Caption', 'Hint text if empty',
        'Required input', 'Anchor', 'Plane(s) containing the control',
        'Mode', 'Border', 'Group', 'Alias', 'Note',
        # Propriedades de binding
        'Linked item', 'File link', 'Rubrique fichier', 'Binding',
        'Data binding', 'Item lié',
    }

    def __init__(self, pdf_path: Path):
        """
        Inicializa o parser.

        Args:
            pdf_path: Caminho para o PDF do elemento
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    def parse(self, screenshots_dir: Optional[Path] = None) -> ParsedPDFElement:
        """
        Parseia o PDF e extrai propriedades.

        Args:
            screenshots_dir: Diretório para salvar screenshots (opcional)

        Returns:
            ParsedPDFElement com propriedades extraídas
        """
        doc = fitz.open(self.pdf_path)

        try:
            # Extrai todo o texto
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"

            # Nome do elemento
            element_name = self.pdf_path.stem

            result = ParsedPDFElement(
                element_name=element_name,
                total_pages=len(doc),
                raw_text=full_text
            )

            # Parseia o texto
            self._parse_text(full_text, result)

            # Extrai screenshot se solicitado
            if screenshots_dir:
                result.screenshot_path = self._extract_screenshot(
                    doc, screenshots_dir, element_name
                )

            return result

        finally:
            doc.close()

    def _parse_text(self, text: str, result: ParsedPDFElement):
        """
        Parseia o texto do PDF e extrai propriedades.

        Args:
            text: Texto completo do PDF
            result: Objeto para preencher
        """
        lines = text.split('\n')
        current_section = None  # 'general' ou 'controls'
        current_control = None
        current_properties: dict[str, Any] = {}
        current_control_text: list[str] = []  # Acumula texto do controle para binding

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Detecta seção
            if 'General information' in line:
                current_section = 'general'
                current_control = None
                i += 1
                continue

            if 'Information on controls' in line:
                current_section = 'controls'
                i += 1
                continue

            # Ignora linhas irrelevantes
            if self._is_header_line(line):
                i += 1
                continue

            # Detecta novo controle
            if current_section == 'controls':
                if self._is_control_name(line):
                    # Salva controle anterior com binding extraído
                    if current_control and current_properties:
                        # Tenta extrair binding do texto acumulado
                        control_text = '\n'.join(current_control_text)
                        binding = self._extract_binding(control_text)
                        if binding:
                            current_properties['_data_binding'] = binding
                        result.control_properties[current_control] = current_properties.copy()

                    current_control = line
                    current_properties = {}
                    current_control_text = [line]  # Inicia novo bloco
                    i += 1
                    continue

            # Acumula texto do controle atual
            if current_control and line:
                current_control_text.append(line)

            # Parseia propriedade
            if line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # Verifica se é par chave/valor
                # IMPORTANTE: Não tratar next_line como valor se for nome de controle
                # Isso evita que controles sejam "consumidos" como valores de propriedades
                if (self._is_property_name(line) and
                    not self._is_property_name(next_line) and
                    not self._is_control_name(next_line)):
                    value = self._parse_property_value(next_line)

                    if current_section == 'general':
                        result.general_properties[line] = value
                    elif current_control:
                        current_properties[line] = value
                        # Acumula também a próxima linha
                        current_control_text.append(next_line)

                    i += 2
                    continue

            i += 1

        # Salva último controle com binding
        if current_control and current_properties:
            control_text = '\n'.join(current_control_text)
            binding = self._extract_binding(control_text)
            if binding:
                current_properties['_data_binding'] = binding
            result.control_properties[current_control] = current_properties

    def _is_header_line(self, line: str) -> bool:
        """Verifica se é linha de cabeçalho a ignorar."""
        ignore_patterns = [
            'Part 2', 'Part 3', 'Page ›', 'Window ›', 'Report ›',
            'Linkpay_ADM', '/2025', '/2024', '/2026',
        ]
        return any(p in line for p in ignore_patterns)

    def _is_control_name(self, line: str) -> bool:
        """Verifica se a linha é um nome de controle."""
        if not line or len(line) < 3 or len(line) > 150:
            return False

        # Ignora valores comuns
        if line in {'Yes', 'No', 'BR', 'True', 'False', 'Image'}:
            return False

        # Padrões comuns de nomes de controles
        prefixes = [
            'EDT_', 'BTN_', 'CELL_', 'IMG_', 'TBL_', 'LAB_', 'STC_',
            'CHK_', 'RBT_', 'CMB_', 'LST_', 'TAB_', 'MENU_', 'ZONE_',
            'LOOP_', 'POPUP_', 'Popup_', 'Popup', 'LNK_', 'CHART_', 'RTA_',
            'PAGE_', 'FORM_', 'LIST_', 'DASHBOARD_', 'RADIO_', 'COL_',
            'TABLE_', 'Table_', 'ComboBox_', 'CBOX_',
        ]

        # Verifica prefixo direto
        if any(line.startswith(p) for p in prefixes):
            return True

        # Verifica formato PARENT.CHILD onde CHILD tem prefixo conhecido
        if '.' in line:
            parts = line.split('.')
            last_part = parts[-1]
            if any(last_part.startswith(p) for p in prefixes):
                return True

        return False

    def _is_property_name(self, line: str) -> bool:
        """Verifica se a linha parece ser um nome de propriedade."""
        if not line or len(line) > 50:
            return False

        # Propriedade conhecida
        if line in self.KNOWN_PROPERTIES:
            return True

        # Padrões de propriedades
        # - Começa com maiúscula
        # - Não é um valor simples
        # - Contém espaços (geralmente propriedades têm)
        if line[0].isupper() and line not in {'Yes', 'No', 'BR', 'True', 'False'}:
            # Não é número
            try:
                float(line)
                return False
            except ValueError:
                pass

            # Provavelmente é propriedade
            return True

        return False

    def _parse_property_value(self, value: str) -> Any:
        """Converte string de valor para tipo apropriado."""
        if not value:
            return None

        # Valores especiais
        if value == 'Yes':
            return True
        if value == 'No':
            return False
        if value == 'BR' or value == '<Undefined>':
            return None

        # Números
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value

    def _extract_binding(self, text: str) -> Optional[DataBindingInfo]:
        """
        Extrai informação de DataBinding do texto.

        Args:
            text: Texto do bloco do controle

        Returns:
            DataBindingInfo se encontrado, None caso contrário
        """
        for pattern in self.BINDING_PATTERNS:
            match = pattern.search(text)
            if match:
                raw_value = match.group(1).strip()
                # Limpa valor (remove quebras de linha, espaços extras)
                raw_value = re.sub(r'\s+', ' ', raw_value).strip()
                if raw_value and raw_value not in {'None', '<None>', '<Undefined>', ''}:
                    return self._parse_binding_value(raw_value)
        return None

    def _parse_binding_value(self, value: str) -> DataBindingInfo:
        """
        Parseia o valor de binding extraído do PDF.

        Args:
            value: Valor bruto do binding (ex: "CLIENTE.nome", ":gsVariavel")

        Returns:
            DataBindingInfo configurado corretamente
        """
        value = value.strip()

        # Binding com variável: começa com ':'
        if value.startswith(':'):
            return DataBindingInfo(
                binding_type=DataBindingType.VARIABLE,
                variable_name=value[1:].strip(),
                source="pdf",
                raw_value=value
            )

        # Binding simples: TABLE.FIELD (sem espaços, com ponto)
        if '.' in value and ' ' not in value:
            parts = value.split('.', 1)
            return DataBindingInfo(
                binding_type=DataBindingType.SIMPLE,
                table_name=parts[0].strip(),
                field_name=parts[1].strip(),
                source="pdf",
                raw_value=value
            )

        # Binding complexo: caminho com múltiplas partes ou espaços
        # Ex: "PEDIDO via CLIENTE.nome"
        parts = re.split(r'[\s.]+', value)
        if len(parts) >= 2:
            return DataBindingInfo(
                binding_type=DataBindingType.COMPLEX,
                binding_path=[p.strip() for p in parts if p.strip()],
                source="pdf",
                raw_value=value
            )

        # Fallback: assume simples sem campo
        return DataBindingInfo(
            binding_type=DataBindingType.SIMPLE,
            table_name=value,
            source="pdf",
            raw_value=value
        )

    def _extract_screenshot(
        self,
        doc: fitz.Document,
        output_dir: Path,
        element_name: str
    ) -> Optional[str]:
        """
        Extrai primeira imagem do PDF como screenshot.

        Args:
            doc: Documento PDF
            output_dir: Diretório de saída
            element_name: Nome do elemento para o arquivo

        Returns:
            Caminho do screenshot ou None
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Procura primeira imagem significativa
        for page_num in range(min(3, len(doc))):  # Primeiras 3 páginas
            page = doc[page_num]
            images = page.get_images()

            for img_idx, img in enumerate(images):
                xref = img[0]

                try:
                    base_image = doc.extract_image(xref)
                    if base_image:
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Ignora imagens muito pequenas (ícones)
                        if len(image_bytes) < 5000:
                            continue

                        output_path = output_dir / f"{element_name}.{image_ext}"
                        with open(output_path, "wb") as f:
                            f.write(image_bytes)

                        return str(output_path)
                except Exception:
                    continue

        return None


def parse_pdf_element(
    pdf_path: Path,
    screenshots_dir: Optional[Path] = None
) -> ParsedPDFElement:
    """
    Função de conveniência para parsear PDF de elemento.

    Args:
        pdf_path: Caminho para o PDF
        screenshots_dir: Diretório para screenshots

    Returns:
        ParsedPDFElement com propriedades
    """
    parser = PDFElementParser(pdf_path)
    return parser.parse(screenshots_dir)
