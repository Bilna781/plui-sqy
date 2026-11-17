"""Construit le site GitHub Pages : le README (rendu par l'API Markdown de GitHub) dans la DA, plus la popularite.

Usage : python site/build.py <historique.json> <dossier_sortie>
Variable : GH_TOKEN (API Markdown). Aucune dependance.
"""
import html
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DEPOT = os.environ.get("GITHUB_REPOSITORY", "Bilna781/plui-sqy")


def readme_html():
    texte = (RACINE / "README.md").read_text(encoding="utf-8")
    corps = json.dumps({"text": texte, "mode": "markdown", "context": DEPOT}).encode()
    req = urllib.request.Request("https://api.github.com/markdown", data=corps, method="POST",
                                 headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        rendu = r.read().decode()
    # Liens relatifs du README (fichiers du depot) : vers GitHub, sinon 404 sur le site. Les images restent locales.
    return re.sub(r'href="(?!https?:|#|mailto:)([^"]+)"', rf'href="https://github.com/{DEPOT}/blob/main/\1"', rendu)


def barres(serie, titre, unite):
    """Histogramme d'une seule serie (pas de legende : le titre la nomme). Survol : infobulle native."""
    if not any(v for _, v in serie):
        return f"<figure class=graphe><figcaption>{titre}</figcaption><p class=vide>Pas encore de données.</p></figure>"
    w, h, g, b = 640, 180, 34, 22  # largeur, hauteur, marge gauche, marge basse
    haut = max(v for _, v in serie)
    pas = (w - g) / len(serie)
    larg = max(2.0, pas - 2)  # 2 px d'espace entre barres
    marques = ""
    for i, (j, v) in enumerate(serie):
        bh = (h - b - 8) * v / haut if haut else 0
        x, y = g + i * pas, h - b - bh
        etiquette = f"{date.fromisoformat(j):%d/%m} : {v} {unite}"
        marques += (f"<g><title>{etiquette}</title><rect class=cible x={x:.1f} y=0 width={pas:.1f} height={h - b} />"
                    + (f"<rect class=barre x={x:.1f} y={y:.1f} width={larg:.1f} height={bh:.1f} rx=2 />" if v else "")
                    + "</g>")
    reperes = "".join(f"<text x={g + i * pas + larg / 2:.1f} y={h - 6} text-anchor=middle>"
                      f"{date.fromisoformat(j):%d/%m}</text>" for i, (j, _) in enumerate(serie) if i % 7 == 0)
    return (f"<figure class=graphe><figcaption>{titre}</figcaption>"
            f"<svg viewBox='0 0 {w} {h}' role=img aria-label='{html.escape(titre)}'>"
            f"<line class=axe x1={g} y1={h - b} x2={w} y2={h - b} />"
            f"<text x={g - 6} y=14 text-anchor=end>{haut}</text><text x={g - 6} y={h - b} text-anchor=end>0</text>"
            f"{marques}{reperes}</svg></figure>")


def popularite(hist):
    if not hist:
        return "<p class=vide>La collecte démarre : les premiers chiffres apparaîtront demain.</p>"
    dernier = hist[max(hist)]
    fin = date.fromisoformat(max(hist))
    jours = [(fin - timedelta(days=n)).isoformat() for n in range(29, -1, -1)]
    serie = lambda cle: [(j, hist.get(j, {}).get(cle, 0)) for j in jours]
    somme = lambda cle: sum(v for _, v in serie(cle)[-14:])
    tuiles = [("Étoiles", dernier.get("etoiles", 0)), ("Forks", dernier.get("forks", 0)),
              ("Abonnés", dernier.get("abonnes", 0)), ("Visites, 14 jours", somme("visites")),
              ("Clones, 14 jours", somme("clones"))]
    lignes = "".join(f"<tr><td>{date.fromisoformat(j):%d/%m/%Y}</td>" + "".join(
        f"<td>{hist[j].get(c, '–')}</td>" for c in ("etoiles", "visites", "visites_uniques", "clones", "clones_uniques"))
        + "</tr>" for j in sorted(hist, reverse=True))
    return ("<div class=tuiles>" + "".join(f"<div class=tuile><span class=nombre>{v}</span><span>{n}</span></div>"
                                           for n, v in tuiles) + "</div>"
            + barres(serie("visites"), "Visites du dépôt par jour", "visites")
            + barres(serie("clones"), "Clones par jour (installations et mises à jour du plugin)", "clones")
            + "<details><summary>Voir le tableau</summary><table><thead><tr><th>Jour</th><th>Étoiles</th>"
              "<th>Visites</th><th>Visiteurs uniques</th><th>Clones</th><th>Clones uniques</th></tr></thead>"
              f"<tbody>{lignes}</tbody></table></details>"
            + f"<p class=note>Mis à jour le {date.today():%d/%m/%Y}. Visites et clones : chiffres agrégés de "
              "GitHub, sans donnée personnelle ni traceur sur ce site.</p>")


PAGE = """<!doctype html>
<html lang=fr><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>PLUi SQY (non officiel)</title>
<meta name=description content="Skill non officiel pour Claude Code et Codex : lit le PLUi de Saint-Quentin-en-Yvelines.">
<link rel=icon href="assets/icone.svg" type="image/svg+xml">
<style>
@font-face{font-family:Archivo;src:url(polices/archivo.woff2) format("woff2");font-weight:700;font-display:swap}
@font-face{font-family:"Public Sans";src:url(polices/public-sans.woff2) format("woff2");font-weight:100 900;font-display:swap}
@font-face{font-family:Plex;src:url(polices/plex-mono-400.woff2) format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:Plex;src:url(polices/plex-mono-500.woff2) format("woff2");font-weight:500;font-display:swap}
:root{--fond:#EEF2F4;--carte:#fff;--texte:#1B2638;--doux:#4F5B6B;--trait:#C9D2D8;--accent:#BF4521;--donnee:#2C6FB7}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--fond:#1B2638;--carte:#232F44;--texte:#EEF2F4;
 --doux:#A9B4C2;--trait:#3A475D;--accent:#F07A55;--donnee:#6FA3DD}}
:root[data-theme=dark]{--fond:#1B2638;--carte:#232F44;--texte:#EEF2F4;--doux:#A9B4C2;--trait:#3A475D;--accent:#F07A55;
 --donnee:#6FA3DD}
*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--texte);font:16px/1.6 "Public Sans",system-ui,sans-serif}
header{display:flex;align-items:center;gap:12px;max-width:920px;margin:0 auto;padding:20px 16px}
header img{width:36px;height:36px}
header b{font:700 20px Archivo,sans-serif}
header nav{margin-left:auto;display:flex;gap:14px;flex-wrap:wrap;justify-content:flex-end;font-size:15px}
header b{white-space:nowrap}
a{color:var(--accent)}
main{max-width:920px;margin:0 auto;padding:0 16px 48px}
section{background:var(--carte);border:1px solid var(--trait);border-radius:16px;padding:28px clamp(16px,4vw,36px);
 margin-bottom:24px;overflow-wrap:anywhere}
h1,h2,h3{font-family:Archivo,sans-serif;font-weight:700;line-height:1.2}
h2.titre{margin-top:0}
code,pre,.nombre,svg text,th{font-family:Plex,ui-monospace,monospace}
pre{background:var(--fond);border-radius:8px;padding:12px;overflow-x:auto}
code{font-size:.9em}
img{max-width:100%;height:auto}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:14px}
th,td{border-bottom:1px solid var(--trait);padding:6px 10px;text-align:left}
blockquote{margin:0;padding:4px 16px;border-left:4px solid var(--accent);color:var(--doux)}
.tuiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:24px}
.tuile{border:1px solid var(--trait);border-radius:10px;padding:14px;display:flex;flex-direction:column;color:var(--doux)}
.nombre{font-size:30px;font-weight:500;color:var(--texte)}
.graphe{margin:0 0 24px}
figcaption{font-weight:600;margin-bottom:8px}
svg{width:100%;height:auto;overflow:visible}
svg text{font-size:11px;fill:var(--doux)}
.axe{stroke:var(--trait);stroke-width:1}
.barre{fill:var(--donnee)}
.cible{fill:transparent}
g:hover .barre{opacity:.8}
.vide,.note{color:var(--doux);font-size:14px}
</style></head><body>
<header><img src="assets/icone.svg" alt=""><b>PLUi SQY</b>
<nav><a href="#presentation">Présentation</a><a href="#popularite">Popularité</a>
<a href="https://github.com/__DEPOT__">GitHub</a></nav></header>
<main>
<section id=presentation>__README__</section>
<section id=popularite><h2 class=titre>Popularité</h2>__POPULARITE__</section>
</main></body></html>
"""


def construire(historique, sortie):
    hist = json.loads(historique.read_text(encoding="utf-8")) if historique.exists() else {}
    sortie.mkdir(parents=True, exist_ok=True)
    shutil.copytree(RACINE / "assets", sortie / "assets", dirs_exist_ok=True)
    shutil.copytree(RACINE / "site/polices", sortie / "polices", dirs_exist_ok=True)
    page = (PAGE.replace("__README__", readme_html()).replace("__POPULARITE__", popularite(hist))
            .replace("__DEPOT__", DEPOT))
    (sortie / "index.html").write_text(page, encoding="utf-8")
    print(f"Site : {sortie / 'index.html'} ({len(hist)} jours de statistiques)")


if __name__ == "__main__":
    construire(Path(sys.argv[1]), Path(sys.argv[2]))
