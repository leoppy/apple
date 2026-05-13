import argparse
import os
from typing import List


def extract_with_pypdf(pdf_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    pages: List[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def extract_with_pymupdf(pdf_path: str) -> str:
    import fitz

    doc = fitz.open(pdf_path)
    try:
        pages: List[str] = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n\n".join(pages)
    finally:
        doc.close()


def extract_with_pdfplumber(pdf_path: str) -> str:
    import pdfplumber

    pages: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description="提取简历 PDF 文本")
    parser.add_argument("--pdf", required=True, help="PDF 路径")
    parser.add_argument("--out", required=True, help="输出 txt 路径")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        raise FileNotFoundError(args.pdf)

    text = ""
    errors = []

    try:
        text = extract_with_pypdf(args.pdf)
    except Exception as e:
        errors.append(f"pypdf: {e}")

    if not text.strip():
        try:
            text = extract_with_pdfplumber(args.pdf)
        except Exception as e:
            errors.append(f"pdfplumber: {e}")

    if not text.strip():
        try:
            text = extract_with_pymupdf(args.pdf)
        except Exception as e:
            errors.append(f"pymupdf: {e}")

    if not text.strip():
        msg = "; ".join(errors) if errors else "unknown extractor error"
        raise RuntimeError(f"无法提取 PDF 文本: {msg}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)

    print(args.out)


if __name__ == "__main__":
    main()
