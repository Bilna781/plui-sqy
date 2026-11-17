"""Collecte la popularite du depot et l'ajoute a l'historique (une ligne par jour).

Usage : python site/stats.py <historique.json>
Variables : GH_TOKEN (obligatoire : etoiles, forks, abonnes),
            STATS_TOKEN (facultatif : visites et clones, que GitHub ne garde que 14 jours).
Les visites et les clones de GitHub ne contiennent aucune donnee personnelle (comptes agreges par jour).
"""
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

DEPOT = os.environ.get("GITHUB_REPOSITORY", "Bilna781/plui-sqy")


def api(chemin, jeton, accept="application/vnd.github+json"):
    req = urllib.request.Request(f"https://api.github.com/repos/{DEPOT}{chemin}",
                                 headers={"Authorization": f"Bearer {jeton}", "Accept": accept})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collecter(fichier):
    hist = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}
    jeton = os.environ["GH_TOKEN"]
    d = api("", jeton)
    jour = hist.setdefault(date.today().isoformat(), {})
    jour.update(etoiles=d["stargazers_count"], forks=d["forks_count"], abonnes=d["subscribers_count"])
    trafic = os.environ.get("STATS_TOKEN")
    if trafic:
        # GitHub renvoie les 14 derniers jours : on reecrit ces jours-la, les plus anciens restent acquis.
        for cle, nom in (("views", "visites"), ("clones", "clones")):
            for j in api(f"/traffic/{cle}", trafic)[cle]:
                ligne = hist.setdefault(j["timestamp"][:10], {})
                ligne[nom], ligne[f"{nom}_uniques"] = j["count"], j["uniques"]
    else:
        print("STATS_TOKEN absent : visites et clones non collectes.")
    hist = dict(sorted(hist.items()))
    fichier.write_text(json.dumps(hist, indent=1) + "\n", encoding="utf-8")
    return hist


if __name__ == "__main__":
    h = collecter(Path(sys.argv[1]))
    print(f"{len(h)} jours dans l'historique, dernier : {list(h.items())[-1]}")
