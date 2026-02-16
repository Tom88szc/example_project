from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _as_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return "\n".join("" if v is None else str(v) for v in x)
    return str(x)


def _normalize_root(data: Any) -> List[Dict[str, Any]]:
    # Behave json.pretty root is usually: [ {feature}, {feature}, ... ]
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        feats = data.get("features")
        if isinstance(feats, list):
            return [d for d in feats if isinstance(d, dict)]
        if "elements" in data and "name" in data:
            return [data]
    return []


def _iter_elements(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    els = feature.get("elements")
    if isinstance(els, list):
        return [e for e in els if isinstance(e, dict)]
    for key in ("scenarios", "children"):
        v = feature.get(key)
        if isinstance(v, list):
            return [e for e in v if isinstance(e, dict)]
    return []


def _infer_status(steps: List[Dict[str, Any]], fallback: str = "passed") -> str:
    any_skipped = False
    for s in steps or []:
        res = s.get("result") or {}
        st = res.get("status") or s.get("status")
        if st == "failed":
            return "failed"
        if st == "skipped":
            any_skipped = True
    return "skipped" if any_skipped else fallback


def _first_error(steps: List[Dict[str, Any]]) -> str:
    for s in steps or []:
        res = s.get("result") or {}
        if (res.get("status") or "") == "failed":
            return _as_text(res.get("error_message")).strip()
    return ""


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "scenario"


@dataclass
class ScenarioRow:
    feature: str
    name: str
    status: str
    location: str
    steps: List[Dict[str, Any]]
    failure_reason: str
    scenario_id: str
    tcp_log: str


def _collect(features: List[Dict[str, Any]]) -> List[ScenarioRow]:
    rows: List[ScenarioRow] = []
    for feat in features:
        feat_name = str(feat.get("name") or "")
        for el in _iter_elements(feat):
            el_type = str(el.get("type") or "").lower()
            if el_type == "background":
                continue
            if el_type and "scenario" not in el_type:
                continue

            name = str(el.get("name") or "")
            location = str(el.get("location") or "")
            steps = el.get("steps") or []
            if not isinstance(steps, list):
                steps = []
            status = str(el.get("status") or "").lower() or _infer_status(steps)
            failure_reason = _first_error(steps)

            sid = _slug(f"{feat_name}-{name}")
            tcp_log = f"{sid}.log"
            rows.append(
                ScenarioRow(
                    feature=feat_name,
                    name=name,
                    status=status,
                    location=location,
                    steps=steps,
                    failure_reason=failure_reason,
                    scenario_id=sid,
                    tcp_log=tcp_log,
                )
            )
    return rows


CSS = """
:root {
  --bg: #070b16;
  --card: #0b132a;
  --text: #e8eefc;
  --muted: #91a0c6;
  --border: rgba(255,255,255,0.08);
  --green: #2ecc71;
  --red: #ff5a5f;
  --yellow: #f5c542;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:linear-gradient(180deg, #050814 0%, #050814 30%, #070b16 100%);
  color:var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
}
header{
  padding:22px 26px;
  border-bottom:1px solid var(--border);
  display:flex;
  justify-content:space-between;
  align-items:center;
}
h1{margin:0;font-size:18px;letter-spacing:.2px}
.badges{display:flex;gap:10px;align-items:center}
.badge{
  padding:6px 10px;
  border:1px solid var(--border);
  border-radius:999px;
  background:rgba(255,255,255,0.03);
  font-size:12px;
  color:var(--muted);
}
main{padding:22px 26px}
.controls{
  display:flex;
  gap:12px;
  align-items:center;
  margin-bottom:16px;
}
input, select{
  background:rgba(255,255,255,0.03);
  border:1px solid var(--border);
  color:var(--text);
  padding:10px 12px;
  border-radius:10px;
  outline:none;
}
table{
  width:100%;
  border-collapse:collapse;
  background:rgba(255,255,255,0.02);
  border:1px solid var(--border);
  border-radius:14px;
  overflow:hidden;
}
thead th{
  text-align:left;
  font-size:12px;
  color:var(--muted);
  padding:12px 14px;
  border-bottom:1px solid var(--border);
}
tbody td{
  padding:12px 14px;
  border-bottom:1px solid var(--border);
  vertical-align:top;
}
tbody tr:hover{background:rgba(255,255,255,0.03)}
a{color:#9cc3ff;text-decoration:none}
a:hover{text-decoration:underline}
.status{
  display:inline-flex;
  align-items:center;
  gap:8px;
  font-weight:600;
}
.dot{width:8px;height:8px;border-radius:99px;display:inline-block}
.dot.passed{background:var(--green)}
.dot.failed{background:var(--red)}
.dot.skipped{background:var(--yellow)}
.small{font-size:12px;color:var(--muted)}
pre{
  background:rgba(0,0,0,0.35);
  border:1px solid var(--border);
  padding:12px;
  border-radius:12px;
  overflow:auto;
  white-space:pre-wrap;
}
.section{
  background:rgba(255,255,255,0.02);
  border:1px solid var(--border);
  border-radius:14px;
  padding:14px;
  margin-bottom:14px;
}
hr{border:none;border-top:1px solid var(--border);margin:14px 0}
footer{padding:18px 26px;color:var(--muted);font-size:12px}
"""

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Automation Report (Behave)</title>
  <style>{css}</style>
</head>
<body>
<header>
  <h1>Automation Report (Behave)</h1>
  <div class="badges">
    <div class="badge">Total: <span id="total">0</span></div>
    <div class="badge">Passed: <span id="passed">0</span></div>
    <div class="badge">Failed: <span id="failed">0</span></div>
    <div class="badge">Skipped: <span id="skipped">0</span></div>
    <div class="badge">Generated: <span id="generated"></span></div>
  </div>
</header>

<main>
  <div class="controls">
    <input id="q" placeholder="Search feature/scenario..." style="min-width:320px" />
    <select id="status">
      <option value="all">All</option>
      <option value="passed">Passed</option>
      <option value="failed">Failed</option>
      <option value="skipped">Skipped</option>
    </select>
    <span class="small" id="hint"></span>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:44%">Scenario</th>
        <th style="width:12%">Status</th>
        <th>Failure reason (first)</th>
        <th style="width:12%">TCP log</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</main>

<footer>
  Click scenario name for drill-down (steps + errors).
</footer>

<script>
const meta = {meta_json};
const rows = {rows_json};

document.getElementById("generated").textContent = meta.generated_at;
document.getElementById("total").textContent = rows.length;

function counts(){
  let p=0,f=0,s=0;
  for(const r of rows){
    if(r.status==="passed") p++;
    else if(r.status==="failed") f++;
    else if(r.status==="skipped") s++;
  }
  document.getElementById("passed").textContent=p;
  document.getElementById("failed").textContent=f;
  document.getElementById("skipped").textContent=s;
}
counts();

function render(){
  const q = (document.getElementById("q").value||"").toLowerCase();
  const st = document.getElementById("status").value;

  const filtered = rows.filter(r => {
    const hay = (r.feature + " " + r.name).toLowerCase();
    if(q && !hay.includes(q)) return false;
    if(st !== "all" && r.status !== st) return false;
    return true;
  });

  const tbody = document.getElementById("tbody");
  tbody.innerHTML = "";

  document.getElementById("hint").textContent = meta.warning ? ("Warning: " + meta.warning) : "";

  if(filtered.length === 0){
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="4" class="small">No scenarios to display. (Try clearing filters.)</td>`;
    tbody.appendChild(tr);
    return;
  }

  for(const r of filtered){
    const tr = document.createElement("tr");
    const dot = `<span class="dot ${r.status}"></span>`;
    const status = `<span class="status">${dot}${r.status}</span>`;
    const link = `<a href="scenarios/${r.scenario_id}.html">${r.feature} — ${r.name}</a><div class="small">${r.location}</div>`;
    const reason = r.failure_reason ? `<pre>${r.failure_reason}</pre>` : `<span class="small">—</span>`;
    const tcp = `<a href="../tcp/${r.tcp_log}">log</a>`;
    tr.innerHTML = `<td>${link}</td><td>${status}</td><td>${reason}</td><td>${tcp}</td>`;
    tbody.appendChild(tr);
  }
}

document.getElementById("q").addEventListener("input", render);
document.getElementById("status").addEventListener("change", render);
render();
</script>
</body>
</html>
"""

SCENARIO_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{title}</title>
  <style>{css}</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div class="badges">
    <div class="badge">Status: {status}</div>
    <div class="badge"><a href="../index.html">Back to index</a></div>
    <div class="badge"><a href="../../tcp/{tcp_log}">TCP log</a></div>
  </div>
</header>

<main>
  <div class="section">
    <div class="small">Location</div>
    <div>{location}</div>
  </div>

  <div class="section">
    <div class="small">Steps</div>
    <hr/>
    {steps_html}
  </div>
</main>

<footer>Generated: {generated_at}</footer>
</body>
</html>
"""


def _render_steps(steps: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for s in steps or []:
        keyword = s.get("keyword", "")
        name = s.get("name", "")
        loc = (s.get("match") or {}).get("location") or s.get("location") or ""
        res = s.get("result") or {}
        st = res.get("status") or ""
        msg = _as_text(res.get("error_message")).strip()

        parts.append("<div style='margin-bottom:12px'>")
        parts.append(f"<div><b>{keyword}</b> {name}</div>")
        parts.append(f"<div class='small'>{loc}</div>")
        parts.append(f"<div class='small'>status: <b>{st}</b></div>")
        if msg:
            parts.append(f"<pre>{msg}</pre>")
        parts.append("</div>")
    return "\n".join(parts)


def generate_report(results_json_path: str, output_dir: str) -> None:
    out = Path(output_dir)
    (out / "scenarios").mkdir(parents=True, exist_ok=True)

    warning = ""
    p = Path(results_json_path)
    if not p.exists():
        warning = f"Missing results file: {results_json_path}"
        features: List[Dict[str, Any]] = []
    else:
        txt = p.read_text(encoding="utf-8", errors="ignore").strip()
        if not txt:
            warning = f"Empty results file: {results_json_path}"
            features = []
        else:
            features = _normalize_root(json.loads(txt))
            if not features:
                warning = "Results parsed but no features found (unexpected JSON shape)."

    rows = _collect(features)
    meta = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "warning": warning,
    }

    (out / "index.html").write_text(
        INDEX_HTML.format(
            css=CSS,
            meta_json=json.dumps(meta, ensure_ascii=False),
            rows_json=json.dumps([r.__dict__ for r in rows], ensure_ascii=False),
        ),
        encoding="utf-8",
    )

    for r in rows:
        title = f"{r.feature} — {r.name}"
        (out / "scenarios" / f"{r.scenario_id}.html").write_text(
            SCENARIO_HTML.format(
                title=title,
                css=CSS,
                status=r.status,
                location=r.location,
                tcp_log=r.tcp_log,
                steps_html=_render_steps(r.steps),
                generated_at=meta["generated_at"],
            ),
            encoding="utf-8",
        )
