import io

import pytest
from docx import Document
from pypdf import PdfWriter

from app.config import settings
from app.extraction import chunks, extract


def test_text_sections_and_chunk_provenance():
    sections = extract(b"First policy.\n\nSecond policy.", "policy.txt")
    assert [s["location"] for s in sections] == ["Section 1", "Section 2"]
    text = "The policy applies to all employees. " * 90
    pieces = chunks([{"location": "Page 7", "text": text}])
    assert len(pieces) > 1
    assert all(p["location"] == "Page 7" and len(p["text"]) <= 1000 for p in pieces)
    assert pieces[-1]["text"].endswith("employees.")


@pytest.mark.parametrize("data,name", [(b"", "empty.txt"), (b"hello", "file.exe"),
    (b"not a PDF", "file.pdf"), (b"\xff\xfe", "file.txt"), (b"bad zip", "file.docx")])
def test_invalid_uploads(data, name):
    with pytest.raises(ValueError):
        extract(data, name)


def test_limits(monkeypatch):
    monkeypatch.setattr(settings, "max_file_bytes", 4)
    with pytest.raises(ValueError, match="10 MB"):
        extract(b"hello", "file.txt")


def test_scanned_and_encrypted_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(ValueError, match="No readable text"):
        extract(output.getvalue(), "scan.pdf")
    writer.encrypt("secret")
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(ValueError, match="Password-protected"):
        extract(output.getvalue(), "locked.pdf")


def test_docx_paragraphs_and_tables():
    document = Document()
    document.add_paragraph("Annual leave is 20 days.")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Carryover"
    table.cell(0, 1).text = "5 days"
    output = io.BytesIO()
    document.save(output)
    sections = extract(output.getvalue(), "policy.docx")
    assert "Annual leave" in sections[0]["text"]
    assert "Carryover | 5 days" in sections[1]["text"]
