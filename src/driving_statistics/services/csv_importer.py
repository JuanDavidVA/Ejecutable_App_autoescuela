import csv
from driving_statistics.services.database import get_connection


def to_int(v):
    try:
        return int(str(v).replace(".", "").replace(",", "").strip())
    except Exception:
        return 0


def _norm(s):
    return str(s).strip().lower()


def _header_map(header):
    return {_norm(name): idx for idx, name in enumerate(header)}


def _cell(row, hmap, *names):
    for name in names:
        idx = hmap.get(_norm(name))
        if idx is not None and idx < len(row):
            return str(row[idx]).strip()
    return ""


def read_text_rows(path):
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, encoding=enc, newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample, ",;\t|")
                return list(csv.reader(f, dialect))
        except Exception:
            pass
    raise ValueError("No se pudo leer el archivo")


def save_csv_to_db(path):
    rows = read_text_rows(path)
    if not rows:
        return

    first_row = rows[0]
    has_header = any(
        key in _norm(" ".join(first_row))
        for key in ("provincia", "desc_provincia", "centro_examen", "nombre_autoescuela")
    )
    data = rows[1:] if has_header else rows
    hmap = _header_map(first_row) if has_header else {}

    sql = """
        INSERT OR IGNORE INTO exams
        (province, exam_center, exam_type, driving_school, exam_month,
         presented, passed, failed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as conn:
        cur = conn.cursor()
        for r in data:
            if not any(str(x).strip() for x in r):
                continue

            if hmap:
                province = _cell(r, hmap, "province", "provincia", "desc_provincia")
                exam_center = _cell(r, hmap, "exam_center", "centro", "centro_examen")
                driving_school = _cell(r, hmap, "driving_school", "autoescuela", "nombre_autoescuela")
                exam_type = _cell(r, hmap, "exam_type", "tipo_examen")
                permiso = _cell(r, hmap, "nombre_permiso")
                if permiso:
                    exam_type = f"{exam_type} {permiso}".strip()

                month = _cell(r, hmap, "mes", "exam_month")
                year = _cell(r, hmap, "anyo", "año", "year")
                exam_month = f"{year}-{month.zfill(2)}" if year and month else month

                # DGT export: presented is not explicit; derive from aptos + no aptos.
                passed = to_int(_cell(r, hmap, "passed", "aptos", "num_aptos"))
                failed = to_int(_cell(r, hmap, "failed", "no aptos", "num_no_aptos"))
                has_dgt_counts = (
                    _norm("num_aptos") in hmap or _norm("num_no_aptos") in hmap
                )
                if has_dgt_counts:
                    presented = passed + failed
                else:
                    presented_raw = _cell(r, hmap, "presented", "presentados")
                    presented = to_int(presented_raw) if presented_raw else (passed + failed)
            else:
                r += [""] * (8 - len(r))
                province = r[0].strip()
                exam_center = r[1].strip()
                exam_type = r[2].strip()
                driving_school = r[3].strip()
                exam_month = r[4].strip()
                presented = to_int(r[5])
                passed = to_int(r[6])
                failed = to_int(r[7])

            cur.execute(sql, (
                province,
                exam_center,
                exam_type,
                driving_school,
                exam_month,
                presented,
                passed,
                failed,
            ))
