# -*- coding: utf-8 -*-
"""Arma el HTML del reporte de daily a partir de un JSON.

Uso: py render.py <datos.json> <salida.html>   (en Mac/Linux: python3)
El formato del JSON está en SKILL.md. Los campos `title`, `why` y `note` admiten solo <code> y <b>;
el resto se escapa y los links que no son http(s) se anulan.
"""
import html
import json
import sys

STATUS_CLASS = {
    "backlog": "st-backlog", "to do": "st-backlog", "open": "st-backlog",
    "in progress": "st-prog", "in review": "st-rev", "review": "st-rev",
    "blocked": "st-block", "completed": "st-done", "closed": "st-done", "done": "st-done",
}

CSS = """
  :root { --bg:#f6f7f9; --card:#fff; --text:#1d2330; --muted:#5d6677; --line:#e1e4ea; --accent:#1f6feb;
    --b-bg:#eef0f3; --b-tx:#5d6677; --p-bg:#e7f0ff; --p-tx:#1f5fc8; --r-bg:#f3ecff; --r-tx:#7040c0;
    --k-bg:#fdecec; --k-tx:#c0362c; --d-bg:#e8f5ec; --d-tx:#1a7f37; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
    --bg:#12151b; --card:#1b2029; --text:#e6e9ef; --muted:#9aa3b2; --line:#2c3340; --accent:#6ea8fe;
    --b-bg:#262c37; --b-tx:#a9b1bf; --p-bg:#1b2c48; --p-tx:#8fb8ff; --r-bg:#2b2142; --r-tx:#c3a6ff;
    --k-bg:#3a1d1d; --k-tx:#ff8f85; --d-bg:#16281c; --d-tx:#5cc27a; } }
  :root[data-theme="dark"] {
    --bg:#12151b; --card:#1b2029; --text:#e6e9ef; --muted:#9aa3b2; --line:#2c3340; --accent:#6ea8fe;
    --b-bg:#262c37; --b-tx:#a9b1bf; --p-bg:#1b2c48; --p-tx:#8fb8ff; --r-bg:#2b2142; --r-tx:#c3a6ff;
    --k-bg:#3a1d1d; --k-tx:#ff8f85; --d-bg:#16281c; --d-tx:#5cc27a; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:1000px; margin:0 auto; padding:24px 16px 48px; }
  .conf { font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
  h1 { margin:4px 0; font-size:24px; }
  .sub { color:var(--muted); margin:0 0 16px; }
  .hitos { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
  .hito { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:8px 12px; font-size:14px; }
  .hito b { color:var(--accent); }
  .legend { font-size:12.5px; color:var(--muted); margin-bottom:18px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; margin-bottom:14px; }
  .card h2 { margin:0; font-size:18px; }
  .role { color:var(--muted); font-size:13px; margin-bottom:6px; }
  h3 { font-size:13px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin:14px 0 4px; }
  ul { list-style:none; margin:0; padding:0; }
  li { display:flex; gap:10px; align-items:flex-start; padding:8px 0; border-top:1px solid var(--line); }
  li:first-child { border-top:0; }
  input[type=checkbox] { margin-top:4px; width:16px; height:16px; flex:none; accent-color:var(--accent); }
  .item { flex:1; min-width:0; }
  .why { color:var(--muted); font-size:13px; }
  .links { font-size:13px; margin-top:2px; display:flex; flex-wrap:wrap; gap:4px 12px; }
  a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
  li.done .item { opacity:.5; text-decoration:line-through; }
  .st { display:inline-block; font-size:11.5px; padding:1px 8px; border-radius:10px; white-space:nowrap; vertical-align:1px; }
  .st-backlog { background:var(--b-bg); color:var(--b-tx); } .st-prog { background:var(--p-bg); color:var(--p-tx); }
  .st-rev { background:var(--r-bg); color:var(--r-tx); } .st-block { background:var(--k-bg); color:var(--k-tx); }
  .st-done { background:var(--d-bg); color:var(--d-tx); }
  .tw { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; font-size:13.5px; }
  th { text-align:left; font-weight:600; color:var(--muted); font-size:12px; border-bottom:1px solid var(--line); padding:4px 8px 4px 0; }
  td { border-bottom:1px solid var(--line); padding:6px 8px 6px 0; vertical-align:top; }
  td.d { white-space:nowrap; color:var(--muted); }
  .note { font-size:13px; color:var(--muted); margin-top:18px; }
"""

