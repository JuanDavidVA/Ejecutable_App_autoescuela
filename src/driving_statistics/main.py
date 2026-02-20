import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QMessageBox, QTableWidgetItem,
    QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox
)

from driving_statistics.view.main_window import MainWindowUI
from driving_statistics.view.filtres import FilterDialog
from driving_statistics.services.database import init_database, fetch, COLUMNS
from driving_statistics.services.csv_importer import save_csv_to_db
from driving_statistics.services.charts import build_chart_view
from driving_statistics.services.reports import export_table_pdf, export_html_pdf


class MainController(MainWindowUI):
    def __init__(self):
        super().__init__()

        menu = self.menuBar().addMenu("Archivo")
        menu.addAction("Importar CSV/TXT", self.import_txt)
        menu.addAction("Aplicar filtros", self.open_filter_dialog)
        menu.addAction("Generar PDF", self.export_pdf)
        toolbar = self.addToolBar("Acciones")
        toolbar.addAction("Aplicar filtros", self.open_filter_dialog)
        toolbar.addAction("Generar PDF", self.export_pdf)
        self.chart_widget = None
        self.last_rows = []
        self.last_cols = []
        self.last_headers = []
        self.has_imported_data = False
        self.last_filters = {
            "province": "",
            "exam_center": "",
            "driving_school": "",
            "exam_type": "",
            "from_ym": "",
            "to_ym": "",
            "limit": 0,
            "group_by": "",
        }
        self.table.setSortingEnabled(True)
        self.load_initial_data()

    def load_initial_data(self):
        cols = [k for k, _ in COLUMNS]
        rows = fetch(f"SELECT {', '.join(cols)} FROM exams")
        self.last_rows = rows
        self.last_cols = cols
        self.last_headers = [lbl for _, lbl in COLUMNS]
        self.has_imported_data = len(rows) > 0
        self.render_table(rows, cols, self.last_headers)
        self.update_chart(rows, cols)

    def import_txt(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar datos",
            "",
            "Datos (*.txt *.csv);;TXT (*.txt);;CSV (*.csv)"
        )
        if not path:
            return

        try:
            save_csv_to_db(path)
            self.has_imported_data = True
            self.open_filter_dialog()

            QMessageBox.information(self, "OK", "TXT importado")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def open_filter_dialog(self):
        if not self.has_imported_data:
            QMessageBox.information(self, "Filtros", "Primero importa un TXT/CSV.")
            return

        dlg = FilterDialog(
            self,
            initial={"cols": self.last_cols, "filters": self.last_filters}
        )
        if dlg.exec():
            cols, filters = dlg.get_filters()
            self.load_filtered_data(cols, filters)

    def load_filtered_data(self, cols, filters):
        if not cols:
            cols = [k for k, _ in COLUMNS]

        where = []
        params = []

        for k in ("province", "exam_center", "driving_school"):
            if filters[k]:
                where.append(f"{k} LIKE ?")
                params.append(f"%{filters[k]}%")

        if filters["exam_type"]:
            where.append("exam_type LIKE ?")
            params.append(f"%{filters['exam_type']}%")

        where.append("(exam_month BETWEEN ? AND ? OR exam_month IS NULL OR exam_month = '')")
        params += [filters["from_ym"], filters["to_ym"]]

        group_by = filters.get("group_by", "")
        limit_value = int(filters.get("limit") or 0)
        headers_map = dict(COLUMNS)

        sql = ""
        render_cols = cols[:]
        render_headers = [headers_map[k] for k in cols if k in headers_map]

        if group_by:
            metric_cols = [k for k in ("presented", "passed", "failed") if k in cols]
            if not metric_cols:
                metric_cols = ["presented", "passed", "failed"]
            group_label = headers_map.get(group_by, group_by)
            select_parts = [group_by]
            for metric in metric_cols:
                select_parts.append(f"SUM(COALESCE({metric}, 0)) AS {metric}")
            render_cols = [group_by] + metric_cols
            render_headers = [group_label] + [headers_map[m] for m in metric_cols]
            sql = f"SELECT {', '.join(select_parts)} FROM exams"
        else:
            sql = f"SELECT {', '.join(cols)} FROM exams"

        if where:
            sql += " WHERE " + " AND ".join(where)
        if group_by:
            sql += f" GROUP BY {group_by} ORDER BY {group_by} ASC"
        if limit_value > 0:
            sql += " LIMIT ?"
            params.append(limit_value)

        rows = fetch(sql, params)
        self.last_rows = rows
        self.last_cols = render_cols
        self.last_headers = render_headers
        self.last_filters = filters
        self.has_imported_data = len(rows) > 0

        self.render_table(rows, render_cols, render_headers)
        self.update_chart(rows, render_cols)

    def render_table(self, rows, cols, headers=None):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(headers or [lbl for k, lbl in COLUMNS if k in cols])

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                col_key = cols[c]
                shown = self._format_value_for_table(col_key, val)
                self.table.setItem(r, c, QTableWidgetItem(shown))
        self.table.setSortingEnabled(True)

    def _format_value_for_table(self, col_key, value):
        if value is None:
            return ""

        text = str(value).strip()
        if col_key != "exam_month" or not text:
            return text

        # Normalize date-like values for display in the "Mes" column.
        if re.fullmatch(r"\d{4}-\d{2}", text):
            yyyy, mm = text.split("-")
            return f"{mm}/{yyyy}"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            yyyy, mm, dd = text.split("-")
            return f"{dd}/{mm}/{yyyy}"
        return text

    def update_chart(self, rows, cols):
        if getattr(self, "chart_placeholder", None) is not None:
            self.chart_layout.removeWidget(self.chart_placeholder)
            self.chart_placeholder.deleteLater()
            self.chart_placeholder = None

        if self.chart_widget is not None:
            self.chart_layout.removeWidget(self.chart_widget)
            self.chart_widget.deleteLater()
            self.chart_widget = None

        self.chart_widget = build_chart_view(rows, cols)
        self.chart_layout.addWidget(self.chart_widget)

    def export_pdf(self):
        if not self.last_cols:
            QMessageBox.information(self, "PDF", "Primero importa y aplica filtros.")
            return

        mode = self._select_pdf_mode()
        if mode is None:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "", "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            if mode == "table":
                export_table_pdf(self.table, path)
            else:
                export_html_pdf(self.last_rows, self.last_cols, self.last_headers, path)
            QMessageBox.information(self, "PDF", "PDF generado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _select_pdf_mode(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Generar PDF")
        layout = QVBoxLayout(dlg)

        opt_table = QRadioButton("Imprimir tabla (como captura)")
        opt_html = QRadioButton("Generar HTML e imprimir (todas las filas)")
        opt_html.setChecked(True)
        layout.addWidget(opt_table)
        layout.addWidget(opt_html)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        return "table" if opt_table.isChecked() else "html"


if __name__ == "__main__":
    init_database()
    app = QApplication(sys.argv)
    win = MainController()
    win.show()
    sys.exit(app.exec())