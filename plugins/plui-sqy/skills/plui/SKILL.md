---
name: plui
description: Lit le PLUi de Saint-Quentin-en-Yvelines (Trappes, Élancourt, Guyancourt, La Verrière, Magny-les-Hameaux, Montigny-le-Bretonneux, Voisins-le-Bretonneux) pour une adresse ou une parcelle - zone, règles (recul, retrait, emprise au sol, hauteur, espaces verts, stationnement), prescriptions, servitudes, risques, et ce qu'on peut y construire. À utiliser pour toute question de PLU, PLUi, permis de construire, constructibilité, plan de masse ou plan de situation sur ce territoire.
argument-hint: "[adresse ou lon,lat] [question]"
---

# PLUi de Saint-Quentin-en-Yvelines (non officiel)

Aide à la lecture du PLUi. Ne remplace ni un certificat d'urbanisme ni l'avis du service instructeur : le dire dans
chaque réponse qui conclut sur la constructibilité.

## Ce que je sais faire
- Fiche d'une parcelle à partir d'une adresse : cadastre, zone, prescriptions, informations, servitudes, terrain,
  bâtiments voisins, zones naturelles, gares, risques (commande `fiche`).
- Fond de plan de masse (PCMI2) ou de situation (PCMI1) seul (commandes `masse` et `situation`).
- Lecture d'un article du règlement en vigueur pour une zone, avec la page citée (commande `regles`).
- Comparaison d'un projet aux règles de la zone, avec verdict article par article (commande `verifier`).
- Vérification que le PLUi n'a pas changé depuis la dernière mise à jour du skill (commande `veille`).

## Scripts
Dossier des scripts : `${CLAUDE_PLUGIN_ROOT}/skills/plui/scripts/` sous Claude Code ; sinon le dossier `scripts/`
à côté de ce fichier. Les lancer avec `uv run <script> ...` (dépendances installées automatiquement), ou avec
`python3` après `pip install shapely pyproj numpy pymupdf`.

| Script | Rôle |
|---|---|
| `parcelle.py "<adresse>"` | Fiche complète : écrit `plui-sqy-fiches/<idu>/fiche.json`, `masse.png`, `situation.png`, `CREDITS.txt` |
| `parcelle.py "<adresse>" --seulement masse` | Fond de plan de masse seul (ou `situation`) |
| `reglement.py --zone <code>` | Décode le code de zone (forme, densité, hauteur) |
| `reglement.py --url <reglement> --zone <code> --article <n>` | Texte de l'article de zone, avec pages |
| `reglement.py --url <reglement> --commun <n>` | Texte d'un article des dispositions communes (ex. 12 stationnement) |

## Méthode
1. Lancer `parcelle.py` sur l'adresse. Une adresse est une donnée personnelle : ne pas la recopier ailleurs que
   dans la réponse à l'utilisateur, ne jamais l'écrire dans un fichier du dépôt ni dans une issue.
2. Lire `fiche.json`. Si le script affiche « ATTENTION : le PLUi en vigueur est ... », le signaler en tête de réponse.
3. Pour chaque règle utile, lancer `reglement.py` avec l'URL `plui.reglement` de la fiche (toujours la version en
   vigueur) et le code de zone. Lire les paragraphes de l'indice de forme et de densité de la zone. Les règles
   générales sont dans les articles communes (titre II) : stationnement = `--commun 12`. Pour les dimensions des
   places, les plantations (essences interdites, distances) ou les vues et jours : `references/annexes-reglement.md`.
4. Tenir compte des prescriptions de la fiche (espace paysager, linéaire, élément protégé) : elles s'ajoutent aux
   règles de zone. Leur texte est dans le PDF indiqué par `urlfic`.
5. Répondre avec un tableau article / règle / valeur pour la parcelle, en citant la page du règlement, puis les
   points de vigilance (risques, servitudes, bruit, archéologie).
6. Terminer par les mentions de `CREDITS.txt` et le rappel « non officiel ».

Détails : [references/lecture-code-zone.md](references/lecture-code-zone.md),
[references/methode-verdict.md](references/methode-verdict.md), [references/sources.md](references/sources.md),
[references/annexes-reglement.md](references/annexes-reglement.md) (stationnement, plantations, invasives, vues et jours).

## Limites
- Les hauteurs de la BD TOPO sont des estimations ; les surfaces cadastrales ne remplacent pas un relevé de géomètre.
- Géorisques coupe parfois la connexion : la fiche continue sans les risques et le signale.
- Les plans de zonage en image ne sont pas lus : la zone vient du Géoportail de l'Urbanisme.
- Les PDF ont été lus en texte brut. Le PPRI de la Bièvre n'est pas exploitable (police mal encodée) : signaler la zone sans
  annoncer ses prescriptions. Détail dans `references/sources.md`.
