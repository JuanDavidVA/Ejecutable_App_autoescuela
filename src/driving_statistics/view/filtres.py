from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate, QEvent
from driving_statistics.services.database import fetch, COLUMNS


class FilterDialog(QDialog):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros")
        self.resize(500, 500)
        initial = initial or {}
        initial_cols = initial.get("cols", [])
        initial_filters = initial.get("filters", {})

        layout = QVBoxLayout(self)

        
        self.checks = {}
        box = QGroupBox("Columnas")
        v = QVBoxLayout(box)
        for k, lbl in COLUMNS:
            cb = QCheckBox(lbl)
            if initial_cols:
                cb.setChecked(k in initial_cols)
            else:
                cb.setChecked(k in ("province", "exam_center", "exam_type", "presented", "passed", "failed"))
            self.checks[k] = cb
            v.addWidget(cb)
        layout.addWidget(box)

        
        form = QFormLayout()
        self.province = QLineEdit()
        self.center = QLineEdit()
        self.school = QLineEdit()
        self.exam_type = QLineEdit()
        self.province.setText(initial_filters.get("province", ""))
        self.center.setText(initial_filters.get("exam_center", ""))
        self.school.setText(initial_filters.get("driving_school", ""))
        self.exam_type.setText(initial_filters.get("exam_type", ""))

        self.limit = QSpinBox()
        self.limit.setRange(0, 1_000_000)
        self.limit.setSpecialValueText("Sin limite")
        self.limit.setValue(int(initial_filters.get("limit") or 0))

        self.group_by = QComboBox()
        self.group_by.addItem("Sin agrupar", "")
        self.group_by.addItem("Ano o mes y ano", "exam_month")
        self.group_by.addItem("Provincia", "province")
        self.group_by.addItem("Centro de examen", "exam_center")
        self.group_by.addItem("Autoescuela", "driving_school")
        initial_group = initial_filters.get("group_by", "")
        idx = self.group_by.findData(initial_group)
        self.group_by.setCurrentIndex(idx if idx >= 0 else 0)

        default_from = QDate.currentDate().addMonths(-6)
        default_to = QDate.currentDate()
        from_ym = initial_filters.get("from_ym")
        to_ym = initial_filters.get("to_ym")
        from_date = QDate.fromString(f"{from_ym}-01", "yyyy-MM-dd") if from_ym else default_from
        to_date = QDate.fromString(f"{to_ym}-01", "yyyy-MM-dd") if to_ym else default_to
        self.from_date = QDateEdit(from_date if from_date.isValid() else default_from)
        self.to_date = QDateEdit(to_date if to_date.isValid() else default_to)
        for d in (self.from_date, self.to_date):
            d.setDisplayFormat("MM/yyyy")
            d.setCalendarPopup(True)

        form.addRow("Provincia", self.province)
        form.addRow("Centro", self.center)
        form.addRow("Autoescuela", self.school)
        form.addRow("Tipo", self.exam_type)
        form.addRow("Limite", self.limit)
        form.addRow("Agrupar por", self.group_by)

        row = QHBoxLayout()
        row.addWidget(self.from_date)
        row.addWidget(self.to_date)
        form.addRow("Mes", row)

        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Aplicar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

        self._setup_completers()
        for w in (self.province, self.center, self.school, self.exam_type):
            w.installEventFilter(self)

    def _setup_completers(self):
        self._set_completer(self.province, self._distinct("province"))
        self._set_completer(self.center, self._distinct("exam_center"))
        self._set_completer(self.school, self._distinct("driving_school"))
        self._set_completer(self.exam_type, self._distinct("exam_type"))

    def _set_completer(self, widget, values):
        comp = QCompleter(values)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        widget.setCompleter(comp)

    def _distinct(self, column):
        rows = fetch(f"SELECT DISTINCT {column} FROM exams WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}")
        return [r[0] for r in rows]

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            comp = obj.completer()
            if comp:
                comp.complete()
        return super().eventFilter(obj, event)

    def get_filters(self):
        cols = [k for k, cb in self.checks.items() if cb.isChecked()]
        return cols, {
            "province": self.province.text(),
            "exam_center": self.center.text(),
            "driving_school": self.school.text(),
            "exam_type": self.exam_type.text(),
            "from_ym": self.from_date.date().toString("yyyy-MM"),
            "to_ym": self.to_date.date().toString("yyyy-MM"),
            "limit": self.limit.value(),
            "group_by": self.group_by.currentData(),
        }
