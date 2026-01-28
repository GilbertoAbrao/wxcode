---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/pdf_element_parser.py
type: module
updated: 2026-01-21
status: active
---

# pdf_element_parser.py

## Purpose

Extracts visual properties and documentation from WinDev-generated PDF documentation files. Parses control properties, screenshots, and descriptive text that complement the raw code parsing. Enriches Element documents with presentation layer details.

## Exports

- `PDFElementParser` - Class for parsing PDF documentation
- `parse_pdf(pdf_path)` - Extract element properties from PDF
- `extract_screenshot(pdf_path)` - Extract embedded screenshots

## Dependencies

- [[src-wxcode-models-element]] - Element enrichment
- pdfplumber - PDF text extraction
- PIL - Image extraction from PDFs

## Used By

TBD
