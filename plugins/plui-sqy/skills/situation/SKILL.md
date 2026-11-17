---
name: situation
description: Fond du plan de situation (PCMI1) d'une parcelle de Saint-Quentin-en-Yvelines - Plan IGN centré sur la parcelle, sans analyse PLUi.
argument-hint: "[adresse ou lon,lat]"
allowed-tools: Bash(uv run *) Bash(python3 *)
---
Lancer `uv run "${CLAUDE_PLUGIN_ROOT}/skills/plui/scripts/parcelle.py" "$ARGUMENTS" --seulement situation`.
Donner le chemin de `situation.png` et la mention « © IGN – Plan IGN – Licence Ouverte Etalab 2.0 », avec la date.
Rappeler d'ajouter le repère de la parcelle, le nord et l'échelle sur la pièce PCMI1.
