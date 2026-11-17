---
name: regles
description: Lit un ou plusieurs articles du règlement du PLUi de Saint-Quentin-en-Yvelines en vigueur pour un code de zone (ex. URs2f9), avec les pages citées.
argument-hint: "[code de zone] [articles, ex. 6 7 9 10]"
allowed-tools: Bash(uv run *) Bash(python3 *)
---
1. Décoder le code : `uv run "${CLAUDE_PLUGIN_ROOT}/skills/plui/scripts/reglement.py" --zone <code>`.
2. URL du règlement en vigueur : celle de `plui.reglement` d'une fiche déjà faite ; sinon lancer d'abord la commande
   `fiche` sur une adresse de la zone.
3. Pour chaque article demandé (par défaut 6, 7, 9, 10, 12, 13) :
   `uv run ".../reglement.py" --url <url> --zone <code> --article <n>`, et `--commun 12` pour le stationnement.
4. Ne retenir que les paragraphes des indices de la zone. Présenter un tableau article / règle / page, avec de
   courtes citations exactes. Ne pas extrapoler ce que le texte ne dit pas.
