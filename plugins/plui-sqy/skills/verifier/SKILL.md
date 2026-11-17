---
name: verifier
description: Vérifie un projet de construction (dimensions, surface de plancher, hauteur, stationnement) contre les règles du PLUi de Saint-Quentin-en-Yvelines pour une parcelle, avec un verdict article par article.
argument-hint: "[adresse] [description du projet]"
allowed-tools: Bash(uv run *) Bash(python3 *)
---
Suivre `${CLAUDE_PLUGIN_ROOT}/skills/plui/references/methode-verdict.md` :
1. fiche de la parcelle (`parcelle.py`) ;
2. articles de la zone avec `reglement.py` (6, 7, 8, 9, 10, 11, 12, 13 et commun 12) ;
3. demander les données du projet qui manquent ;
4. tableau point / projet / règle (page) / verdict, puis pistes de mise en conformité ;
5. rappel : verdict indicatif, non officiel ; seul le service urbanisme décide ; recommander un certificat
   d'urbanisme opérationnel.
