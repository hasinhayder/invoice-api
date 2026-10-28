from html import escape

from .templates import INFO

SKILL_URL = "https://github.com/hasinhayder/invoice-generator-skill"

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Invoice API for AI Agents</title>
<meta name="description" content="A stateless API that turns structured invoice data into PDF invoices. Built for AI agents using the invoice-generator skill.">
<style>
  :root {{ --bg:#f7f8fa; --card:#fff; --text:#16181d; --muted:#5f6674; --line:#e4e7ec; --accent:#2563eb; --code:#0f172a; --codefg:#e2e8f0; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#0d1117; --card:#161b22; --text:#e6edf3; --muted:#8b949e; --line:#262c36; --accent:#58a6ff; --code:#010409; --codefg:#e6edf3; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:0 20px; }}
  header {{ padding:64px 0 36px; }}
  .badge {{ display:inline-block; font-size:12px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--accent); border:1px solid var(--accent); border-radius:999px; padding:3px 12px; }}
  h1 {{ font-size:clamp(30px,5vw,44px); line-height:1.15; margin:16px 0 12px; letter-spacing:-.02em; }}
  .lead {{ font-size:18px; color:var(--muted); max-width:680px; margin:0 0 24px; }}
  .btns {{ display:flex; flex-wrap:wrap; gap:10px; }}
  .btn {{ text-decoration:none; font-weight:600; font-size:15px; padding:10px 18px; border-radius:8px; border:1px solid var(--line); color:var(--text); background:var(--card); }}
  .btn.primary {{ background:var(--accent); border-color:var(--accent); color:#fff; }}
  section {{ margin:0 0 20px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:24px 26px; }}
  h2 {{ font-size:18px; margin:0 0 12px; }}
  p {{ margin:0 0 12px; }}
  a {{ color:var(--accent); }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:12px; }}
  .tpl {{ border:1px solid var(--line); border-radius:8px; padding:12px 14px; }}
  .tpl b {{ display:block; text-transform:capitalize; }}
  .tpl span {{ color:var(--muted); font-size:14px; }}
  table {{ width:100%; border-collapse:collapse; font-size:15px; }}
  td {{ padding:8px 6px; border-top:1px solid var(--line); vertical-align:top; }}
  tr:first-child td {{ border-top:0; }}
  td:first-child {{ white-space:nowrap; }}
  code {{ font:13.5px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  .m {{ font-weight:700; font-size:12px; padding:2px 7px; border-radius:5px; background:var(--line); margin-right:6px; }}
  pre {{ margin:0; background:var(--code); color:var(--codefg); border-radius:8px; padding:16px; overflow-x:auto; }}
  ol {{ margin:0; padding-left:20px; }} li {{ margin-bottom:6px; }}
  footer {{ color:var(--muted); font-size:14px; padding:12px 0 56px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <span class="badge">API &middot; Online</span>
    <h1>Invoice API for AI agents</h1>
    <p class="lead">Send structured invoice data, get a finished PDF back. This service is built to be used by AI agents together with the
      <a href="{skill}"><b>invoice-generator skill</b></a>, which turns a plain text file of invoice details into the right API call.</p>
    <div class="btns">
      <a class="btn primary" href="{skill}">Get the agent skill</a>
      <a class="btn" href="/docs">API documentation</a>
      <a class="btn" href="/templates">Templates (JSON)</a>
    </div>
  </header>

  <section>
    <h2>How it works with the skill</h2>
    <ol>
      <li>You keep your invoice details in any text file, however messy.</li>
      <li>The agent reads the skill, organizes the information and asks you for anything missing.</li>
      <li>It calls this API and downloads your PDF invoice.</li>
    </ol>
    <p style="margin-top:12px">Install the skill from <a href="{skill}">github.com/hasinhayder/invoice-generator-skill</a>.</p>
  </section>

  <section>
    <h2>Templates</h2>
    <div class="grid">{templates}</div>
  </section>

  <section>
    <h2>Endpoints</h2>
    <table>
      <tr><td><span class="m">GET</span><code>/health</code></td><td>Service status</td></tr>
      <tr><td><span class="m">GET</span><code>/templates</code></td><td>Available templates</td></tr>
      <tr><td><span class="m">POST</span><code>/invoices</code></td><td>Multipart: <code>data</code> (JSON) and optional <code>logo</code> (PNG/JPEG, up to 2&nbsp;MB). Returns a PDF.</td></tr>
      <tr><td><span class="m">POST</span><code>/invoices/json</code></td><td>JSON body without a logo. Returns a PDF.</td></tr>
    </table>
  </section>

  <section>
    <h2>Example</h2>
<pre><code>curl -fS -o invoice.pdf \\
  -F 'data=&lt;invoice.json' \\
  -F 'logo=@logo.png' \\
  {base}/invoices</code></pre>
  </section>

  <footer>Stateless: invoices are rendered on request and never stored. See <a href="/docs">/docs</a> for the full schema.</footer>
</div>
</body>
</html>
"""


def render_home(base_url: str) -> str:
    tpls = "".join(
        f'<div class="tpl"><b>{escape(t["name"])}</b><span>{escape(t["description"])}</span></div>'
        for t in INFO
    )
    return _PAGE.format(skill=SKILL_URL, templates=tpls, base=escape(base_url.rstrip("/")))
