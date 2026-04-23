"""Render report.md to report.pdf via python-markdown + WeasyPrint."""
from __future__ import annotations

from pathlib import Path

import markdown
from weasyprint import CSS, HTML

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "report.md"
DST = ROOT / "report.pdf"

CSS_TEXT = """
@page { size: Letter; margin: 0.75in 0.9in; }
html { font-family: "Times New Roman", Georgia, serif; font-size: 10pt; line-height: 1.35; }
body { color: #111; }
h1 { font-size: 14pt; margin: 0 0 0.25em 0; }
h2 { font-size: 11.5pt; margin: 1.0em 0 0.3em 0; }
h3 { font-size: 10.5pt; margin: 0.8em 0 0.25em 0; }
p  { margin: 0 0 0.5em 0; text-align: justify; }
strong { font-weight: 700; }
table { border-collapse: collapse; width: 100%; margin: 0.4em 0 0.6em 0; font-size: 9pt; }
th, td { border: 1px solid #888; padding: 2px 6px; text-align: left; }
th { background: #eee; }
code { font-family: "Menlo", "Courier New", monospace; font-size: 9pt; }
ul, ol { margin: 0.25em 0 0.5em 1.25em; padding: 0; }
li { margin-bottom: 0.15em; }
hr { border: 0; border-top: 1px solid #bbb; margin: 0.5em 0; }
""".strip()


def main() -> None:
    md_text = SRC.read_text(encoding="utf-8")
    html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    html_doc = f"<!doctype html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    HTML(string=html_doc, base_url=str(ROOT)).write_pdf(
        str(DST), stylesheets=[CSS(string=CSS_TEXT)]
    )
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
