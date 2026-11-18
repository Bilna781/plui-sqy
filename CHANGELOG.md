# Journal des versions

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les tags combinent la version du skill et celle
du PLUi vérifiée : `v1.0.0+plui-20260219`.

## [2.1.0] - 2026-11-18
PLUi vérifié : `200058782_PLUi_20260219` (inchangé).

### Ajouté
- `projet.py` et commande `projet` : placement d'un projet sur le cadastre à partir des cotes d'un plan, avec
  récapitulatif et image à faire confirmer par l'utilisateur avant tout verdict, distances aux limites, emprise,
  bande constructible de 25 m, empiétement sur les prescriptions, côté sur la voie déduit des routes de la BD TOPO.
  Documentation : `references/projet-sur-cadastre.md`.
- Illustration « Projet sur le cadastre » (claire et sombre) dans le README.
- Workflow `controle.yml` : autotest de `projet.py` ; workflow `sante-api.yml` : `projet.py --selftest-reseau`
  (routes BD TOPO et parcelles voisines).

### Modifié
- Description du plugin et du catalogue, `CONTRIBUTING.md` et dépendances du README (matplotlib) mises à jour.

## [2.0.0] - 2026-11-18
PLUi vérifié : `200058782_PLUi_20260219` (inchangé).

### Ajouté
- `references/annexes-reglement.md` : annexes 2, 3, 5, 7, 8 et 10 du règlement (dimensions des places de stationnement,
  espèces invasives interdites, distances de plantation, vues et jours), avec leur portée juridique.
- Prescription d'implantation sur voie : recul d'alignement et bande constructible de 25 m (méthode de vérification).
- Illustration « Limites » (claire et sombre) dans le README : cartes, PPRI de la Bièvre, annexe 9, relecture du PLUi.
- Limites d'extraction des documents (texte brut, PPRI de la Bièvre, annexe 9) dans `sources.md`, le `SKILL.md`
  et le README.

## [1.0.1] - 2026-11-18
PLUi vérifié : `200058782_PLUi_20260219` (inchangé).

### Modifié
- Veille simplifiée à deux états (« à jour », « version modifiée ») : contrôles sur le Géoportail de l'Urbanisme
  (versions, dates de mise à jour, empreinte des fichiers) et en-têtes du règlement, sans analyse de page web.
- Badge d'état généré chaque jour sur GitHub Pages (`etat.svg`) au lieu d'un fichier fixe.

### Retiré
- Surveillance des PDF de la page de SQY (`veille/inventaire.json`) et état « procédure en cours ».

## [1.0.0] - 2026-11-17
PLUi vérifié : `200058782_PLUi_20260219` (approuvé le 19/02/2026, publié sur le Géoportail de l'Urbanisme le 26/03/2026).

### Ajouté
- Plugin Claude Code `plui-sqy` : commandes `fiche`, `masse`, `situation`, `regles`, `verifier`, `veille`, et skill
  général `plui` (aussi disponible pour Codex dans `.agents/skills/plui`).
- `parcelle.py` : fiche de parcelle (cadastre, PLUi, servitudes, terrain, voisins, zones naturelles, gares,
  Géorisques, fonds de plan) avec mentions de source.
- `reglement.py` : extraction d'un article du règlement en vigueur, avec pages.
- Veille hebdomadaire : versions du Géoportail de l'Urbanisme, PDF du site de SQY, en-têtes du règlement.
- La fiche refuse les adresses situées hors des 7 communes de Saint-Quentin-en-Yvelines.
- Nouvelles tentatives automatiques quand un service public renvoie une erreur passagère ou une réponse vide.
