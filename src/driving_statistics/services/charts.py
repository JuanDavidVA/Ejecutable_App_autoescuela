# Preparado para futuras gráficas (QtCharts)
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QCursor
from PyQt6.QtWidgets import QToolTip


def build_chart_view(rows, cols):
    labels = {
        "presented": "Presentados",
        "passed": "Aptos",
        "failed": "No aptos",
    }

    sums = {}
    for key in ("presented", "passed", "failed"):
        if key in cols:
            idx = cols.index(key)
            total = 0
            for row in rows:
                val = row[idx]
                if val is None or val == "":
                    continue
                total += int(val)
            sums[key] = total

    chart = QChart()
    chart.setTitle("Totales del filtro")
    chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

    categories = [labels[k] for k in ("presented", "passed", "failed") if k in sums]
    if categories:
        series = QBarSeries()
        bar_set = QBarSet("Total")
        values = [sums[k] for k in ("presented", "passed", "failed") if k in sums]
        bar_set.append(values)
        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Cantidad")
        axis_y.setMin(0)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        def _on_hovered(status, index, bar_set_ref=bar_set, cats=categories):
            if not status:
                QToolTip.hideText()
                return
            try:
                val = int(bar_set_ref.at(index))
            except Exception:
                val = bar_set_ref.at(index)
            label = cats[index] if 0 <= index < len(cats) else "Valor"
            QToolTip.showText(QCursor.pos(), f"{label}: {val}")

        bar_set.hovered.connect(_on_hovered)
    else:
        chart.setTitle("Sin datos para graficar")

    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    return view
