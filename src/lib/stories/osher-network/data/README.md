# Osher network data

Turns the Osher participation matrix into a bipartite graph that the story's
`NetworkGraph.svelte` draws as an ego-radial network.

## Files

| File | What it is |
|------|-----------|
| `osher-network(MAP).csv` | **Source.** A participation matrix (hand-maintained). |
| `network.py` | Wrangler: CSV → `nodes.json` + `edges.json`. |
| `nodes.json` / `edges.json` | Generated. Do not edit by hand. |
| `pyproject.toml`, `.venv/` | uv-managed environment (stdlib only, no deps). |

## Regenerate

```bash
uv run network.py
```

## The source CSV

Each row is an **organizational unit** described at several levels of hierarchy;
the columns after `Division` are the 30 **projects**, with an `x` marking that
the unit on that row takes part in the project.

```
Organization | Org Type | College/Unit/Center | Unit Type | Department | Division | P1 P2 … P30
```

## What the wrangler emits

A **bipartite graph**: organizational units and projects are both nodes;
every `x` becomes one participation edge (unit → project).

**Org node**
```json
{ "id": "UVM / CNHS / RMS", "type": "org", "label": "RMS", "level": "dept",
  "n_projects": 5, "organization": "UVM", "organization_type": "University",
  "college_unit": "CNHS", "college_unit_type": "College",
  "department": "RMS", "division": "" }
```
- `id` — the granular hierarchy path (keeps units unique); `label` is the most specific level.
- `level` — `org` | `unit` | `dept`, the depth used for the ring layout (see below).
- `n_projects` — how many projects this unit participates in.

**Project node**
```json
{ "id": "P1", "type": "project", "label": "Peer Coaching", "number": 1, "n_orgs": 6 }
```

**Edge**: `{ "source": "<org id>", "target": "<project id>" }`

Current output: **56 org nodes** (12 `org` · 16 `unit` · 28 `dept`), **30 projects**, **102 edges**.

## `level` — the one non-obvious rule

`level` decides which ring a node sits on. It is derived from *which hierarchy
column is filled*, not from a label:

1. a **Department** or **Division** value → `dept`
2. **or** the unit is explicitly typed `"Department"` (e.g. `UVMH / DEI`, which has
   a blank Departments column) → `dept`
3. otherwise a **College/Unit/Center** value → `unit`
4. otherwise (only an organization) → `org`

Rule 2 is a data quirk: a few UVMH departments (DEI) were entered in the
College/Unit column, so we catch them by their type.

## How the story draws it (in `NetworkGraph.svelte`)

Geometry and color are **not** in the data — the wrangler only provides `level`
and the fields. The component:

- **Rings by depth** — Osher Center is the ego at the center; `dept` nodes on the
  inner ring; `org` + `unit` nodes together on the outer ring (abstract outside,
  concrete inside). Projects float in the core via a light force layout, pulled
  toward the units they connect to.
- **Wedges** — each organization gets an angular sector sized by its node count,
  so an org's units and departments stack into one radial slice.
- **Color** — orthogonal to the rings:
  - `UVM` and `UVMH` are colored individually (they're the bulk of the graph);
  - every other (external) organization is grouped by its **type**
    (`University`, `Government Agency`, `Professional Association`, …),
  - **except** where a node carries a more specific unit type, which wins
    (e.g. Osher Collaborative's *Harvard* / *Wisconsin* read as `Center; Institute`,
    Dartmouth's *NNE Coop* as `Practice Based Research Network`).

## Note on the source

Labels are passed through verbatim, including source typos
(`Welness`, `Anastesiology`, `Physicain Group`). They're spelled consistently, so
they don't fragment nodes — fix them upstream in the CSV and re-run if desired.