LEGEND = ["backlog", "in progress", "in review", "blocked", "completed"]


def esc(s):
    return html.escape(s or "")


# title, why y note vienen de contenido ingerido (reuniones, canales): se escapa todo
# y solo se rehabilitan <code> y <b>, que es lo que documenta SKILL.md.
ALLOWED_TAGS = ("code", "b")


def rich(s):
    out = esc(s)
    for tag in ALLOWED_TAGS:
        out = out.replace(f"&lt;{tag}&gt;", f"<{tag}>").replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return out


def safe_url(u):
    u = (u or "").strip()
    return u if u.lower().startswith(("https://", "http://")) else "#"


def pill(status):
    if not status:
        return ""
    return f' <span class="st {STATUS_CLASS.get(status.lower(), "st-backlog")}">{esc(status)}</span>'


def task_url(t, base):
    return safe_url(t.get("url") or (base + t["id"] if t.get("id") else ""))


def links(items):
    return "".join(f'<a href="{esc(safe_url(l["url"]))}">{esc(l["label"])}</a>' for l in items or [])


def render(d):
    base = d.get("task_url_base", "https://app.clickup.com/t/")
    cards = []
    for p in d["people"]:
        talk = ""
        for t in p.get("talk", []):
            lk = links(t.get("links"))
            talk += ('<li><input type="checkbox"><div class="item">' + rich(t["title"]) + pill(t.get("status")) +
                     (f'<div class="why">{rich(t["why"])}</div>' if t.get("why") else "") +
                     (f'<div class="links">{lk}</div>' if lk else "") + "</div></li>")
        rows = ""
        for t in p.get("tasks", []):
            url = task_url(t, base)
            name = f'<a href="{esc(url)}">{esc(t["name"])}</a>' if url else esc(t["name"])
            note = f'<div class="why">{rich(t["note"])}</div>' if t.get("note") else ""
            rows += f'<tr><td>{name}{note}</td><td>{pill(t.get("status"))}</td><td class="d">{esc(t.get("updated"))}</td></tr>'
        card = f'<section class="card"><h2>{esc(p["name"])}</h2><div class="role">{esc(p.get("role"))}</div>'
        if talk:
            card += f"<h3>Para hablar hoy</h3><ul>{talk}</ul>"
        if rows:
            card += ('<h3>En qué está según ClickUp</h3><div class="tw"><table><thead><tr><th>Tarea</th>'
                     f'<th>Estado</th><th>Últ. act.</th></tr></thead><tbody>{rows}</tbody></table></div>')
        cards.append(card + "</section>")

    hitos = "".join(f'<div class="hito"><b>{esc(m["label"])}</b> · {esc(m["text"])}</div>' for m in d.get("milestones", []))
    if d.get("doc_links"):
        hitos += '<div class="hito">' + " · ".join(f'<a href="{esc(safe_url(l["url"]))}">{esc(l["label"])}</a>' for l in d["doc_links"]) + "</div>"
    legend = "".join(f'<span class="st {STATUS_CLASS[s]}">{s}</span>' for s in LEGEND)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(d["title"])}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="conf">DinoCloud Internal - Confidential</div>
  <h1>{esc(d["heading"])}</h1>
  <p class="sub">{esc(d.get("subtitle"))}</p>
  <div class="hitos">{hitos}</div>
  <div class="legend">Estados ClickUp al {esc(d.get("status_asof"))}: {legend}</div>
{chr(10).join(cards)}
  <p class="note">{esc(d.get("footnote", "Los checks son solo de esta pantalla, no se guardan."))}</p>
</div>
<script>
  document.querySelectorAll('input[type=checkbox]').forEach(cb =>
    cb.addEventListener('change', () => cb.closest('li').classList.toggle('done', cb.checked)));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: render.py <datos.json> <salida.html>")
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(render(data))
    print(sys.argv[2])
