# /// script
# requires-python = ">=3.10"
# dependencies = ["shapely>=2", "pyproj", "numpy", "matplotlib"]
# ///
"""Place un projet sur le cadastre d'une parcelle et mesure distances, emprise et bande constructible.

Usage : python projet.py DOSSIER_FICHE projet.json [--voie N] [--sortie DOSSIER]
        python projet.py --selftest   (parcelle synthetique, sans reseau)
        python projet.py --selftest-reseau [--out DOSSIER]   (lieu public : routes, voisines, batiments ; sante des API)
DOSSIER_FICHE est le dossier <idu> ecrit par parcelle.py (fiche.json et brut/). Ecrit mesures.json et placement.png.

projet.json (metres ; repere local du plan : x vers la droite, y vers le fond de la parcelle, la voie en bas) :
{
  "valide": false,                        # true seulement apres confirmation explicite de l'utilisateur
  "voie_segment": 3,                      # facultatif : numero du cote sur la voie (tableau affiche par le script)
  "batiments": [{"nom": "maison", "type": "batiment", "emprise": [[0,0],[9,0],[9,10],[0,10]],
                 "hauteur_faitage": 8.2, "hauteur_egout": 5.5}],      # types : batiment, annexe, terrasse, piscine, acces, autre
  "emprise_declaree_m2": 90,              # facultatif : valeur du cartouche, comparee a la geometrie
  "position": {"rotation_deg": 0,         # angle du repere du plan par rapport a la voie (0 : facade parallele a la voie)
               "ancrages": [{"point": [0,0], "limite": "voie", "distance_m": 5.0},
                            {"point": [0,0], "limite": "gauche", "distance_m": 2.5}]}   # gauche vue depuis la rue
}
Chaque cote d'ancrage est une distance perpendiculaire a la limite. Deux limites non paralleles au moins sont
necessaires ; les cotes en plus servent de controle. Limites cadastrales indicatives : seul un geometre fait foi.
"""
import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import shapely
import shapely.ops
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, shape

TOL_RESIDU = 0.15      # m : ecart tolerable entre une cote lue et la cote recalculee sur le cadastre
TOL_EMPRISE = 0.03     # ecart relatif tolerable entre emprise declaree et emprise du dessin
ECART_SURFACE = 0.05   # ecart relatif contenance / geometrie au-dela duquel on le signale
LONG_MIN = 1.0         # m : longueur minimale d'un cote pour en faire une limite
BANDE = 25.0           # m : bande constructible depuis l'alignement (article 10 des dispositions communes)
CONSTRUIT = {"batiment", "annexe"}
TYPES = CONSTRUIT | {"terrasse", "piscine", "acces", "autre"}
_INV = Transformer.from_crs(2154, 4326, always_xy=True)


class Erreur(Exception):
    pass


def cardinal(v):
    """Direction (N, NE, ...) d'un vecteur du plan en Lambert 93 (x vers l'est, y vers le nord)."""
    return ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][int(round(math.degrees(math.atan2(v[0], v[1])) % 360 / 45)) % 8]


def segments(poly, autres):
    """Cotes du contour avec leur statut : limite (partagee avec une voisine), libre (voie probable) ou mixte."""
    pts = np.array(poly.exterior.coords)[:-1]
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        L = float(np.linalg.norm(b - a))
        if L < 1e-6:
            continue
        d = (b - a) / L
        m = np.array([-d[1], d[0]])
        mid = (a + b) / 2
        if not poly.contains(Point(mid + 0.05 * m)):
            m = -m  # normale dirigee vers l'interieur de la parcelle
        s = LineString([a, b])
        partage = max((s.intersection(o.buffer(0.15)).length for o in autres), default=0.0)
        statut = "limite" if partage >= 0.5 * L else "libre" if partage < 0.2 * L else "mixte"
        out.append(dict(i=i, a=a, b=b, L=L, d=d, m=m, mid=mid, statut=statut, role=None, geom=s))
    return out


