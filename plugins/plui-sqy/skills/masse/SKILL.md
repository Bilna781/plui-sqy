---
name: masse
description: Fond du plan de masse (PCMI2) d'une parcelle de Saint-Quentin-en-Yvelines - photo aérienne avec limites cadastrales, sans analyse PLUi. Pour la fiche complète, utiliser fiche.
argument-hint: "[adresse ou lon,lat]"
allowed-tools: Bash(uv run *) Bash(python3 *)
---
Lancer `uv run "${CLAUDE_PLUGIN_ROOT}/skills/plui/scripts/parcelle.py" "$ARGUMENTS" --seulement masse`.
Donner le chemin de `masse.png`, la parcelle (identifiant, contenance, surface et périmètre calculés) et la mention
de source à reprendre en légende : « © IGN – Géoplateforme – Licence Ouverte Etalab 2.0 », avec la date.
Préciser que c'est un fond : le projet, les cotes et les limites de recul restent à dessiner.
