from pathlib import Path
from io import BytesIO
from pypdf import PdfReader

def extract_text(
    filename: str,
    content: bytes
) -> str:

    extension = Path(filename).suffix.lower()

    if extension == ".txt":
        return extract_txt(content)
    
    if extension == ".pdf":
        return extract_pdf(content)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


def extract_txt(content: bytes) -> str:
    return content.decode("utf-8")

def extract_pdf(content: bytes) -> str:
    pdf=PdfReader(
        BytesIO(content)
    )
    text = ""
    for page in pdf.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    return text