def choisir_voie(segs, adresse, forcee, routes):
    """Cote sur la voie : indique par l'utilisateur, sinon le plus proche d'une route BD TOPO, sinon un cote sans voisine."""
    if forcee is not None:
        s = [x for x in segs if x["i"] == forcee]
        if not s:
            raise Erreur(f"Cote {forcee} inexistant : choisir un numero du tableau des cotes.")
        return s[0], [], "indiquee"
    eligibles = [s for s in segs if s["L"] >= 2.0]
    if routes:  # la voie est souvent une parcelle cadastree : l'absence de voisine ne suffit pas
        note = lambda s: min(r.distance(Point(s["mid"])) for r in routes)
        cand = sorted(eligibles, key=lambda s: (round(note(s), 1), s["geom"].distance(Point(adresse))))
        # a egalite de proximite (a 1,5 m pres), la facade la plus longue est la voie : on evite un petit decrochement
        choix = max((s for s in cand if note(s) <= note(cand[0]) + 1.5), key=lambda s: s["L"])
        return choix, [s for s in cand if s is not choix and note(s) < note(choix) + 3.0], "route BD TOPO"
    cand = [s for s in eligibles if s["statut"] == "libre"]
    if not cand:
        raise Erreur("Aucun cote de la parcelle n'est libre de voisine (voie cadastree ou parcelle d'angle) : "
                     "indiquer le cote sur la voie avec --voie N (numero du tableau des cotes).\n" + tableau(segs))
    cand.sort(key=lambda s: s["geom"].distance(Point(adresse)))
    return cand[0], cand[1:], "cote sans voisine"


def attribuer_roles(segs, v):
    n = v["m"]
    u = np.array([n[1], -n[0]])  # droite de l'observateur qui regarde de la rue vers la parcelle
    v["role"] = "voie"
    autres = [s for s in segs if s is not v and s["L"] >= LONG_MIN]
    lat = [s for s in autres if abs(s["d"] @ n) >= 0.5]
    plus_long = lambda c: max(c, key=lambda s: s["L"]) if c else None
    for nom, s in (("gauche", plus_long([s for s in lat if (s["mid"] - v["mid"]) @ u < 0])),
                   ("droite", plus_long([s for s in lat if (s["mid"] - v["mid"]) @ u > 0])),
                   ("fond", max((s for s in autres if abs(s["d"] @ n) < 0.5), key=lambda s: (s["mid"] - v["mid"]) @ n,
                                default=None))):
        if s is not None:
            s["role"] = nom
    return u


def poser(pos, segs, v, u):
    """Resout la translation du projet par moindres carres sur les cotes d'ancrage (distances aux limites)."""
    n = v["m"]
    th = math.radians(pos.get("rotation_deg", 0))
    e1, e2 = math.cos(th) * u + math.sin(th) * n, -math.sin(th) * u + math.cos(th) * n
    par_role = {s["role"]: s for s in segs if s["role"]}
    A, b = [], []
    for a in pos.get("ancrages", []):
        nom = a["limite"]
        s = par_role.get(nom) if not nom.startswith("segment:") else next((x for x in segs if x["i"] == int(nom[8:])), None)
        if s is None:
            raise Erreur(f"Limite « {nom} » introuvable sur cette parcelle (voir le tableau des cotes).")
        q = np.array(a["point"], float)
        qp = q[0] * e1 + q[1] * e2
        A.append(s["m"])
        b.append(a["distance_m"] + s["a"] @ s["m"] - qp @ s["m"])
    if len(A) < 2:
        raise Erreur("Il faut au moins deux cotes de position (voie et une limite laterale).")
    A, b = np.array(A), np.array(b)
    sv = np.linalg.svd(A, compute_uv=False)
    if sv[1] / sv[0] < 0.2:
        raise Erreur("Les cotes de position portent sur des limites quasi paralleles : ajouter une cote sur une "
                     "limite perpendiculaire (par exemple la voie et une limite laterale).")
    T = np.linalg.lstsq(A, b, rcond=None)[0]
    residus = A @ T - b
    return (lambda q: T + q[0] * e1 + q[1] * e2), residus, e1, e2


