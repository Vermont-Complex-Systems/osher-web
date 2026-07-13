"""Wrangle the Osher participation matrix into a bipartite network.

The source CSV `osher-network(MAP).csv` is a participation matrix:
  - the first six columns describe an organizational unit at several levels of
    hierarchy (Organization > College/Unit/Center > Department > Division);
  - the remaining columns are 30 projects, with an "x" marking that the unit
    on that row takes part in the project.

We emit a bipartite graph:
  - `nodes.json`  -> org-unit nodes and project nodes;
  - `edges.json`  -> one edge per "x" (unit --participates--> project).

Run with:  uv run network.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "osher-network(MAP).csv"

# Column layout of the source matrix.
HIERARCHY_COLS = [
    "organization",        # 0  Organizations
    "organization_type",   # 1  Organization Type
    "college_unit",        # 2  College/Unit/Center_Inst.
    "college_unit_type",   # 3  College/Unit/Center_Inst. Type
    "department",          # 4  Departments
    "division",            # 5  Division
]
N_HIER = len(HIERARCHY_COLS)

# Levels (most-granular last) used to name a unit and build a unique id.
ID_LEVELS = ["organization", "college_unit", "department", "division"]


def clean(value: str) -> str:
    return (value or "").strip()


def is_x(value: str) -> bool:
    return clean(value).lower() == "x"


# Curated short display labels (reduce clutter on the canvas). The full name is
# kept as `label` for the tooltip; `short` falls back to the full label when not
# listed here. Edit freely — keys are the raw CSV labels.
SHORT = {
    # LCOM / Medical Group departments (academic = a, clinical = c)
    "Anastesiology (academic)": "Anesth (a)",
    "Anastesiology (clinical)": "Anesth (c)",
    "Cancer Center (academic)": "Cancer (a)",
    "Cancer Center (clinical)": "Cancer (c)",
    "Childrens Hospital (academic)": "Childrens (a)",
    "Childrens Hospital (clinical)": "Childrens (c)",
    "Emergency Med (academic)": "Emerg Med (a)",
    "Emergency Med (clinical)": "Emerg Med (c)",
    "Family Medicine (academic)": "Family Med (a)",
    "Family Medicine (clinical)": "Family Med (c)",
    "Medicine (academic)": "Medicine (a)",
    "Medicine (clinical)": "Medicine (c)",
    "OBGYN (academic)": "OBGYN (a)",
    "OBGYN (clinical)": "OBGYN (c)",
    "Psychiatry (academic)": "Psych (a)",
    # units / other entities
    "Medical Group": "UVM Health",  # the clinical practice group (parent of the clinical depts)
    "BioMedical/Mechanical Eng": "BME/ME",
    "Complex Systems": "Complex Sys",
    "Employee Wellness": "Emp Wellness",
    "Employee Welness (UVM)": "Emp Welln (UVM)",
    "Health Coaching": "Health Coach",
    "Inst. for Behavior Change": "IBC",
    "Nutrtion/Culinary Medicine": "Nutr/Culinary",
    "Osher WH Division": "Osher WH",
    # projects (only the longer names)
    "Peer Coaching": "Peer Coach",
    "Multi Center Imp": "MultiCtr Imp",
    "WH Levy Cancer": "WH Levy",
    "Comm Health Wrk": "CHW",
    "MultiStakeholer Ana.": "MultiStake",
    "Readiness Osher": "Readiness",
}


def short_label(label: str) -> str:
    return SHORT.get(label, label)


def depth_level(hier: dict) -> str:
    """Hierarchy depth of a node, for the abstract-outside / concrete-inside layout.

    org  = a whole organization        (outermost ring)
    unit = a college / center / unit    (middle ring)
    dept = a department / division      (innermost ring)
    """
    if hier.get("department") or hier.get("division"):
        return "dept"
    # a unit explicitly typed "Department" (e.g. UVMH / DEI) is a department even
    # when its Departments column is blank
    if hier.get("college_unit_type") == "Department":
        return "dept"
    if hier.get("college_unit"):
        return "unit"
    return "org"


def main() -> None:
    with SRC.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))

    # Row 0: headers; row 1: project names; row 2: project numbers; rest: data.
    project_names = rows[1]
    project_numbers = rows[2]

    # Project columns are everything past the hierarchy block.
    projects = []
    for col in range(N_HIER, len(project_names)):
        name = clean(project_names[col])
        if not name:
            continue
        num = clean(project_numbers[col]) if col < len(project_numbers) else ""
        projects.append(
            {
                "col": col,
                "id": f"P{num or col}",
                "name": name,
                "number": int(num) if num.isdigit() else None,
            }
        )

    org_nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for row in rows[3:]:
        if not any(clean(c) for c in row[:N_HIER]):
            continue  # skip blank rows

        hier = {key: clean(row[i]) for i, key in enumerate(HIERARCHY_COLS)}
        parts = [hier[level] for level in ID_LEVELS if hier[level]]
        if not parts:
            continue

        node_id = " / ".join(parts)
        if node_id not in org_nodes:
            org_nodes[node_id] = {
                "id": node_id,
                "type": "org",
                "label": parts[-1],
                "short": short_label(parts[-1]),
                "level": depth_level(hier),
                "n_projects": 0,
                **hier,
            }

        for proj in projects:
            col = proj["col"]
            if col < len(row) and is_x(row[col]):
                edges.append({"source": node_id, "target": proj["id"]})
                org_nodes[node_id]["n_projects"] += 1

    # Synthesize a parent unit node (CNHS, LCOM, Medical Group, …) for any
    # college/unit that only appears through its departments, so the college is
    # visible on the outer ring and its departments link up to it.
    unit_keys = {
        (n["organization"], n["college_unit"])
        for n in org_nodes.values()
        if n["level"] == "unit"
    }
    unit_type_of: dict[tuple, str] = {}
    for n in org_nodes.values():
        if n["college_unit"]:
            unit_type_of.setdefault(
                (n["organization"], n["college_unit"]), n["college_unit_type"]
            )

    for n in list(org_nodes.values()):
        if n["level"] != "dept" or not n["college_unit"]:
            continue
        key = (n["organization"], n["college_unit"])
        unit_id = f"{n['organization']} / {n['college_unit']}"
        # skip when the unit already exists, the dept *is* the unit (DEI), or the
        # "unit" is really an admin department (PHSO/HR) — those aren't colleges.
        if key in unit_keys or unit_id == n["id"] or unit_type_of.get(key) == "Department":
            continue
        unit_keys.add(key)
        label = n["college_unit"]
        org_nodes[unit_id] = {
            "id": unit_id,
            "type": "org",
            "label": label,
            "short": short_label(label),
            "level": "unit",
            "n_projects": 0,
            "synthetic": True,
            "organization": n["organization"],
            "organization_type": n["organization_type"],
            "college_unit": n["college_unit"],
            "college_unit_type": unit_type_of.get(key, n["college_unit_type"]),
            "department": "",
            "division": "",
        }

    # Give each node a `parent` (a department -> its unit node) for the hierarchy
    # spokes; units/orgs have no parent here.
    unit_ids = {n["id"] for n in org_nodes.values() if n["level"] == "unit"}
    for n in org_nodes.values():
        parent = ""
        if n["level"] == "dept" and n["college_unit"]:
            cand = f"{n['organization']} / {n['college_unit']}"
            if cand in unit_ids and cand != n["id"]:
                parent = cand
        n["parent"] = parent

    # Count participants per project.
    proj_degree: dict[str, int] = {}
    for e in edges:
        proj_degree[e["target"]] = proj_degree.get(e["target"], 0) + 1

    project_nodes = [
        {
            "id": p["id"],
            "type": "project",
            "label": p["name"],
            "short": short_label(p["name"]),
            "number": p["number"],
            "n_orgs": proj_degree.get(p["id"], 0),
        }
        for p in projects
    ]

    nodes = list(org_nodes.values()) + project_nodes

    (HERE / "nodes.json").write_text(json.dumps(nodes, indent=2) + "\n", encoding="utf-8")
    (HERE / "edges.json").write_text(json.dumps(edges, indent=2) + "\n", encoding="utf-8")

    print(
        f"org nodes: {len(org_nodes)}  |  "
        f"project nodes: {len(project_nodes)}  |  "
        f"edges: {len(edges)}"
    )


if __name__ == "__main__":
    main()
