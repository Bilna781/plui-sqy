"""Controle local de la structure du depot (complement de `claude plugin validate`).

Verifie : JSON valides, noms identiques entre marketplace.json et plugin.json, chemins existants, chaque SKILL.md
avec name et description, lien Codex valide, aucune adresse temoin privee (secret PLUI_TEMOINS) dans les fichiers.
Usage : python outils/controle_structure.py   (code de sortie 1 en cas d'erreur)
"""
import json
import os
import re
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
erreurs = []
mk = json.loads((R / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
for e in mk["plugins"]:
    racine = R / e["source"]
    manifeste = json.loads((racine / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifeste["name"] != e["name"]:
        erreurs.append(f"nom different : marketplace {e['name']} / plugin.json {manifeste['name']}")
    for s in sorted((racine / "skills").glob("*/SKILL.md")):
        tete = s.read_text(encoding="utf-8").split("---")[1]
        for champ in ("name:", "description:"):
            if champ not in tete:
                erreurs.append(f"{s.relative_to(R)} : champ {champ} manquant")
        nom = re.search(r"^name:\s*(\S+)", tete, re.M)
        if nom and nom.group(1) != s.parent.name:
            erreurs.append(f"{s.relative_to(R)} : name {nom.group(1)} different du dossier")
codex = R / ".agents/skills/plui/SKILL.md"
if not codex.exists():
    erreurs.append("lien Codex .agents/skills/plui casse")
# Adresses temoins privees : lues dans le secret PLUI_TEMOINS, jamais ecrites dans le depot.
privees = [t["adresse"].lower() for t in json.loads(os.environ.get("PLUI_TEMOINS", "[]"))]
for f in R.rglob("*"):
    if privees and f.is_file() and ".git" not in f.parts and f.suffix in {".py", ".md", ".json", ".yml", ".txt"}:
        texte = f.read_text(encoding="utf-8", errors="ignore").lower()
        if any(a in texte for a in privees):
            erreurs.append(f"adresse privee dans {f.relative_to(R)}")
print("\n".join(erreurs) or "structure OK")
sys.exit(1 if erreurs else 0)
