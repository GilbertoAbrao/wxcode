"""
Parsers de elementos WinDev.
"""

from wxcode.parser.wwp_parser import WWPParser
from wxcode.parser.pdf_doc_splitter import (
    PDFDocumentSplitter,
    PDFElement,
    ElementType as PDFElementType,
    ProcessingStats as PDFProcessingStats,
    split_documentation_pdf,
)
from wxcode.parser.line_reader import (
    LineContext,
    read_lines,
    count_lines,
)
from wxcode.parser.project_mapper import (
    ProjectElementMapper,
    MappingStats,
    ElementInfo,
    ParserState,
    map_project_elements,
)
from wxcode.parser.xdd_parser import (
    XddParser,
    XddParseResult,
    HYPERFILE_TYPE_MAP,
    find_analysis_file,
)
from wxcode.parser.wdc_parser import (
    WdcParser,
    ParsedClass,
)
from wxcode.parser.dependency_extractor import (
    DependencyExtractor,
    ExtractedDependencies,
)
from wxcode.parser.wwh_parser import (
    WWHParser,
    ParsedPage,
    ParsedControl,
    ParsedEvent,
    ParsedLocalProcedure,
    ParsedLocalParameter,
    parse_wwh_file,
)

__all__ = [
    # WWP Parser
    "WWPParser",
    # PDF Splitter
    "PDFDocumentSplitter",
    "PDFElement",
    "PDFElementType",
    "PDFProcessingStats",
    "split_documentation_pdf",
    # Line Reader
    "LineContext",
    "read_lines",
    "count_lines",
    # Project Mapper
    "ProjectElementMapper",
    "MappingStats",
    "ElementInfo",
    "ParserState",
    "map_project_elements",
    # XDD Parser
    "XddParser",
    "XddParseResult",
    "HYPERFILE_TYPE_MAP",
    "find_analysis_file",
    # WDC Parser
    "WdcParser",
    "ParsedClass",
    # Dependency Extractor
    "DependencyExtractor",
    "ExtractedDependencies",
    # WWH Parser
    "WWHParser",
    "ParsedPage",
    "ParsedControl",
    "ParsedEvent",
    "ParsedLocalProcedure",
    "ParsedLocalParameter",
    "parse_wwh_file",
]
