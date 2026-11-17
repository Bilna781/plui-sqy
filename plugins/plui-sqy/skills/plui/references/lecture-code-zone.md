# Lire un code de zone du PLUi de SQY

Exemple : `URs2f9`, `UM4c16`. Source : article U 0 du règlement (« Fonctionnement du système d'indices »).

| Partie | Exemple | Sens |
|---|---|---|
| Famille | `U` | `U` urbaine, `AU` à urbaniser, `A` agricole, `N` naturelle |
| Vocation | `Rs`, `M` | Lettres après la famille : vocation du secteur (ex. `Rs` résidentiel strict, `M` mixte) |
| Indice de forme | `2` | Chiffre : règles d'implantation (articles 6, 7, 8) et de hauteur relative |
| Indice de densité | `f` | Lettre : emprise au sol (article 9) et espaces verts (article 13) |
| Hauteur | `9` | Nombre final : hauteur maximale en mètres (article 10) |

`reglement.py --zone <code>` fait ce découpage. Dans chaque article, chercher les paragraphes
« Dispositions applicables aux secteurs régis par l'indice … » qui correspondent à la zone.

Exemple vérifié dans le règlement du 19/02/2026 (page 71) : article U 9, indice « f » = emprise au sol maximale
de 30 % de la surface du terrain.
