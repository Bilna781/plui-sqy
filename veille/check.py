"""Veille du PLUi de Saint-Quentin-en-Yvelines : detecte une nouvelle version ou une modification du document en vigueur.

Usage : python veille/check.py                  compare et ecrit veille/rapport.md (code de sortie 0)
        python veille/check.py --maj            enregistre l'etat courant comme reference (apres relecture)
        python veille/check.py --etiquette F    ecrit aussi l'etiquette d'etat (SVG) dans F
Etat : « version modifiee » des qu'un controle releve un ecart, sinon « a jour ». Controles (donnees structurees,
aucun mot-cle lu dans une page) :
  1. Geoportail de l'Urbanisme : versions, statuts et dates de mise a jour (versions/index.json)
  2. Geoportail : empreinte de la liste des fichiers du document en vigueur (veille/etat.json)
  3. En-tetes HTTP du PDF du reglement en vigueur : date, taille, ETag (veille/etat.json)
  4. Version vérifiée par le skill (version.json) egale a la version en vigueur
Ecrit « changements=true|false » dans $GITHUB_OUTPUT quand il tourne dans une GitHub Action.
Aucune dependance. Une requete par controle, espacees d'une seconde.
"""
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import date
from math import ceil
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
API = "https://www.geoportail-urbanisme.gouv.fr/api"
PARTITION = "DU_200058782"
UA = {"User-Agent": "plui-sqy-veille (projet open source non officiel)"}
INDEX, ETAT, RAPPORT = RACINE / "versions/index.json", RACINE / "veille/etat.json", RACINE / "veille/rapport.md"
VERSION_SKILL = RACINE / "plugins/plui-sqy/skills/plui/references/version.json"


def lire(url, methode="GET"):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method=methode), timeout=60) as r:
        return r.read() if methode == "GET" else dict(r.headers)


def charger(p, defaut):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defaut


def versions_gpu():
    champs = ("originalName", "id", "effectiveStatus", "publicationDate", "statusDate", "updateDate")
    docs = [{k: d.get(k) for k in champs} for d in json.loads(lire(f"{API}/document?partition={PARTITION}"))]
    return sorted(docs, key=lambda d: d["originalName"])


def fichiers(doc):
    """Empreinte des noms de fichiers du document : repere une piece ajoutee, retiree ou renommee."""
    # shortcut: les noms seulement, pas le contenu ; le PDF du reglement (controle 3) couvre sa propre modification.
    try:
        noms = sorted(f["name"] for f in json.loads(lire(f"{API}/document/{doc['id']}/files")))
    except (OSError, ValueError, KeyError) as e:
        return {"erreur": str(e)}
    return {"document": doc["id"], "nombre": len(noms), "empreinte": hashlib.sha1("\n".join(noms).encode()).hexdigest()}


def entetes_reglement(en_vigueur):
    """En-tetes des pieces ecrites du document en vigueur."""
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


def etiquette_svg(etat, en_vigueur):
    """Etiquette de l'etat du PLUi (meme gabarit que assets/etiquettes/*.svg) : valeur verte ou rouge."""
    j = en_vigueur["originalName"].split("_")[-1]
    valeur, fond = ((f"à jour {j[6:]}/{j[4:6]}/{j[:4]}", "#267A4D") if etat == "plui-a-jour"
                    else ("version modifiée", "#BF4521"))
    g, d = 40, ceil(14 + len(valeur) * 6.6)  # IBM Plex Mono 11 px : 6,6 px par caractere
    txt = f"PLUi : {valeur}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{g + d}" height="20" role="img" aria-label="{txt}">'
            f'<title>{txt}</title><clipPath id="r"><rect width="{g + d}" height="20" rx="4"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{g}" height="20" fill="#1B2638"/>'
            f'<rect x="{g}" width="{d}" height="20" fill="{fond}"/></g>'
            f'<g font-family="IBM Plex Mono,ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11">'
            f'<text x="7" y="14" fill="#EEF2F4">PLUi</text><text x="47" y="14" fill="#FFFFFF">{valeur}</text></g></svg>\n')


def main(maj=False, svg=None):
    rapport = []
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
        elif "updateDate" in a and a["updateDate"] != d["updateDate"]:
            rapport.append(f"- `{d['originalName']}` mis à jour sur le Géoportail ({a['updateDate']} → {d['updateDate']})")
    skill = charger(VERSION_SKILL, {}).get("document")
    if skill and skill != en_vigueur["originalName"]:
        rapport.append(f"- Le skill est vérifié sur `{skill}`, la version en vigueur est `{en_vigueur['originalName']}`")

    ref = charger(ETAT, {})
    time.sleep(1)
    etat = {"fichiers": fichiers(en_vigueur)}
    time.sleep(1)
    etat["reglement"] = entetes_reglement(en_vigueur)
    avant = ref.get("fichiers")
    if avant and avant.get("document") == en_vigueur["id"] and avant != etat["fichiers"]:
        rapport.append(f"- Fichiers du document en vigueur modifiés sans nouvelle version ({avant} → {etat['fichiers']})")
    for url, h in etat["reglement"].items():
        avant = ref.get("reglement", {}).get(url)
        if avant and avant != h:
            rapport.append(f"- Règlement modifié sans nouvelle version : {url} ({avant} → {h})")

    etiquette = "version-modifiee" if rapport else "plui-a-jour"
    texte = (f"# Veille du PLUi : {date.today().isoformat()}\n\nVersion en vigueur : `{en_vigueur['originalName']}`, "
             f"publiée le {en_vigueur['publicationDate']}.\n\n"
             + ("État : **version modifiée**\n\n" + "\n".join(rapport) + "\n\n"
                "Suite : relire, mettre à jour le skill (`version.json`, tableau du README), puis "
                "`python veille/check.py --maj` et commit.\n" if rapport else "État : **à jour**\n"))
    RAPPORT.write_text(texte, encoding="utf-8")
    print(texte)
    if svg:
        Path(svg).write_text(etiquette_svg(etiquette, en_vigueur), encoding="utf-8")
    if maj:
        INDEX.write_text(json.dumps(gpu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        ETAT.write_text(json.dumps(etat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Références mises à jour.")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changements={'true' if rapport else 'false'}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(maj="--maj" in args, svg=args[args.index("--etiquette") + 1] if "--etiquette" in args else None)
