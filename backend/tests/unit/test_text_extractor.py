import pytest
from io import BytesIO
from pypdf import PdfWriter
from app.utils.text_extractor import extract_text, extract_txt, extract_pdf


def test_extract_txt_valid():
    content = "Hello, world! This is a test document.".encode("utf-8")
    result = extract_text("test.txt", content)
    assert "Hello, world!" in result


def test_extract_txt_direct():
    content = "Direct text extraction test.".encode("utf-8")
    assert extract_txt(content) == "Direct text extraction test."


def test_extract_pdf_valid():
    # Dynamically build a valid 1-page PDF in-memory
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_content = pdf_bytes.getvalue()

    # Empty pages return empty string gracefully
    result = extract_text("test.pdf", pdf_content)
    assert isinstance(result, str)


def test_extract_unsupported_extension():
    content = b"Some binary or word content"
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("document.docx", content)


def test_extract_unsupported_image():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("image.png", b"\x89PNG")
