#!/usr/bin/env python3
"""Bind every table number of 06.18-COSTS.md to the JSON cost evidence.

Stdlib only. Run from anywhere:

    python3 check_costs_md.py           # check; exit 0 when every check passes, exit 1 otherwise
    python3 check_costs_md.py --facts   # print the JSON facts the prose numerals are copied from
    python3 check_costs_md.py --emit    # print the current 24 rows and the categories table from the JSON

Checked (each heading locates the first Markdown table that follows it):

1. ``## The 24 cells``: the current 24-cell table against ``evidence/261109-bf5/cost-observations``
   (Now, Guard, Rest, Delta, Gates, status 200) and the Baseline column against
   ``evidence/06.18-01/baseline-observations`` (``legacy-no-mode/{op}``).
2. ``## History: plan 12 record (5829cae7)``: the plan 12 24-cell table against ``evidence/06.18-12/cost-observations``.
3. ``### Categories per request``: ``| Cells | Temperature | Guard | Rest |`` rows against ``guard_by_table`` and
   ``rest_by_table``; all 48 (cell, temperature) observations covered exactly once.
4. ``## Nearest-only and top-level controls``: the four top-level rows against ``top-level.json``.
5. ``## Render-helper work, separate from the guard``: the two fixed-form total sentences against the
   ``*-list-with-create-button.json`` files, and the plain totals equal to matrix cells 1, 2, 13, 14.
6. ``## Sources and runtime``: the "Current measurement" SHA and runtime against ``meta`` of all nine files.
"""

import json
import re
import sys
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parents[2]
COSTS_MD = PHASE_DIR / "06.18-COSTS.md"
CURRENT_DIR = PHASE_DIR / "evidence" / "261109-bf5" / "cost-observations"
HISTORY_DIR = PHASE_DIR / "evidence" / "06.18-12" / "cost-observations"
BASELINE_DIR = PHASE_DIR / "evidence" / "06.18-01" / "baseline-observations"

EVIDENCE_FILES = [
    "depth1-plain.json",
    "depth1-guardian.json",
    "depth3-plain.json",
    "depth3-guardian.json",
    "depth1-plain-list-with-create-button.json",
    "depth1-guardian-list-with-create-button.json",
    "depth3-plain-list-with-create-button.json",
    "depth3-guardian-list-with-create-button.json",
    "top-level.json",
]

ABBREV = {
    "session": "django_session",
    "user": "auth_user",
    "ct": "django_content_type",
    "perm": "auth_permission",
    "publisher": "app_publisher",
    "book": "app_book",
    "booknote": "app_booknote",
    "leaf": "app_ancestorobservationleaf",
}
TABLE_TO_ABBREV = {v: k for k, v in ABBREV.items()}
MODEL_NAMES = {"publisher": "Publisher", "book": "Book", "booknote": "BookNote"}

# Canonical cell order 1-24: depth, provider, op, mode.
CELLS = []
for _depth in (1, 3):
    for _provider in ("plain", "guardian"):
        for _op in ("list", "object", "create"):
            for _mode in ("full", "nearest"):
                CELLS.append((_depth, _provider, _op, _mode))

TEMPS = ("cold", "warm")

H_CELLS = "## The 24 cells"
H_HISTORY = "## History: plan 12 record (5829cae7)"
H_CATEGORIES = "### Categories per request"
H_CONTROLS = "## Nearest-only and top-level controls"
H_RENDER = "## Render-helper work, separate from the guard"
H_SOURCES = "## Sources and runtime"

HELPER_RE = re.compile(
    r"\(depth 1: (\d+)/(\d+) full, (\d+)/(\d+) nearest; depth 3: (\d+)/(\d+) full, (\d+)/(\d+) nearest\)"
)


class Checker:
    def __init__(self):
        self.checks = 0
        self.mismatches = []
        self.counts = {}

    def eq(self, where, doc, json_value):
        self.checks += 1
        if doc != json_value:
            self.mismatches.append(f"MISMATCH {where}: doc={doc!r} json={json_value!r}")
            return False
        return True

    def fail(self, where, doc, json_value):
        self.checks += 1
        self.mismatches.append(f"MISMATCH {where}: doc={doc!r} json={json_value!r}")

    def count(self, key, n=1):
        self.counts[key] = self.counts.get(key, 0) + n


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def obs(directory, depth, provider, op, mode, temp):
    data = load(directory / f"depth{depth}-{provider}.json")
    return data["observations"][f"{mode}/{op}"][temp]