def tableau(segs):
    return "Cotes de la parcelle (n, longueur, statut, donne vers, role) :\n" + "\n".join(
        f"  {s['i']:>3}  {s['L']:6.2f} m  {s['statut']:<7} {cardinal(-s['m']):<2}  {s['role'] or '-'}"
        for s in segs if s["L"] >= LONG_MIN)


def analyser(parcelle, voisines, adresse, existants, prescriptions, projet, voie=None, routes=()):
    """Coeur du calcul, sans reseau. Toutes les geometries sont en Lambert 93 (metres)."""
    alertes, infos = [], []
    if parcelle.geom_type == "MultiPolygon":
        morceaux = sorted(parcelle.geoms, key=lambda g: -g.area)
        parcelle = next((g for g in morceaux if g.contains(Point(adresse))), morceaux[0])
        alertes.append("La parcelle cadastrale comporte plusieurs morceaux : seul celui de l'adresse est utilise.")
    segs = segments(parcelle, voisines)
    v, proches, methode = choisir_voie(segs, adresse, voie if voie is not None else projet.get("voie_segment"), routes)
    u = attribuer_roles(segs, v)
    if methode != "indiquee":
        alertes.append(f"Cote sur la voie deduit ({methode}) : cote {v['i']}, a confirmer par l'utilisateur.")
    if proches:
        alertes.append("Un autre cote est aussi proche d'une voie (parcelle d'angle ?) : verifier le cote sur la voie.")

    pos = projet.get("position", {})
    try:
        monde, residus, e1, e2 = poser(pos, segs, v, u)
    except Erreur as e:
        raise Erreur(f"{e}\n{tableau(segs)}") from None
    for a, r in zip(pos["ancrages"], residus):
        if abs(r) > TOL_RESIDU:
            alertes.append(f"Cote « {a['limite']} » {a['distance_m']:.2f} m incoherente avec le cadastre "
                           f"(ecart {abs(r):.2f} m) : relire la cote ou le cote de la parcelle.")

    bats = []
    for b in projet["batiments"]:
        typ = b.get("type", "batiment")
        if typ not in TYPES:
            raise Erreur(f"Type « {typ} » inconnu pour {b['nom']} : {', '.join(sorted(TYPES))}.")
        poly = Polygon([monde(np.array(p, float)) for p in b["emprise"]])
        if len(b["emprise"]) < 3 or not poly.is_valid or poly.area < 0.5:
            raise Erreur(f"Emprise de « {b['nom']} » invalide (moins de 3 sommets, contour croise ou surface nulle).")
        bats.append(dict(b, type=typ, poly=poly))

    lim = [s for s in segs if s["role"] is None or s["role"] != "voie"]
    nv = v["m"]
    bande = Polygon([v["a"] + nv * BANDE - 1e4 * u, v["a"] + nv * BANDE + 1e4 * u,
                     v["a"] + nv * 1e4 + 1e4 * u, v["a"] + nv * 1e4 - 1e4 * u])
    mes_bats = []
    for b in bats:
        p = b["poly"]
        d = {"nom": b["nom"], "type": b["type"], "surface_m2": round(p.area, 2),
             "hors_parcelle_m2": round(p.difference(parcelle).area, 2),
             "distance_voie_m": round(p.distance(v["geom"]), 2),
             "distances_cotes_m": {(s["role"] or f"segment:{s['i']}") + (f" ({s['i']})" if s["role"] else ""):
                                   round(p.distance(s["geom"]), 2) for s in segs if s["L"] >= LONG_MIN},
             "distance_limites_separatives_min_m": round(min((p.distance(s["geom"]) for s in lim), default=float("nan")), 2),
             "profondeur_max_depuis_voie_m": round(max((np.array(c) - v["a"]) @ nv for c in p.exterior.coords), 2),
             "au_dela_bande_25m_m2": round(p.intersection(bande).area, 2)}
        for k in ("hauteur_faitage", "hauteur_egout"):
            if b.get(k) is not None:
                d[k + "_m"] = b[k]
        if d["hors_parcelle_m2"] > 0.05:
            alertes.append(f"« {b['nom']} » depasse de la parcelle de {d['hors_parcelle_m2']} m2 : cotes ou limites a revoir.")
        mes_bats.append(d)

    surf_geom, contenance = parcelle.area, projet.get("contenance_m2")
    construit = [b["poly"] for b in bats if b["type"] in CONSTRUIT]
    emprise = shapely.union_all(construit).area if construit else 0.0
    artif = shapely.union_all([b["poly"] for b in bats]).area
    declaree = projet.get("emprise_declaree_m2")
    if declaree and abs(emprise - declaree) > TOL_EMPRISE * declaree:
        alertes.append(f"Emprise du dessin {emprise:.1f} m2 differente de l'emprise declaree {declaree} m2 : verifier le plan.")
    if contenance and abs(contenance - surf_geom) > ECART_SURFACE * contenance:
        alertes.append(f"Contenance cadastrale {contenance} m2 et surface du dessin cadastral {surf_geom:.0f} m2 "
                       f"different de plus de {ECART_SURFACE:.0%} : le taux d'emprise est donne pour les deux surfaces.")
    taux = {"sur_surface_geometrique": round(emprise / surf_geom, 4)}
    if contenance:
        taux["sur_contenance"] = round(emprise / contenance, 4)

    union = shapely.union_all(construit) if construit else Polygon()
    presc = [{"libelle": x["libelle"], "txt": x.get("txt"), "recouvrement_m2": round(union.intersection(x["geom"]).area, 2),
              "dans_la_parcelle_m2": round(parcelle.intersection(x["geom"]).area, 2)}
             for x in prescriptions if x["geom"].intersects(parcelle)]
    voisins = [{"hauteur_m": x.get("hauteur"), "distance_au_projet_m": round(union.distance(x["geom"]), 2)}
               for x in existants if x["geom"].intersection(parcelle).area <= 1]
    sur_parcelle = [{"hauteur_m": x.get("hauteur"), "surface_m2": round(x["geom"].area, 1),
                     "recouvrement_projet_m2": round(union.intersection(x["geom"]).area, 1)}
                    for x in existants if x["geom"].intersection(parcelle).area > 1]
    if any(x["recouvrement_projet_m2"] > 1 for x in sur_parcelle):
        infos.append("Le projet recouvre un batiment existant (BD TOPO) : demolition ou extension, a preciser.")
    infos.append("Limites cadastrales indicatives : un bornage par un geometre peut les deplacer.")

    mesures = {
        "statut": "valide" if projet.get("valide") else "a_confirmer",
        "parcelle": {"surface_geometrique_m2": round(surf_geom, 1), "contenance_m2": contenance,
                     "perimetre_m": round(parcelle.length, 1)},
        "cotes_parcelle": [{"n": s["i"], "longueur_m": round(s["L"], 2), "role": s["role"], "statut": s["statut"],
                            "donne_vers": cardinal(-s["m"])} for s in segs],
        "position": {"rotation_deg": pos.get("rotation_deg", 0), "cote_voie": v["i"], "methode_voie": methode,
                     "ancrages": [{**a, "distance_recalculee_m": round(a["distance_m"] - float(r), 2)}
                                  for a, r in zip(pos["ancrages"], residus)]},
        "batiments": mes_bats,
        "emprise_au_sol_m2": round(emprise, 2), "surface_artificialisee_m2": round(artif, 2), "taux_emprise": taux,
        "prescriptions_recouvertes": presc, "batiments_voisins": sorted(voisins, key=lambda x: x["distance_au_projet_m"])[:6],
        "batiments_existants_sur_parcelle": sur_parcelle, "alertes": alertes, "infos": infos,
    }
    geoms = dict(parcelle=parcelle, voisines=voisines, segs=segs, bats=bats, existants=existants, presc=prescriptions, v=v)
    return mesures, geoms


