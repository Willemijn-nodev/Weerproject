import json
import os
import glob
from datetime import datetime, timedelta

# ============ CONFIGURATIE ============
DATA_FILE = "weerdata_geschiedenis.json"
SATELLIET_MAP = "satellietbeelden"
OUTPUT_HTML = "overzicht.html"

def laad_geschiedenis():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def vind_laatste_bestand(patroon):
    bestanden = glob.glob(os.path.join(SATELLIET_MAP, patroon))
    if not bestanden:
        return None
    return max(bestanden, key=os.path.getmtime)

def bereken_24uurs_samenvatting(geschiedenis):
    """Filtert de eigen geschiedenis op de afgelopen 24 uur en berekent Tmin/Tmax + waarschuwingen-overzicht."""
    grens = datetime.now() - timedelta(hours=24)
    recente_metingen = [
        m for m in geschiedenis
        if datetime.fromisoformat(m["opgehaald_op"]) > grens
    ]

    if not recente_metingen:
        return None

    temperaturen = []
    waarschuwingen = []

    for m in recente_metingen:
        live = m.get("liveweer", [{}])[0] if isinstance(m.get("liveweer"), list) else m.get("liveweer", {})
        if isinstance(live, dict):
            if "temp" in live:
                try:
                    temperaturen.append(float(live["temp"]))
                except (ValueError, TypeError):
                    pass
            if live.get("alarm") == "1" or live.get("alarm") == 1:
                waarschuwingen.append({
                    "tijd": m["opgehaald_op"],
                    "kop": live.get("lkop", "Onbekend"),
                    "tekst": live.get("ltekst", ""),
                    "kleur": live.get("wrschklr", "")
                })

    return {
        "tmin_24u": min(temperaturen) if temperaturen else None,
        "tmax_24u": max(temperaturen) if temperaturen else None,
        "aantal_metingen": len(recente_metingen),
        "waarschuwingen_24u": waarschuwingen
    }

def render_waarschuwingen_24u(samenvatting):
    if not samenvatting or not samenvatting["waarschuwingen_24u"]:
        return '<p class="empty">Geen waarschuwingen geregistreerd in de afgelopen 24 uur (op basis van onze eigen metingen).</p>'
    items = ""
    for w in samenvatting["waarschuwingen_24u"]:
        tijd_kort = datetime.fromisoformat(w["tijd"]).strftime("%H:%M")
        items += f'<div class="warning-item"><b>{tijd_kort}</b> — {w["kop"]} <span class="badge">{w["kleur"]}</span></div>'
    return items

def render_waarde(waarde):
    if isinstance(waarde, dict):
        rijen = "".join(
            f'<tr><td class="label">{k}</td><td class="value">{render_waarde(v)}</td></tr>'
            for k, v in waarde.items()
        )
        return f'<table class="data-table">{rijen}</table>'
    elif isinstance(waarde, list):
        kaarten = "".join(f'<div class="subcard">{render_waarde(item)}</div>' for item in waarde)
        return f'<div class="grid">{kaarten}</div>'
    else:
        return str(waarde)

