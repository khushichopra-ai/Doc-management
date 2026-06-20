from __future__ import annotations

import io
import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring

from django.core.management.base import BaseCommand

from aka.ingestion.parser import DocumentParser


def _build_docx_bytes() -> bytes:
    document = Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document")
    body = SubElement(document, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body")
    paragraph = SubElement(body, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")
    run = SubElement(paragraph, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r")
    text = SubElement(run, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
    text.text = "Hello DOCX"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", tostring(document))
    return buffer.getvalue()


def _build_xlsx_bytes() -> bytes:
    shared_strings = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">'
        "<si><t>Hello XLSX</t></si></sst>"
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData><row r='1'><c r='A1' t='s'><v>0</v></c></row></sheetData></worksheet>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared_strings)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


def _build_pptx_bytes() -> bytes:
    slide = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Hello PPTX</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>"
        "</p:sld>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Verify parsers return strings."

    def handle(self, *args, **options):
        parser = DocumentParser()
        cases = [
            ("sample.txt", b"hello world"),
            ("sample.docx", _build_docx_bytes()),
            ("sample.xlsx", _build_xlsx_bytes()),
            ("sample.pptx", _build_pptx_bytes()),
        ]
        for filename, content in cases:
            parsed = parser.parse(filename, content)
            if not isinstance(parsed.text, str):
                raise SystemExit(1)
            self.stdout.write(f"{filename}: OK")