def recap(m):
    fmt = lambda x: f"{x:.2f}".replace(".", ",")
    L = ["STATUT : " + ("VALIDE par l'utilisateur" if m["statut"] == "valide" else
                       "A CONFIRMER : montrer ce recapitulatif et placement.png, faire corriger ou valider, puis relancer"
                       " avec \"valide\": true")]
    p = m["parcelle"]
    L.append(f"Parcelle : {p['surface_geometrique_m2']} m2 au dessin cadastral, contenance {p['contenance_m2']} m2")
    L.append("Cotes de la parcelle (n, longueur, role, statut, donne vers) :")
    L += [f"  {s['n']:>3}  {fmt(s['longueur_m']):>7} m  {s['role'] or '-':<7} {s['statut']:<7} {s['donne_vers']}"
          for s in m["cotes_parcelle"] if s["longueur_m"] >= LONG_MIN]
    L.append("Cotes de position lues (lue, recalculee sur le cadastre) :")
    L += [f"  {a['limite']:<8} point {a['point']} : {fmt(a['distance_m'])} m, {fmt(a['distance_recalculee_m'])} m"
          for a in m["position"]["ancrages"]]
    for b in m["batiments"]:
        L.append(f"{b['nom']} ({b['type']}) : {fmt(b['surface_m2'])} m2, a {fmt(b['distance_voie_m'])} m de la voie, "
                 f"limites separatives a {fmt(b['distance_limites_separatives_min_m'])} m au plus pres, "
                 f"profondeur {fmt(b['profondeur_max_depuis_voie_m'])} m, {fmt(b['au_dela_bande_25m_m2'])} m2 au-dela de {BANDE:.0f} m")
        L.append("   distances : " + ", ".join(f"{k} {fmt(x)} m" for k, x in b["distances_cotes_m"].items()))
    t = m["taux_emprise"]
    L.append(f"Emprise au sol {fmt(m['emprise_au_sol_m2'])} m2 = {t['sur_surface_geometrique']:.1%} (dessin)"
             + (f", {t['sur_contenance']:.1%} (contenance)" if "sur_contenance" in t else ""))
    L += [f"Prescription {x['libelle']} : {fmt(x['recouvrement_m2'])} m2 recouverts" for x in m["prescriptions_recouvertes"]]
    L += ["ALERTE : " + a for a in m["alertes"]] + ["Info : " + i for i in m["infos"]]
    return "\n".join(L)


