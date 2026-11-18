import pymupdf as fitz
from pathlib import Path


def parse_pdf(pdf_path: Path) -> dict:
    """Parse PDF into per-page text + structured tables."""
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        page_num = i + 1
        text = page.get_text("text") or ""

        tables = []
        try:
            tabs = page.find_tables()
            for t in tabs.tables:
                rows = t.extract()
                if rows:
                    tables.append(rows)
        except Exception:
            pass

        pages.append({
            "page": page_num,
            "text": text.strip(),
            "tables": tables,
            "images": [],
        })

    doc.close()
    return {"pages": pages}