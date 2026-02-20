from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter


def export_table_pdf(table_widget, path):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)

    # Render only the visible area (like a screenshot).
    from PyQt6.QtGui import QPainter
    painter = QPainter(printer)
    table_widget.render(painter)
    painter.end()


def export_html_pdf(rows, cols, headers, path):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)

    html = build_html_table(rows, cols, headers)
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print(printer)


def build_html_table(rows, cols, headers):
    css = """
    <style>
      body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #999; padding: 4px 6px; }
      th { background: #efefef; text-align: left; }
      tr:nth-child(even) td { background: #fafafa; }
    </style>
    """
    thead = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for row in rows:
        tds = "".join(f"<td>{'' if v is None else v}</td>" for v in row)
        body_rows.append(f"<tr>{tds}</tr>")
    tbody = "".join(body_rows)
    return f"<!doctype html><html><head>{css}</head><body><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></body></html>"
