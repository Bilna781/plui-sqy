# /// script
# requires-python = ">=3.10"
# dependencies = ["shapely>=2", "pyproj", "numpy"]
# ///
"""Fiche d'une parcelle a partir d'une adresse : cadastre, PLUi (GPU), servitudes, terrain,
voisins, environnement, risques, gares, fonds de plan. API publiques sans cle (IGN, Georisques).

Usage : python parcelle.py "<adresse>" | "<lon>,<lat>" [--out DOSSIER] [--seulement masse|situation]
        python parcelle.py --selftest   (lieu public ; temoins prives via la variable PLUI_TEMOINS)
Ecrit DOSSIER/<idu>/fiche.json, brut/*.json, situation.png, masse.png et affiche un resume.
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape

APICARTO = "https://apicarto.ign.fr/api"
GEOPF = "https://data.geopf.fr"
_T = Transformer.from_crs(4326, 2154, always_xy=True)


def l93(geom):
    return shapely.transform(geom, lambda c: np.column_stack(_T.transform(c[:, 0], c[:, 1])))
GPU = ["zone-urba", "prescription-surf", "prescription-lin", "prescription-pct",
       "info-surf", "info-lin", "info-pct", "assiette-sup-s", "assiette-sup-l", "assiette-sup-p", "document"]
NATURE = ["natura-habitat", "natura-oiseaux", "znieff1", "znieff2", "pn", "pnr", "rnn"]


def get(url, params=None, body=None, raw=False):
    if params:
        url += "?" + urllib.parse.urlencode(params, safe="|,:")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    for essai in range(3):  # coupures reseau intermittentes observees sur plusieurs services publics
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read() if raw else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code < 500 or essai == 2:
                raise
        except OSError:
            if essai == 2:
                raise
        time.sleep(1 + essai)


def wfs(typename, cql):
    # Le WFS Geoplateforme attend latitude,longitude en EPSG:4326 : dans l'autre ordre il renvoie 0 objet sans erreur.
    return get(f"{GEOPF}/wfs/ows", {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
                                    "TYPENAMES": typename, "OUTPUTFORMAT": "application/json", "CQL_FILTER": cql})["features"]


def bbox_latlon(geom, marge_deg):
    x0, y0, x1, y1 = geom.bounds
    return f"{y0 - marge_deg},{x0 - marge_deg},{y1 + marge_deg},{x1 + marge_deg}"


def wms(layers, geom, marge_deg, path, w=1000):
    x0, y0, x1, y1 = geom.bounds
    # Hauteur deduite de l'emprise pour ne pas deformer l'image (1 degre de longitude = cos(lat) degre de latitude).
    h = round(w * (y1 - y0 + 2 * marge_deg) / ((x1 - x0 + 2 * marge_deg) * np.cos(np.radians((y0 + y1) / 2))))
    png = get(f"{GEOPF}/wms-r/wms", {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": layers,
                                     "STYLES": "," * layers.count(","), "CRS": "EPSG:4326", "FORMAT": "image/png",
                                     "BBOX": bbox_latlon(geom, marge_deg), "WIDTH": w, "HEIGHT": h}, raw=True)
    path.write_bytes(png)


def fiche(adresse, out, seulement=None):
    try:
        lon, lat = (float(v) for v in adresse.split(","))
        geo = [{"geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": {"label": f"point {lon},{lat}"}}]
    except ValueError:
        geo = get(f"{GEOPF}/geocodage/search", {"q": adresse, "limit": 1})["features"]
        if not geo:
            sys.exit(f"Adresse introuvable : {adresse}")
        lon, lat = geo[0]["geometry"]["coordinates"]
    point = {"type": "Point", "coordinates": [lon, lat]}

    parc = get(f"{APICARTO}/cadastre/parcelle", body={"geom": point})["features"]
    if not parc:
        sys.exit("Aucune parcelle cadastrale sous ce point.")
    p = parc[0]
    g = shape(p["geometry"])
    g93 = l93(g)
    dossier = out / p["properties"]["idu"]
    (dossier / "brut").mkdir(parents=True, exist_ok=True)
    brut = {"geocodage": geo[0], "cadastre": p}

    if seulement:  # fond de plan seul : pas d'appel au PLUi ni aux autres API
        nom = f"{seulement}.png"
        if seulement == "situation":
            wms("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", g, 0.01, dossier / nom)
        else:
            wms("ORTHOIMAGERY.ORTHOPHOTOS,CADASTRALPARCELS.PARCELLAIRE_EXPRESS", g, 0.0004, dossier / nom)
        f = {"adresse": geo[0]["properties"]["label"], "parcelle": {**{k: p["properties"][k] for k in
             ("idu", "section", "numero", "contenance")}, "surface_geom_m2": round(g93.area),
             "perimetre_m": round(g93.length, 1)}, "fichiers": {seulement: nom}, "sources": credits("non consulte", "")[1:2]}
        (dossier / "CREDITS.txt").write_text("\n".join(f["sources"]) + "\n", encoding="utf-8")
        return f, dossier

    # PLUi et servitudes : on interroge avec la parcelle entiere, pas seulement le point d'adresse.
    for m in GPU:
        brut[f"gpu_{m}"] = get(f"{APICARTO}/gpu/{m}", body={"geom": p["geometry"]})["features"]
    for m in NATURE:
        brut[f"nature_{m}"] = get(f"{APICARTO}/nature/{m}", {"geom": json.dumps(point)})["features"]

    # Altitude aux sommets de la parcelle : pente et terrain naturel pour la coupe.
    sommets = list(g.exterior.coords if g.geom_type == "Polygon" else g.geoms[0].exterior.coords)[:-1]
    alt = get(f"{GEOPF}/altimetrie/1.0/calcul/alti/rest/elevation.json",
              {"lon": "|".join(str(x) for x, _ in sommets), "lat": "|".join(str(y) for _, y in sommets),
               "resource": "ign_rge_alti_wld", "zonly": "true"})["elevations"]

    bats = wfs("BDTOPO_V3:batiment", f"BBOX(geometrie,{bbox_latlon(g, 0.0003)},'urn:ogc:def:crs:EPSG::4326')")
    gares = wfs("BDTOPO_V3:equipement_de_transport",
                f"nature LIKE 'Gare voyageurs%' AND BBOX(geometrie,{bbox_latlon(g, 0.03)},'urn:ogc:def:crs:EPSG::4326')")
    iso = get(f"{GEOPF}/navigation/isochrone", {"point": f"{lon},{lat}", "resource": "bdtopo-valhalla",
                                                "costValue": 600, "costType": "time", "profile": "pedestrian"})
    iso_g = shape(iso["geometry"])
    risques = None
    # Diagnostic du 17/11/2026 : cet endpoint composite est coupe par le serveur environ 1 fois sur 3 (flux HTTP/2
    # INTERNAL_ERROR, aucun 429), alors que les endpoints simples repondent toujours. 5 essais espaces, puis sans.
    for essai in range(5):
        try:
            risques = get("https://georisques.gouv.fr/api/v1/resultats_rapport_risque", {"latlon": f"{lon},{lat}"})
            break
        except OSError:
            time.sleep(1 + essai)
    brut.update(altimetrie=alt, bdtopo_batiments=bats, gares=gares, isochrone_10min_pied=iso, georisques=risques)

    for k, v in brut.items():
        (dossier / "brut" / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    wms("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", g, 0.01, dossier / "situation.png")
    wms("ORTHOIMAGERY.ORTHOPHOTOS,CADASTRALPARCELS.PARCELLAIRE_EXPRESS", g, 0.0004, dossier / "masse.png")

    props = lambda feats, *ks: [{k: f["properties"].get(k) for k in ks} for f in feats]
    zone = brut["gpu_zone-urba"][0]["properties"] if brut["gpu_zone-urba"] else {}
    doc = brut["gpu_document"][0]["properties"] if brut["gpu_document"] else {}
    voisins = []
    for b in bats:
        bg = l93(shape(b["geometry"]))
        voisins.append({**{k: b["properties"].get(k) for k in ("usage_1", "hauteur", "nombre_d_etages",
                                                                "nombre_de_logements", "date_d_apparition")},
                        "sur_parcelle": bg.intersection(g93).area > 1, "distance_m": round(bg.distance(g93), 1)})
    f = {
        "adresse": geo[0]["properties"]["label"], "lon": lon, "lat": lat,
        "parcelle": {**{k: p["properties"][k] for k in ("idu", "section", "numero", "contenance")},
                     "surface_geom_m2": round(g93.area), "perimetre_m": round(g93.length, 1)},
        "plui": {"document": doc.get("name"), "publie_gpu": doc.get("gpu_timestamp"),
                 "zone": zone.get("libelle"), "libelle": zone.get("libelong"), "approbation": zone.get("datappro"),
                 "reglement": zone.get("urlfic")},
        "prescriptions": props(brut["gpu_prescription-surf"] + brut["gpu_prescription-lin"] + brut["gpu_prescription-pct"],
                               "libelle", "txt", "urlfic"),
        "informations": props(brut["gpu_info-surf"] + brut["gpu_info-lin"] + brut["gpu_info-pct"], "libelle", "txt"),
        "servitudes": props(brut["gpu_assiette-sup-s"] + brut["gpu_assiette-sup-l"] + brut["gpu_assiette-sup-p"],
                            "suptype", "nomsuplitt"),
        "terrain": {"alt_min": min(alt), "alt_max": max(alt), "denivele_m": round(max(alt) - min(alt), 2)},
        "batiments": sorted(voisins, key=lambda v: v["distance_m"]),
        "nature": {m: len(brut[f"nature_{m}"]) for m in NATURE},
        "gares": [{"nom": x["properties"]["toponyme"],
                   "distance_m": round(l93(shape(x["geometry"])).distance(l93(shape(point)))),
                   "a_10min_a_pied": iso_g.intersects(shape(x["geometry"]))} for x in gares],
        "risques": {"naturels": {v["libelle"]: v.get("libelleStatutAdresse") for v in risques["risquesNaturels"].values() if v["present"]},
                    "technologiques": {v["libelle"]: v.get("libelleStatutAdresse") for v in risques["risquesTechnologiques"].values() if v["present"]},
                    "rapport": risques.get("url")} if risques else {"naturels": {}, "technologiques": {}, "rapport": None,
                                                                     "erreur": "Georisques indisponible, relancer plus tard"},
        "fichiers": {"situation": "situation.png", "masse": "masse.png", "brut": "brut/"},
        "sources": credits(doc.get("name"), doc.get("gpu_timestamp", "")[:10]),
    }
    f["gares"].sort(key=lambda x: x["distance_m"])
    (dossier / "fiche.json").write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    (dossier / "CREDITS.txt").write_text("\n".join(f["sources"]) + "\n", encoding="utf-8")
    alerte_version(f["plui"]["document"])
    return f, dossier


def alerte_version(en_vigueur):
    """Compare la version du PLUi en vigueur (GPU) a celle sur laquelle le skill a ete verifie."""
    ref = Path(__file__).resolve().parent.parent / "references" / "version.json"
    if ref.exists() and en_vigueur:
        connue = json.loads(ref.read_text(encoding="utf-8"))["document"]
        if connue != en_vigueur:
            print(f"ATTENTION : le PLUi en vigueur est {en_vigueur}, le skill a ete verifie sur {connue}. "
                  "Mettre a jour le skill ou verifier chaque regle dans le reglement en vigueur.", file=sys.stderr)


def credits(version_plui, publie_gpu):
    """Mentions exigees par les licences (Licence Ouverte 2.0 : paternite + date). Voir NOTICE.md."""
    jour = datetime.date.today().strftime("%d/%m/%Y")
    return [
        f"PLUi de Saint-Quentin-en-Yvelines, version {version_plui} publiee le {publie_gpu}, "
        f"via le Geoportail de l'Urbanisme (Licence Ouverte), consulte le {jour}",
        f"Cadastre, Plan IGN, orthophotographies, BD TOPO, altimetrie, isochrones : © IGN – Geoplateforme – "
        f"Licence Ouverte Etalab 2.0 – consulte le {jour}",
        "Zonages naturels : MNHN via API Carto IGN, licence d'origine",
        "Ministère de la Transition écologique, de la Biodiversité et des Négociations Internationales sur le Climat "
        f"et la Nature – Données originales téléchargées sur https://www.georisques.gouv.fr, consultées le {jour}",
        "Fiche non officielle : ne remplace ni un certificat d'urbanisme ni l'avis du service instructeur",
    ]


def resume(f):
    pa, pl = f["parcelle"], f["plui"]
    print(f"{f['adresse']}\nParcelle {pa['idu']} : {pa['contenance']} m2 (geom {pa['surface_geom_m2']} m2)")
    print(f"Zone {pl['zone']} ({pl['libelle']}), {pl['document']} publie le {pl['publie_gpu'][:10]}\nReglement : {pl['reglement']}")
    for x in f["prescriptions"]:
        print(f"  Prescription : {x['libelle']} [{x['txt']}]")
    for x in f["informations"]:
        print(f"  Information  : {x['libelle']}")
    print(f"  Servitudes   : {len(f['servitudes']) or 'aucune'}")
    t = f["terrain"]
    print(f"Terrain : {t['alt_min']} a {t['alt_max']} m, denivele {t['denivele_m']} m")
    for b in f["batiments"][:6]:
        ou = "sur parcelle" if b["sur_parcelle"] else f"a {b['distance_m']} m"
        print(f"  Batiment {ou} : "
              f"{b['usage_1']}, {b['hauteur']} m, {b['nombre_d_etages']} niv., {b['date_d_apparition']}")
    print("Nature : " + (", ".join(k for k, n in f["nature"].items() if n) or "aucune zone protegee"))
    for g in f["gares"][:3]:
        print(f"Gare : {g['nom']} a {g['distance_m']} m{' (moins de 10 min a pied)' if g['a_10min_a_pied'] else ''}")
    print("Sources :\n  " + "\n  ".join(f["sources"]))
    if f["risques"].get("erreur"):
        print("Risques : " + f["risques"]["erreur"])
    print("Risques : " + "; ".join(f"{k} ({v})" for k, v in {**f["risques"]["naturels"], **f["risques"]["technologiques"]}.items()))


def selftest(out):
    # Lieu public uniquement (gare de Trappes) : aucune adresse de particulier dans le code ni dans les journaux.
    f, _ = fiche("2.006353,48.774939", out)
    assert f["parcelle"]["idu"].startswith("78621"), f["parcelle"]
    assert f["plui"]["zone"] and f["plui"]["document"].startswith("200058782_PLUi_"), f["plui"]
    assert 150 < f["terrain"]["alt_min"] < 190
    assert any(g["nom"] == "Gare de Trappes" and g["a_10min_a_pied"] for g in f["gares"])
    # Temoins prives : PLUI_TEMOINS='[{"adresse": "...", "zone": "URs2f9"}]' (secret GitHub). Seul le rang est affiche.
    for i, t in enumerate(json.loads(os.environ.get("PLUI_TEMOINS") or "[]"), 1):
        z = fiche(t["adresse"], out)[0]["plui"]["zone"]
        print(f"temoin {i} : {'OK' if z == t['zone'] else 'ZONE CHANGEE'}")
    print("selftest OK")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("adresse", nargs="?")
    a.add_argument("--out", type=Path, default=Path.cwd() / "plui-sqy-fiches")
    a.add_argument("--seulement", choices=["masse", "situation"], help="fond de plan seul, sans analyse PLUi")
    a.add_argument("--selftest", action="store_true")
    args = a.parse_args()
    if args.selftest:
        selftest(args.out)
    elif args.adresse:
        f, d = fiche(args.adresse, args.out, args.seulement)
        if args.seulement:
            print(f"Parcelle {f['parcelle']['idu']} : {d / f['fichiers'][args.seulement]}\n" + f["sources"][0])
        else:
            resume(f)
            print(f"\nFiche : {d / 'fiche.json'}")
    else:
        a.error("adresse requise")