def dessiner(m, g, chemin):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    LIMITE, DONNEE, TERRE, ENCRE = "#E4572E", "#2C6FB7", "#2F8F5B", "#1B2638"
    fig, ax = plt.subplots(figsize=(9, 9))
    xy = lambda geom: np.array(geom.exterior.coords)
    for o in g["voisines"]:
        for p in getattr(o, "geoms", [o]):
            ax.plot(*xy(p).T, color="#9AA5B1", lw=0.8)
    for e in g["existants"]:
        for p in getattr(e["geom"], "geoms", [e["geom"]]):
            ax.fill(*xy(p).T, color="#C9D2D8", zorder=1)
    for x in g["presc"]:
        inter = x["geom"].intersection(g["parcelle"])
        for p in getattr(inter, "geoms", [inter]):
            if p.geom_type == "Polygon" and not p.is_empty:
                ax.fill(*xy(p).T, facecolor="none", edgecolor=TERRE, hatch="///", lw=0, zorder=2)
    ax.fill(*xy(g["parcelle"]).T, color=TERRE, alpha=0.07, zorder=0)
    ax.plot(*xy(g["parcelle"]).T, color=LIMITE, lw=2.2, ls="--", zorder=3)
    for s in g["segs"]:
        if s["L"] >= LONG_MIN:
            t = s["mid"] - 0.9 * s["m"]
            ax.text(*t, f"{s['i']}" + (f" {s['role']}" if s["role"] else ""), ha="center", va="center", fontsize=8,
                    color=LIMITE, zorder=6)
    for b in g["bats"]:
        face = DONNEE if b["type"] in CONSTRUIT else "#8FB4DA"
        ax.fill(*xy(b["poly"]).T, facecolor=face, edgecolor=ENCRE, alpha=0.65, lw=1.5, zorder=4)
        c = b["poly"].centroid
        ax.text(c.x, c.y, b["nom"], ha="center", va="center", fontsize=9, color=ENCRE, zorder=7)
    for b, mb in zip(g["bats"], m["batiments"]):
        for s in g["segs"]:
            if s["role"] and s["L"] >= LONG_MIN:
                a, c = shapely.ops.nearest_points(b["poly"], s["geom"])
                if a.distance(c) > 0.05:
                    ax.plot([a.x, c.x], [a.y, c.y], color=ENCRE, lw=0.8, zorder=5)
                    ax.text((a.x + c.x) / 2, (a.y + c.y) / 2, f"{a.distance(c):.2f}".replace(".", ","), fontsize=8,
                            ha="center", color=ENCRE, bbox=dict(fc="white", ec="none", pad=1, alpha=0.8), zorder=8)
    ax.set_aspect("equal")
    x0, y0, x1, y1 = g["parcelle"].buffer(6).bounds
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.axis("off")
    etat = "VALIDE" if m["statut"] == "valide" else "A CONFIRMER"
    ax.set_title(f"Projet sur le cadastre ({etat}) - nord en haut, distances en metres", color=ENCRE, fontsize=11)
    ax.text(0.01, 0.01, "Fond : cadastre IGN (limites indicatives), batiments BD TOPO. Hachures : prescription du PLUi.",
            transform=ax.transAxes, fontsize=7, color="#5A6575")
    fig.savefig(chemin, dpi=150, bbox_inches="tight")
    plt.close(fig)


