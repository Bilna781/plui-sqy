"""Veille du PLUi de Saint-Quentin-en-Yvelines : detecte une nouvelle version, un document modifie ou une procedure.

Usage : python veille/check.py            compare et ecrit veille/rapport.md (code de sortie 0)
        python veille/check.py --maj      enregistre l'etat courant comme reference (apres relecture)
Sources :
  1. Geoportail de l'Urbanisme : historique des versions (versions/index.json)
  2. Page PLUi du site de SQY : liste des PDF publies (veille/inventaire.json)
  3. En-tetes HTTP des PDF du reglement en vigueur (veille/etat.json) : date, taille, ETag
Ecrit « changements=true|false » dans $GITHUB_OUTPUT quand il tourne dans une GitHub Action.
Aucune dependance. Une requete par document, espacees : usage raisonnable des services.
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GPU = "https://www.geoportail-urbanisme.gouv.fr/api/document?partition=DU_200058782"
PAGE_SQY = "https://saint-quentin-en-yvelines.fr/vivre-ici/logement-et-urbanisme/urbanisme/plans-locaux-durbanisme/plui/"
UA = {"User-Agent": "plui-sqy-veille (projet open source non officiel)"}
INDEX, INVENTAIRE, ETAT = RACINE / "versions/index.json", RACINE / "veille/inventaire.json", RACINE / "veille/etat.json"
VERSION_SKILL = RACINE / "plugins/plui-sqy/skills/plui/references/version.json"


def lire(url, methode="GET"):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method=methode), timeout=60) as r:
        return r.read() if methode == "GET" else dict(r.headers)


def charger(p, defaut):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defaut


def versions_gpu():
    champs = ("originalName", "id", "effectiveStatus", "publicationDate", "statusDate")
    docs = [{k: d.get(k) for k in champs} for d in json.loads(lire(GPU))]
    return sorted(docs, key=lambda d: d["originalName"])


def pdf_site():
    html = lire(PAGE_SQY).decode("utf-8", "ignore")
    return sorted(set(re.findall(r'href="(https?://[^"]+\.pdf)"', html, re.I)))


def entetes_reglement(en_vigueur):
    """En-tetes des pieces ecrites du document en vigueur, via les liens que le GPU publie dans zone-urba."""
    # shortcut: chemin deduit du nom de version (200058782_PLUi_AAAAMMJJ), comme publie par le GPU au 19/02/2026 ;
    # si SQY change d'arborescence, le HEAD echoue et le rapport le signale.
    nom = en_vigueur["originalName"]
    siren, jour = nom.split("_")[0], nom.split("_")[-1]
    url = (f"https://arcgis.sqy.fr/DOC_MULTIMEDIA/URBANISME/PLUI/{siren}_PLUI_{jour}/Pieces_ecrites/3_Reglement/"
           f"{siren}_reglement_{jour}.pdf")
    try:
        h = lire(url, "HEAD")
        return {url: {k: h.get(k) for k in ("Last-Modified", "ETag", "Content-Length")}}
    except OSError as e:
        return {url: {"erreur": str(e)}}


def main(maj=False):
    rapport, changements = [], False
    gpu = versions_gpu()
    en_vigueur = next(d for d in gpu if d["effectiveStatus"] == "EN_VIGUEUR")
    ancien = {d["id"]: d for d in charger(INDEX, [])}
    for d in gpu:
        a = ancien.get(d["id"])
        if a is None:
            rapport.append(f"- Nouvelle version sur le Géoportail de l'Urbanisme : `{d['originalName']}` "
                           f"({d['effectiveStatus']}, publiée le {d['publicationDate']})")
        elif a["effectiveStatus"] != d["effectiveStatus"]:
            rapport.append(f"- `{d['originalName']}` : statut {a['effectiveStatus']} → {d['effectiveStatus']}")
    skill = charger(VERSION_SKILL, {}).get("document")
    if skill and skill != en_vigueur["originalName"]:
        rapport.append(f"- Le skill est vérifié sur `{skill}`, la version en vigueur est `{en_vigueur['originalName']}`")

    time.sleep(1)
    site = pdf_site()
    connus = {x["url"] for x in charger(INVENTAIRE, [])}
    nouveaux, retires = sorted(set(site) - connus), sorted({u for u in connus if u.endswith(".pdf")} - set(site))
    rapport += [f"- Nouveau PDF sur le site de SQY : {u}" for u in nouveaux]
    rapport += [f"- PDF retiré du site de SQY : {u}" for u in retires]

    time.sleep(1)
    etat = entetes_reglement(en_vigueur)
    for url, h in etat.items():
        avant = charger(ETAT, {}).get(url)
        if avant and avant != h:
            rapport.append(f"- Règlement modifié sans nouvelle version : {url} ({avant} → {h})")

    changements = bool(rapport)
    texte = (f"# Veille du PLUi : {date.today().isoformat()}\n\nVersion en vigueur : `{en_vigueur['originalName']}`, "
             f"publiée le {en_vigueur['publicationDate']}.\n\n"
             + ("\n".join(rapport) if rapport else "Aucun changement détecté.") + "\n")
    (RACINE / "veille/rapport.md").write_text(texte, encoding="utf-8")
    print(texte)

    if maj:
        INDEX.write_text(json.dumps(gpu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        ETAT.write_text(json.dumps(etat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        inv = charger(INVENTAIRE, [])
        inv += [{"section": "ajouté par la veille", "titre": u.rsplit("/", 1)[-1], "url": u, "pdf": True, "prio": "?"}
                for u in nouveaux]
        inv = [x for x in inv if x["url"] not in retires]
        INVENTAIRE.write_text(json.dumps(inv, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Références mises à jour.")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changements={'true' if changements else 'false'}\n")


if __name__ == "__main__":
    main(maj="--maj" in sys.argv)
