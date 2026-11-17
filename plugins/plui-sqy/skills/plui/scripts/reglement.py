# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf"]
# ///
"""Extrait un article du reglement du PLUi en vigueur, avec ses numeros de page, pour citer la source exacte.

Usage :
  python reglement.py --url <URL du reglement> --zone URs2f9 --article 9     article U 9 (zone)
  python reglement.py --url <URL> --commun 12                                article 12 des dispositions communes
  python reglement.py --zone URs2f9                                          decode seulement le code de zone
L'URL du reglement est dans fiche.json (plui.reglement), donnee par le Geoportail de l'Urbanisme : c'est toujours
la version en vigueur. Le PDF est mis en cache (CLAUDE_PLUGIN_DATA ou ~/.cache/plui-sqy).
"""
import argparse
import hashlib
import os
import re
import sys
import urllib.request
from pathlib import Path

CODE = re.compile(r"^(?P<fam>AU|U|A|N)(?P<voc>[A-Z]?[a-z]*)(?P<forme>\d)?(?P<dens>[a-f])?(?P<haut>\d+)?$")


def decoder(code):
    """URs2f9 -> famille U, vocation Rs, forme 2, densite f, hauteur 9 m (voir l'article U 0 du reglement)."""
    m = CODE.match(code)
    if not m:
        sys.exit(f"Code de zone non reconnu : {code}")
    return m.groupdict()


def pdf_local(url):
    cache = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".cache" / "plui-sqy")
    cache.mkdir(parents=True, exist_ok=True)
    f = cache / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".pdf")
    if not f.exists():
        with urllib.request.urlopen(url, timeout=120) as r:
            f.write_bytes(r.read())
    return f


def lignes(pdf):
    import pymupdf
    for i, page in enumerate(pymupdf.open(pdf), 1):
        for l in page.get_text().splitlines():
            yield i, l.rstrip()


def extraire(pdf, debut, fin):
    """Texte entre la premiere ligne qui correspond a debut et la suivante qui correspond a fin, page par page."""
    sortie, dedans, page_cour = [], False, None
    for page, l in lignes(pdf):
        if not dedans and debut.match(l):
            dedans = True
        elif dedans and fin.match(l):
            break
        if dedans:
            if page != page_cour:
                sortie.append(f"\n[page {page}]")
                page_cour = page
            sortie.append(l)
    return "\n".join(sortie).strip()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", help="URL du reglement en vigueur (fiche.json : plui.reglement)")
    a.add_argument("--pdf", type=Path, help="ou chemin d'un PDF deja telecharge")
    a.add_argument("--zone", help="code de zone, ex. URs2f9")
    a.add_argument("--article", type=int, help="numero d'article de la zone (U, AU, A ou N)")
    a.add_argument("--commun", type=int, help="numero d'article des dispositions communes (titre II)")
    x = a.parse_args()

    if x.zone:
        z = decoder(x.zone)
        print(f"Zone {x.zone} : famille {z['fam']}, vocation {z['voc'] or '-'}, indice de forme {z['forme'] or '-'}, "
              f"indice de densite {z['dens'] or '-'}, hauteur {z['haut'] + ' m' if z['haut'] else '-'}")
        print("Dans chaque article, lire les paragraphes « indice " + (z["forme"] or "?") + " » et « indice "
              + (z["dens"] or "?") + " ». L'article " + z["fam"] + " 0 explique le systeme d'indices.")
    if not (x.article is not None or x.commun is not None):
        return
    if not (x.url or x.pdf):
        a.error("--url ou --pdf requis pour extraire un article")
    pdf = x.pdf or pdf_local(x.url)
    if x.commun is not None:
        debut = re.compile(rf"\s*ARTICLE\s+{x.commun}\s*[-–]")
        fin = re.compile(r"\s*(ARTICLE\s+\d+\s*[-–]|TITRE\s+[IVX]+)")
        # Les dispositions communes sont au titre II : on saute la table des matieres et le titre I.
        texte = extraire_apres(pdf, re.compile(r"\s*TITRE\s+II\s*:"), debut, fin)
    else:
        if not x.zone:
            a.error("--zone requis avec --article")
        fam = decoder(x.zone)["fam"]
        debut = re.compile(rf"\s*ARTICLE\s+{fam}\s+{x.article}\s*[-–]")
        fin = re.compile(rf"\s*(ARTICLE\s+{fam}\s+\d+\s*[-–]|TITRE\s+[IVX]+)")
        texte = extraire(pdf, debut, fin)
    if not texte:
        sys.exit("Article introuvable dans ce reglement : verifier le numero, ou la structure a change.")
    print(texte)


def extraire_apres(pdf, repere, debut, fin):
    """Comme extraire(), mais ne commence a chercher qu'apres la ligne repere (hors table des matieres)."""
    sortie, vu, dedans, page_cour = [], 0, False, None
    for page, l in lignes(pdf):
        if repere.match(l):
            vu += 1  # 1re occurrence = sommaire, 2e = corps du document
            continue
        if vu < 2:
            continue
        if not dedans and debut.match(l):
            dedans = True
        elif dedans and fin.match(l):
            break
        if dedans:
            if page != page_cour:
                sortie.append(f"\n[page {page}]")
                page_cour = page
            sortie.append(l)
    return "\n".join(sortie).strip()


if __name__ == "__main__":
    main()