def charger(dossier):
    from parcelle import APICARTO, bbox_latlon, get, l93, wfs  # meme dossier ; les import du reseau ne servent qu'ici
    d = Path(dossier)
    brut = d / "brut"
    fiche = json.loads((d / "fiche.json").read_text(encoding="utf-8"))
    p = json.loads((brut / "cadastre.json").read_text(encoding="utf-8"))
    parcelle = l93(shape(p["geometry"]))
    fv = brut / "voisines.json"
    if not fv.exists():
        zone = shapely.transform(parcelle.buffer(5), lambda c: np.column_stack(_INV.transform(c[:, 0], c[:, 1])))
        fv.write_text(json.dumps(get(f"{APICARTO}/cadastre/parcelle", body={"geom": json.loads(shapely.to_geojson(zone))})["features"]))
    voisines = [l93(shape(x["geometry"])) for x in json.loads(fv.read_text())
                if x["properties"]["idu"] != p["properties"]["idu"]]
    fr = brut / "routes.json"
    if not fr.exists():
        wgs = shapely.transform(parcelle.buffer(25), lambda c: np.column_stack(_INV.transform(c[:, 0], c[:, 1])))
        fr.write_text(json.dumps(wfs("BDTOPO_V3:troncon_de_route", f"BBOX(geometrie,{bbox_latlon(wgs, 0)},'urn:ogc:def:crs:EPSG::4326')")))
    routes = [l93(shape(x["geometry"])) for x in json.loads(fr.read_text())
              if x["properties"].get("nature", "").startswith(("Route", "Rond-point", "Bretelle", "Type autoroutier"))
              and x["properties"].get("etat_de_l_objet") == "En service"]
    adresse = l93(Point(fiche["lon"], fiche["lat"]))
    existants = [{"hauteur": x["properties"].get("hauteur"), "geom": l93(shape(x["geometry"]))}
                 for x in json.loads((brut / "bdtopo_batiments.json").read_text(encoding="utf-8"))]
    presc = [{"libelle": x["properties"].get("libelle"), "txt": x["properties"].get("txt"), "geom": l93(shape(x["geometry"]))}
             for x in json.loads((brut / "gpu_prescription-surf.json").read_text(encoding="utf-8"))]
    return parcelle, voisines, (adresse.x, adresse.y), existants, presc, p["properties"]["contenance"], routes