def baseline_total(depth, provider, op, temp):
    data = load(BASELINE_DIR / f"depth{depth}-{provider}.json")
    return data["observations"][f"legacy-no-mode/{op}"][temp]["total"]


def gate_models(gates):
    names = []
    for gate in gates:
        codename = gate[2].split(".", 1)[-1]
        model = codename.split("_", 1)[-1]
        names.append(MODEL_NAMES.get(model, f"?{model}"))
    return names


def abbrev_dict(by_table):
    return {TABLE_TO_ABBREV.get(t, t): n for t, n in by_table.items() if n}


def format_tokens(by_table):
    if not by_table:
        return "nothing"
    order = list(ABBREV)
    items = sorted(by_table.items(), key=lambda kv: order.index(TABLE_TO_ABBREV[kv[0]]) if kv[0] in TABLE_TO_ABBREV else 99)
    return ", ".join(f"{TABLE_TO_ABBREV.get(t, t)} {n}" for t, n in items if n)


def parse_tokens(text):
    """'session 1, perm 2' -> {'django_session': 1, 'auth_permission': 2}; 'nothing' -> {}; None on error."""
    text = text.strip()
    if text == "nothing":
        return {}
    result = {}
    for part in text.split(","):
        m = re.fullmatch(r"\s*([a-z]+) (\d+)\s*", part)
        if not m or m.group(1) not in ABBREV or ABBREV[m.group(1)] in result:
            return None
        result[ABBREV[m.group(1)]] = int(m.group(2))
    return result