def bouw_html(laatste_weerdata, samenvatting_24u, pad_laatste_beeld, pad_loop):
    tijdstip = datetime.now().strftime("%d-%m-%Y %H:%M")

    weer_html = '<p class="empty">Geen weerdata gevonden</p>'
    if laatste_weerdata:
        weer_html = render_waarde(laatste_weerdata)

    beeld_html = '<p class="empty">Geen satellietbeeld gevonden</p>'
    if pad_laatste_beeld:
        beeld_html = f'<img class="sat-img" src="{pad_laatste_beeld}">'

    loop_html = '<p class="empty">Geen satellietloop gevonden</p>'
    if pad_loop:
        loop_html = f'<img class="sat-img" src="{pad_loop}">'

    tmin_max_html = '<p class="empty">Nog onvoldoende geschiedenis (minimaal 24 uur aan runs nodig voor een betrouwbaar beeld)</p>'
    if samenvatting_24u and samenvatting_24u["tmin_24u"] is not None:
        tmin_max_html = f"""
        <div class="grid">
          <div class="subcard"><b>Tmin (24u)</b><br>{samenvatting_24u['tmin_24u']}°C</div>
          <div class="subcard"><b>Tmax (24u)</b><br>{samenvatting_24u['tmax_24u']}°C</div>
          <div class="subcard"><b>Aantal metingen</b><br>{samenvatting_24u['aantal_metingen']}</div>
        </div>
        <p style="font-size:12px;color:#6b7785;margin-top:8px;">Let op: gebaseerd op onze eigen opgeslagen runs, niet op de volledige KNMI-stationreeks. Hoe vaker je het script laat draaien, hoe nauwkeuriger dit wordt.</p>
        """

    waarschuwingen_html = render_waarschuwingen_24u(samenvatting_24u)

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>Weeroverzicht</title>
<style>
  :root {{ --blauw: #1a5f9e; --lichtblauw: #eaf2fa; --grijs: #6b7785; --rand: #dde3ea; --oranje: #e8752c; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 30px; background: #f0f3f7; color: #1e2733; }}
  .wrap {{ max-width: 1200px; margin: 0 auto; }}
  header {{ margin-bottom: 25px; }}
  header h1 {{ margin: 0; color: var(--blauw); font-size: 28px; }}
  header p {{ margin: 4px 0 0; color: var(--grijs); font-size: 14px; }}
  .card {{ background: white; border-radius: 12px; padding: 22px 26px; margin-bottom: 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid var(--rand); }}
  .card h2 {{ margin: 0 0 15px; font-size: 17px; color: var(--blauw); display: flex; align-items: center; gap: 8px; }}
  .data-table {{ width: 100%; border-collapse: collapse; }}
  .data-table tr:nth-child(even) {{ background: var(--lichtblauw); }}
  .data-table td {{ padding: 8px 12px; border-radius: 4px; font-size: 14px; }}
  .data-table .label {{ color: var(--grijs); font-weight: 600; width: 35%; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
  .subcard {{ background: var(--lichtblauw); border-radius: 8px; padding: 12px; }}
  .sat-img {{ width: 100%; min-height: 500px; object-fit: contain; border-radius: 8px; display: block; border: 1px solid var(--rand); background: #000; }}
  .empty {{ color: var(--grijs); font-style: italic; }}
  .warning-item {{ background: #fff3e8; border-left: 4px solid var(--oranje); padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; font-size: 14px; }}
  .badge {{ background: var(--oranje); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 6px; }}
  .full-width {{ grid-column: 1 / -1; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🌦️ Weeroverzicht — De Bilt</h1>
    <p>Gegenereerd op {tijdstip} · bron: KNMI / Weerlive.nl</p>
  </header>

  <div class="card">
    <h2>📊 Actuele data</h2>
    {weer_html}
  </div>

  <div class="card">
    <h2>🌡️ Tmin / Tmax (afgelopen 24 uur)</h2>
    {tmin_max_html}
  </div>

  <div class="card">
    <h2>⚠️ Weerwaarschuwingen (afgelopen 24 uur)</h2>
    {waarschuwingen_html}
  </div>

  <div class="card">
    <h2>🛰️ Satellietbeeld (laatste)</h2>
    {beeld_html}
  </div>

  <div class="card">
    <h2>🔁 Satellietloop (6 uur)</h2>
    {loop_html}
  </div>

</div>
</body>
</html>"""
    return html

def main():
    geschiedenis = laad_geschiedenis()
    laatste_weerdata = geschiedenis[-1] if geschiedenis else None
    samenvatting_24u = bereken_24uurs_samenvatting(geschiedenis)

    pad_laatste_beeld = vind_laatste_bestand("satelliet_laatste_*.jpg")
    pad_loop = vind_laatste_bestand("satelliet_loop_*.gif")

    ruwe_html = bouw_html(laatste_weerdata, samenvatting_24u, pad_laatste_beeld, pad_loop)
    beveiligde_html = voeg_wachtwoordbeveiliging_toe(ruwe_html)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(beveiligde_html)

    print(f"Overzicht (beveiligd) gegenereerd: {OUTPUT_HTML}")

WACHTWOORD = "weersverwachting"   # <-- pas dit aan naar wat jij wilt

def voeg_wachtwoordbeveiliging_toe(html_inhoud):
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>Weeroverzicht - Login</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #1a2733; height: 100vh; margin:0; display:flex; align-items:center; justify-content:center; }}
  #login-box {{ background: white; padding: 40px; border-radius: 12px; text-align:center; width: 280px; }}
  #login-box input {{ width: 100%; padding: 10px; margin: 15px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }}
  #login-box button {{ width: 100%; padding: 10px; background: #1a5f9e; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; }}
  #fout {{ color: #c0392b; font-size: 13px; height: 16px; }}
</style>
</head>
<body>

<div id="login-box">
  <h3>🔒 Weeroverzicht</h3>
  <input type="password" id="wachtwoord-invoer" placeholder="Wachtwoord" autofocus>
  <div id="fout"></div>
  <button onclick="controleer()">Openen</button>
</div>

<div id="inhoud" style="display:none;">
{html_inhoud}
</div>

<script>
function controleer() {{
  const invoer = document.getElementById('wachtwoord-invoer').value;
  if (invoer === "{WACHTWOORD}") {{
    sessionStorage.setItem('toegang_ok', 'true');
    document.body.innerHTML = document.getElementById('inhoud').innerHTML;
  }} else {{
    document.getElementById('fout').innerText = "Onjuist wachtwoord";
  }}
}}
document.getElementById('wachtwoord-invoer').addEventListener('keyup', function(e) {{
  if (e.key === 'Enter') controleer();
}});
if (sessionStorage.getItem('toegang_ok') === 'true') {{
  document.body.innerHTML = document.getElementById('inhoud').innerHTML;
}}
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()