def selftest_reseau(out):
    """Lieu public (gare de Trappes) : verifie que les API dont depend le placement repondent au format attendu."""
    from parcelle import fiche
    existants = next(Path(out).glob("*/fiche.json"), None)
    dossier = existants.parent if existants else fiche("2.006353,48.774939", out)[1]
    parcelle, voisines, adresse, bats, _, contenance, routes = charger(dossier)
    assert parcelle.area > 50 and contenance, (parcelle.area, contenance)
    assert voisines and bats, "voisines ou batiments BD TOPO absents"
    assert routes, "aucune route BD TOPO (nature, etat_de_l_objet : le format a peut-etre change)"
    segs = segments(parcelle.geoms[0] if parcelle.geom_type == "MultiPolygon" else parcelle, voisines)
    voie, _, methode = choisir_voie(segs, adresse, None, routes)
    assert methode == "route BD TOPO" and voie["L"] >= 2.0
    print(f"selftest reseau OK : {len(voisines)} voisines, {len(routes)} routes, voie = cote {voie['i']}")


def selftest():
    """Parcelle rectangulaire 16 x 26 m, voie au sud, puis la meme tournee de 30 degres : memes mesures attendues."""
    from shapely import affinity
    O = (650000.0, 6860000.0)
    rect = lambda x0, y0, x1, y1: Polygon([(O[0] + x0, O[1] + y0), (O[0] + x1, O[1] + y0), (O[0] + x1, O[1] + y1), (O[0] + x0, O[1] + y1)])
    projet = {"batiments": [{"nom": "maison", "type": "batiment", "emprise": [[0, 0], [9, 0], [9, 10], [0, 10]], "hauteur_faitage": 8}],
              "emprise_declaree_m2": 90, "contenance_m2": 416,
              "position": {"ancrages": [{"point": [0, 0], "limite": "voie", "distance_m": 5.0},
                                        {"point": [0, 0], "limite": "gauche", "distance_m": 2.5}]}}
    for angle in (0, 30):
        rot = lambda g: affinity.rotate(g, angle, origin=(O[0] + 8, O[1] + 13))
        parcelle = rot(rect(0, 0, 16, 26))
        voisines = [rot(rect(-10, 0, 0, 26)), rot(rect(16, 0, 26, 26)), rot(rect(0, 26, 16, 40))]
        existants = [{"hauteur": 6, "geom": rot(rect(-9, 5, -3, 12))}]
        presc = [{"libelle": "Espace paysager", "txt": "07", "geom": rot(rect(10, 10, 16, 26))}]
        routes = [rot(LineString([(O[0] - 20, O[1] - 6), (O[0] + 40, O[1] - 6)]))]
        adresse = (O[0] + 8 + 0.0, O[1] - 1.0)
        adresse = tuple(np.array(rot(Point(adresse)).coords[0]))
        m, g = analyser(parcelle, voisines, adresse, existants, presc, projet, routes=routes)
        assert m["position"]["methode_voie"] == "route BD TOPO"
        b = m["batiments"][0]
        d = b["distances_cotes_m"]
        assert [s["role"] for s in g["segs"] if s["role"]].count("voie") == 1
        assert abs(b["distance_voie_m"] - 5.0) < 1e-6
        assert abs(min(v for k, v in d.items() if k.startswith("gauche")) - 2.5) < 1e-6, d
        assert abs(min(v for k, v in d.items() if k.startswith("droite")) - 4.5) < 1e-6, d
        assert abs(min(v for k, v in d.items() if k.startswith("fond")) - 11.0) < 1e-6, d
        assert m["emprise_au_sol_m2"] == 90 and abs(m["taux_emprise"]["sur_contenance"] - 90 / 416) < 1e-3
        assert abs(m["prescriptions_recouvertes"][0]["recouvrement_m2"] - 7.5) < 1e-6
        assert abs(m["batiments_voisins"][0]["distance_au_projet_m"] - 5.5) < 1e-6
        assert b["au_dela_bande_25m_m2"] == 0 and abs(b["profondeur_max_depuis_voie_m"] - 15) < 1e-6
        assert m["statut"] == "a_confirmer" and not [a for a in m["alertes"] if "incoherente" in a]
    # Controle : troisieme cote fausse (droite a 9 m au lieu de 4,5 m) -> alerte d'incoherence.
    faux = json.loads(json.dumps(projet))
    faux["position"]["ancrages"].append({"point": [9, 0], "limite": "droite", "distance_m": 9.0})
    m, _ = analyser(parcelle, voisines, adresse, existants, presc, faux)
    assert any("incoherente" in a for a in m["alertes"]), m["alertes"]
    # Erreurs : cotes sur limites paralleles, voie introuvable, contour invalide.
    for modif, attendu in ((lambda p: p["position"].__setitem__("ancrages", [{"point": [0, 0], "limite": "voie", "distance_m": 5},
                                                                            {"point": [0, 0], "limite": "fond", "distance_m": 11}]), "paralleles"),
                           (lambda p: p["batiments"][0].__setitem__("emprise", [[0, 0], [9, 10], [9, 0], [0, 10]]), "invalide")):
        p2 = json.loads(json.dumps(projet))
        modif(p2)
        try:
            analyser(parcelle, voisines, adresse, existants, presc, p2)
            raise AssertionError("erreur attendue : " + attendu)
        except Erreur as e:
            assert attendu in str(e), e
    entoure = voisines + [rot(rect(0, -10, 16, 0))]
    try:
        analyser(parcelle, entoure, adresse, existants, presc, projet)
        raise AssertionError("voie ambigue non detectee")
    except Erreur as e:
        assert "--voie" in str(e)
    m, g = analyser(parcelle, entoure, adresse, existants, presc, projet, routes=routes)  # voie cadastree : les routes decident
    assert m["position"]["cote_voie"] == 0 and m["statut"] == "a_confirmer"
    with tempfile.TemporaryDirectory() as t:
        dessiner(m, g, Path(t) / "placement.png")
        assert (Path(t) / "placement.png").stat().st_size > 5000
    print(recap(m))
    print("selftest OK")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("fiche", nargs="?")
    a.add_argument("projet", nargs="?")
    a.add_argument("--voie", type=int, help="numero du cote sur la voie (tableau des cotes)")
    a.add_argument("--sortie", "--out", type=Path, dest="sortie")
    a.add_argument("--selftest", action="store_true")
    a.add_argument("--selftest-reseau", action="store_true")
    args = a.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        if args.selftest:
            selftest()
            sys.exit(0)
        if args.selftest_reseau:
            selftest_reseau(args.sortie or Path.cwd() / "plui-sqy-fiches")
            sys.exit(0)
        if not (args.fiche and args.projet):
            a.error("dossier de la fiche et projet.json requis")
        parcelle, voisines, adresse, existants, presc, contenance, routes = charger(args.fiche)
        projet = json.loads(Path(args.projet).read_text(encoding="utf-8"))
        projet.setdefault("contenance_m2", contenance)
        m, g = analyser(parcelle, voisines, adresse, existants, presc, projet, args.voie, routes)
    except Erreur as e:
        sys.exit(f"ERREUR : {e}")
    sortie = args.sortie or Path(args.fiche) / "projet"
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "mesures.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    dessiner(m, g, sortie / "placement.png")
    print(recap(m) + f"\n\nFichiers : {sortie / 'mesures.json'}, {sortie / 'placement.png'}")