def parse_pair(text, signed=False):
    pattern = r"\s*([+-]?\d+) / ([+-]?\d+)\s*" if signed else r"\s*(\d+) / (\d+)\s*"
    m = re.fullmatch(pattern, text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def expand_cells(text):
    cells = []
    for part in text.split(","):
        part = part.strip()
        m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo > hi:
                return None
            cells.extend(range(lo, hi + 1))
        elif re.fullmatch(r"\d+", part):
            cells.append(int(part))
        else:
            return None
    return cells


def section_lines(lines, heading):
    """Lines after the first exact heading line up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    for i, line in enumerate(lines):
        if line.rstrip() == heading:
            out = []
            for nxt in lines[i + 1 :]:
                m = re.match(r"^(#+) ", nxt)
                if m and len(m.group(1)) <= level:
                    break
                out.append(nxt)
            return out
    return None


def first_table(section):
    """Rows of the first Markdown table in the section (header and separator dropped), or None."""
    rows = []
    started = False
    for line in section:
        if line.startswith("|"):
            started = True
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif started:
            break
    if len(rows) < 2:
        return None
    return rows[0], rows[2:]


def check_cells_table(c, lines, heading, directory, label):
    section = section_lines(lines, heading)
    if section is None:
        c.fail(f"{label}: heading", "missing", heading)
        return
    table = first_table(section)
    if table is None:
        c.fail(f"{label}: table", "missing", "24-cell table")
        return
    _header, rows = table
    c.eq(f"{label}: row count", len(rows), 24)
    for index, row in enumerate(rows[:24]):
        number = index + 1
        where = f"{label} row {number}"
        if len(row) != 11:
            c.fail(f"{where}: column count", len(row), 11)
            continue
        depth, provider, op, mode = CELLS[index]
        c.eq(f"{where} #", row[0], str(number))
        c.eq(f"{where} depth", row[1], str(depth))
        c.eq(f"{where} provider", row[2], provider)
        c.eq(f"{where} operation", row[3], op)
        c.eq(f"{where} mode", row[4], mode)
        cold = obs(directory, depth, provider, op, mode, "cold")
        warm = obs(directory, depth, provider, op, mode, "warm")
        base = (baseline_total(depth, provider, op, "cold"), baseline_total(depth, provider, op, "warm"))
        now = (cold["total"], warm["total"])
        delta = (now[0] - base[0], now[1] - base[1])
        for col, idx, expected, signed in (
            ("baseline", 5, base, False),
            ("now", 6, now, False),
            ("delta", 7, delta, True),
            ("guard", 8, (cold["guard"], warm["guard"]), False),
            ("rest", 9, (cold["rest"], warm["rest"]), False),
        ):
            parsed = parse_pair(row[idx], signed=signed)
            if parsed is None:
                c.fail(f"{where} {col}: unparseable", row[idx], expected)
            else:
                c.eq(f"{where} {col}", parsed, expected)
        c.eq(f"{where} status cold/warm", (200, 200), (cold["status"], warm["status"]))
        c.eq(f"{where} gates cold == warm", gate_models(cold["gates"]), gate_models(warm["gates"]))
        c.eq(f"{where} gates", row[10], ", ".join(gate_models(cold["gates"])))
        c.count(f"{label} cells")


def check_categories(c, lines):
    label = "categories"
    section = section_lines(lines, H_CATEGORIES)
    if section is None:
        c.fail(f"{label}: heading", "missing", H_CATEGORIES)
        return
    table = first_table(section)
    if table is None:
        c.fail(f"{label}: table", "missing", "categories table")
        return
    header, rows = table
    if not c.eq(f"{label}: header", header, ["Cells", "Temperature", "Guard", "Rest"]):
        return
    seen = {}
    for r, row in enumerate(rows, start=1):
        where = f"{label} row {r}"
        if len(row) != 4:
            c.fail(f"{where}: column count", len(row), 4)
            continue
        cells = expand_cells(row[0])
        temp = row[1]
        guard = parse_tokens(row[2])
        rest = parse_tokens(row[3])
        if cells is None or temp not in TEMPS or guard is None or rest is None:
            c.fail(f"{where}: unparseable", row, "Cells | cold/warm | abbrev N list | abbrev N list")
            continue
        for cell in cells:
            if not 1 <= cell <= 24:
                c.fail(f"{where}: cell out of range", cell, "1-24")
                continue
            key = (cell, temp)
            seen[key] = seen.get(key, 0) + 1
            o = obs(CURRENT_DIR, *CELLS[cell - 1], temp)
            c.eq(f"{where} cell {cell} {temp} guard", guard, {t: n for t, n in o["guard_by_table"].items() if n})
            c.eq(f"{where} cell {cell} {temp} rest", rest, {t: n for t, n in o["rest_by_table"].items() if n})
    for cell in range(1, 25):
        for temp in TEMPS:
            if c.eq(f"{label} coverage cell {cell} {temp}", seen.get((cell, temp), 0), 1):
                c.count("category observations")


def check_top_level(c, lines):
    label = "top-level"
    section = section_lines(lines, H_CONTROLS)
    if section is None:
        c.fail(f"{label}: heading", "missing", H_CONTROLS)
        return
    table = first_table(section)
    if table is None:
        c.fail(f"{label}: table", "missing", "top-level table")
        return
    _header, rows = table
    data = load(CURRENT_DIR / "top-level.json")["observations"]
    expected_keys = ["plain/list", "plain/detail", "guardian/list", "guardian/detail"]
    c.eq(f"{label}: row count", len(rows), 4)
    for row, key in zip(rows, expected_keys):
        where = f"{label} {key}"
        provider, op = key.split("/")
        name = row[0].lower()
        c.eq(f"{where}: row label", provider in name and op in name, True)
        o = data[key]
        c.eq(f"{where} total", row[1], str(o["total"]))
        c.eq(f"{where} guard", row[2], str(o["guard"]))
        c.eq(f"{where} tables", parse_tokens(row[3]), {t: n for t, n in o["by_table"].items() if n})
        c.count("top-level rows")


def helper_totals(provider):
    values = []
    for depth in (1, 3):
        data = load(CURRENT_DIR / f"depth{depth}-{provider}-list-with-create-button.json")["observations"]
        for mode in ("full", "nearest"):
            values.extend([data[f"{mode}/list"]["cold"]["total"], data[f"{mode}/list"]["warm"]["total"]])
    return values


def check_render_helper(c, lines):
    label = "render-helper"
    section = section_lines(lines, H_RENDER)
    if section is None:
        c.fail(f"{label}: heading", "missing", H_RENDER)
        return
    for provider, marker in (("plain", "**Plain leaf"), ("guardian", "**Guardian leaf")):
        bullets = [line for line in section if marker in line]
        matches = [m for line in bullets for m in HELPER_RE.finditer(line)]
        if len(matches) != 1:
            c.fail(f"{label} {provider}: fixed-form sentence count", len(matches), 1)
            continue
        doc = [int(g) for g in matches[0].groups()]
        c.eq(f"{label} {provider} totals (d1 full c/w, d1 nearest c/w, d3 full c/w, d3 nearest c/w)",
             doc, helper_totals(provider))
        c.count("render-helper sentences")
    # Plain create-button totals equal the matrix list cells 1, 2, 13, 14.
    plain_bullet = " ".join(line for line in section if "**Plain leaf" in line)
    c.eq(f"{label} plain: equality claim present", "matrix list cells" in plain_bullet, True)
    matrix = []
    for depth in (1, 3):
        for mode in ("full", "nearest"):
            for temp in TEMPS:
                matrix.append(obs(CURRENT_DIR, depth, "plain", "list", mode, temp)["total"])
    c.eq(f"{label} plain create-button totals == matrix cells 1, 2, 13, 14", helper_totals("plain"), matrix)
    # Guardian depth 1 warm statement.
    guardian_bullet = " ".join(line for line in section if "**Guardian leaf" in line)
    m = re.search(r"depth 1 warm total is (\d+)", guardian_bullet)
    data = load(CURRENT_DIR / "depth1-guardian-list-with-create-button.json")["observations"]
    warm = {data["full/list"]["warm"]["total"], data["nearest/list"]["warm"]["total"]}
    if m is None:
        c.fail(f"{label} guardian: 'depth 1 warm total is N' statement", "missing", sorted(warm))
    else:
        c.eq(f"{label} guardian depth 1 warm total", {int(m.group(1))}, warm)


def check_sources(c, lines):
    label = "sources"
    section = section_lines(lines, H_SOURCES)
    if section is None:
        c.fail(f"{label}: heading", "missing", H_SOURCES)
        return
    table = first_table(section)
    if table is None:
        c.fail(f"{label}: table", "missing", "sources table")
        return
    header, rows = table
    if "Current measurement" not in header:
        c.fail(f"{label}: 'Current measurement' column", header, "Current measurement")
        return
    col = header.index("Current measurement")
    by_name = {row[0]: row for row in rows}
    metas = {name: load(CURRENT_DIR / name)["meta"] for name in EVIDENCE_FILES}
    source_row = by_name.get("Source")
    runtime_row = next((row for name, row in by_name.items() if name.startswith("Python / Django")), None)
    if source_row is None or runtime_row is None:
        c.fail(f"{label}: Source / runtime rows", sorted(by_name), "Source, Python / Django ...")
        return
    sha = re.search(r"\b[0-9a-f]{40}\b", source_row[col])
    sha = sha.group(0) if sha else None
    for name, meta in metas.items():
        c.eq(f"{label} source sha vs {name}", sha, meta["source_sha"])
        c.eq(f"{label} src_dirty {name}", False, meta["src_dirty"])
        c.eq(f"{label} runtime vs {name}", f"{meta['python']} / {meta['django']}" in runtime_row[col], True)
        c.count("sources files")


def run_check():
    c = Checker()
    lines = COSTS_MD.read_text(encoding="utf-8").splitlines()
    check_sources(c, lines)
    check_cells_table(c, lines, H_CELLS, CURRENT_DIR, "current")
    check_categories(c, lines)
    check_top_level(c, lines)
    check_render_helper(c, lines)
    check_cells_table(c, lines, H_HISTORY, HISTORY_DIR, "history")
    for line in c.mismatches:
        print(line)
    covered = ", ".join(
        f"{key} {c.counts.get(key, 0)}"
        for key in (
            "current cells",
            "history cells",
            "category observations",
            "top-level rows",
            "render-helper sentences",
            "sources files",
        )
    )
    status = "PASS" if not c.mismatches else "FAIL"
    print(f"{status}: checks={c.checks} mismatches={len(c.mismatches)} ({covered}) file={COSTS_MD.name}")
    return 0 if not c.mismatches else 1


def cell_groups(temp):
    """Group cells whose guard and rest categories are identical at this temperature."""
    groups = []
    for number, cell in enumerate(CELLS, start=1):
        o = obs(CURRENT_DIR, *cell, temp)
        key = (format_tokens(o["guard_by_table"]), format_tokens(o["rest_by_table"]))
        for group in groups:
            if group[0] == key:
                group[1].append(number)
                break
        else:
            groups.append((key, [number]))
    return groups


def format_cells(numbers):
    parts = []
    start = prev = numbers[0]
    for n in numbers[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        parts.append(str(start) if start == prev else f"{start}–{prev}")
        if n is not None:
            start = prev = n
    return ", ".join(parts)


def emit():
    print("## current 24-cell rows")
    for number, (depth, provider, op, mode) in enumerate(CELLS, start=1):
        cold = obs(CURRENT_DIR, depth, provider, op, mode, "cold")
        warm = obs(CURRENT_DIR, depth, provider, op, mode, "warm")
        base = (baseline_total(depth, provider, op, "cold"), baseline_total(depth, provider, op, "warm"))
        d = (cold["total"] - base[0], warm["total"] - base[1])
        print(
            f"| {number} | {depth} | {provider} | {op} | {mode} | {base[0]} / {base[1]} | "
            f"{cold['total']} / {warm['total']} | {d[0]:+d} / {d[1]:+d} | {cold['guard']} / {warm['guard']} | "
            f"{cold['rest']} / {warm['rest']} | {', '.join(gate_models(cold['gates']))} |"
        )
    print()
    print("## categories rows")
    rows = []
    for temp in TEMPS:
        for (guard, rest), numbers in cell_groups(temp):
            rows.append((numbers[0], TEMPS.index(temp), f"| {format_cells(numbers)} | {temp} | {guard} | {rest} |"))
    for _first, _t, row in sorted(rows):
        print(row)


def facts():
    print("## per-cell totals and guard/rest (current evidence), cold | warm")
    for number, cell in enumerate(CELLS, start=1):
        parts = []
        for temp in TEMPS:
            o = obs(CURRENT_DIR, *cell, temp)
            parts.append(
                f"{temp} total {o['total']} guard {o['guard']} rest {o['rest']} "
                f"guard_ct {o['guard_by_table'].get('django_content_type', 0)} "
                f"guard_perm {o['guard_by_table'].get('auth_permission', 0)} "
                f"rest {format_tokens(o['rest_by_table'])}"
            )
        print(f"cell {number} {cell}: " + " | ".join(parts))
    print()
    print("## create-button totals (current evidence), cold/warm")
    for provider in ("plain", "guardian"):
        for depth in (1, 3):
            data = load(CURRENT_DIR / f"depth{depth}-{provider}-list-with-create-button.json")["observations"]
            for mode in ("full", "nearest"):
                o = data[f"{mode}/list"]
                gates = [g for g in o["cold"]["gates"] if g[0] != "guard"]
                print(
                    f"{provider} depth {depth} {mode}: total {o['cold']['total']}/{o['warm']['total']} "
                    f"guard {o['cold']['guard']}/{o['warm']['guard']} rest {o['cold']['rest']}/{o['warm']['rest']} "
                    f"non-guard gates {[g[2] for g in gates]}"
                )
    print()
    print("## Guardian guard/rest difference: evidence/06.18-12 -> current (cold and warm)")
    files = ["depth1-guardian.json", "depth3-guardian.json",
             "depth1-guardian-list-with-create-button.json", "depth3-guardian-list-with-create-button.json"]
    n = 0
    for name in files:
        old = load(HISTORY_DIR / name)["observations"]
        new = load(CURRENT_DIR / name)["observations"]
        for key in sorted(new):
            for temp in TEMPS:
                o, w = old[key][temp], new[key][temp]
                n += 1
                gdiff = {t: w["guard_by_table"].get(t, 0) - o["guard_by_table"].get(t, 0)
                         for t in set(o["guard_by_table"]) | set(w["guard_by_table"])}
                gdiff = {t: v for t, v in gdiff.items() if v}
                print(
                    f"{name} {key} {temp}: total {o['total']}->{w['total']} guard {o['guard']}->{w['guard']} "
                    f"({w['guard'] - o['guard']:+d}) rest {o['rest']}->{w['rest']} ({w['rest'] - o['rest']:+d}) "
                    f"by_table equal {o['by_table'] == w['by_table']} guard_by_table diff {gdiff}"
                )
    print(f"guardian observations compared: {n}")
    print()
    print("## top-level (current evidence)")
    for key, o in load(CURRENT_DIR / "top-level.json")["observations"].items():
        print(f"{key}: total {o['total']} guard {o['guard']} tables {format_tokens(o['by_table'])}")
    print()
    meta = load(CURRENT_DIR / "depth1-plain.json")["meta"]
    print(f"## meta: {meta}")


def main(argv):
    if "--facts" in argv:
        facts()
        return 0
    if "--emit" in argv:
        emit()
        return 0
    return run_check()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
