---
name: fiche
description: Fiche complète d'une parcelle du PLUi de Saint-Quentin-en-Yvelines à partir d'une adresse - cadastre, zone, prescriptions, servitudes, terrain, voisins, gares, risques, fonds de plan.
argument-hint: "[adresse ou lon,lat]"
allowed-tools: Bash(uv run *) Bash(python3 *)
---
Lancer `uv run "${CLAUDE_PLUGIN_ROOT}/skills/plui/scripts/parcelle.py" "$ARGUMENTS"` (ou `python3` à la place de
`uv run`), puis présenter la fiche selon la méthode du skill `plui` : parcelle, zone et code décodé, prescriptions,
informations, servitudes, terrain, bâtiments, risques, chemins de `masse.png` et `situation.png`, mentions de
`CREDITS.txt`. Signaler toute alerte de version affichée par le script. Rappeler que la fiche est non officielle.
