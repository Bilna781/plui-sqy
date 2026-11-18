---
name: projet
description: Place un projet de construction (emprise, hauteur, cotes de position lues sur un plan) sur le cadastre d'une parcelle de Saint-Quentin-en-Yvelines et mesure distances aux limites, emprise au sol, bande de 25 m et empiétement sur les prescriptions. Les cotes lues doivent être confirmées par l'utilisateur avant tout verdict.
argument-hint: "[adresse ou dossier de fiche] [plan ou description du projet]"
allowed-tools: Bash(uv run *) Bash(python3 *)
---
Suivre `${CLAUDE_PLUGIN_ROOT}/skills/plui/references/projet-sur-cadastre.md`, dans cet ordre :
1. fiche de la parcelle avec `parcelle.py` si elle n'existe pas ;
2. lire le plan, relever emprise, hauteurs et cotes de position, demander ce qui manque ;
3. écrire `projet.json` avec `"valide": false`, lancer `projet.py <dossier fiche> projet.json` ;
4. montrer à l'utilisateur le récapitulatif et `placement.png`, lui faire corriger ou valider chaque cote et le côté sur la voie ;
5. après sa validation explicite seulement, passer `"valide": true`, relancer, puis faire le verdict avec `mesures.json` (skill `verifier`).
Ne jamais présenter un verdict comme fiable tant que le statut n'est pas « valide ».
