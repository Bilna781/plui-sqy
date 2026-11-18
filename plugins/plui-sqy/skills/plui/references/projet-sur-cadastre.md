# Placer un projet sur le cadastre

Script : `scripts/projet.py`. Il pose l'emprise du projet sur la parcelle cadastrale à partir de cotes lues sur un
plan, puis mesure ce que les articles du règlement demandent de vérifier. Il ne lit pas les plans : c'est Claude qui
relève les cotes, et l'utilisateur qui les valide.

## Déroulé obligatoire
1. **Fiche** : `parcelle.py "<adresse>"` écrit le dossier `<idu>/` (cadastre, bâtiments BD TOPO, prescriptions).
2. **Lecture du plan** (image, PDF, DXF) : relever l'emprise de chaque construction (sommets en mètres), les hauteurs,
   les cotes de position, l'emprise indiquée au cartouche. Si une donnée manque, la demander, ne jamais la déduire
   d'une échelle graphique ou d'une mesure à l'œil.
3. **`projet.json`** avec `"valide": false` (format en tête de `projet.py`).
4. **Premier passage** : `uv run projet.py <dossier fiche> projet.json`. Le script affiche un récapitulatif et écrit
   `projet/placement.png` et `projet/mesures.json` avec le statut `a_confirmer`.
5. **Confirmation** : montrer à l'utilisateur le récapitulatif et l'image. Lui demander, point par point, si les
   cotes lues sont exactes, si le côté n° N est bien celui de la rue, si le plan est orienté comme indiqué. Il corrige
   ou valide.
6. **Passage validé** : après son accord explicite, passer `"valide": true` et relancer. Seules les mesures au statut
   `valide` servent au verdict. Sinon, dire que les mesures sont indicatives et non confirmées.

## Ce que le plan doit contenir
- Cotes hors tout de chaque construction et emprise au sol (cartouche ou calcul).
- **Au moins deux distances perpendiculaires aux limites, sur deux limites non parallèles** : la voie et une limite
  latérale. Une troisième distance sert de contrôle : sans elle, une erreur de lecture passe inaperçue.
- Hauteur au faîtage et à l'égout si le verdict porte sur la hauteur.
- Annexes, terrasses, piscine, accès avec leurs cotes (type `annexe`, `terrasse`, `piscine`, `acces`).
- Repère de l'orientation du plan par rapport à la rue, sinon on suppose la façade parallèle à la voie
  (`rotation_deg` : 0).

## Garde-fous du script
- Cote de position incohérente avec le cadastre (écart de plus de 0,15 m entre la cote lue et la cote recalculée) :
  alerte. Contour croisé, moins de 3 sommets, projet qui sort de la parcelle : erreur ou alerte.
- Deux cotes sur des limites quasi parallèles : erreur, il faut une limite perpendiculaire.
- Emprise du dessin différente de plus de 3 % de l'emprise déclarée : alerte.
- Contenance cadastrale et surface du dessin cadastral éloignées de plus de 5 % : alerte, taux d'emprise donné sur
  les deux surfaces (écarts de 1 % à 17 % observés sur des parcelles de SQY).
- **Côté sur la voie** : lu avec les routes de la BD TOPO ; à défaut, côté sans voisine. Toujours à confirmer. En
  cas de doute (parcelle d'angle, voie cadastrée, parcelle irrégulière), l'utilisateur indique le côté avec
  `--voie N` ou `voie_segment`, d'après le tableau des côtés.

## Mesures produites (`mesures.json`)
Distances de chaque construction aux côtés de la parcelle (voie, gauche vue de la rue, droite, fond) et aux limites
séparatives, profondeur depuis l'alignement et surface au-delà de 25 m (bande constructible, `methode-verdict.md`),
emprise au sol et taux, surface artificialisée, surface recouverte par chaque prescription surfacique, distances aux
bâtiments voisins, recouvrement d'un bâtiment existant.

## Limites
- Limites cadastrales indicatives : seul un bornage par un géomètre fait foi. Pour un projet à moins de 0,5 m d'un
  seuil du règlement, le dire.
- Le plan de masse ne porte pas de coordonnées : la position vient des cotes, donc de leur exactitude.
- Les distances sont perpendiculaires aux limites ; les articles du règlement peuvent mesurer autrement
  (par exemple à partir d'un débord de toit ou d'un point précis) : relire l'article.
- L'emprise au sol réglementaire peut inclure des éléments (débords, terrasses couvertes) que le plan n'affiche pas.
- Les hauteurs se mesurent au terrain naturel : le script ne les calcule pas.
- Aucun contrôle sur le PPRI de la Bièvre ni sur le titre VII (voir `sources.md`).
