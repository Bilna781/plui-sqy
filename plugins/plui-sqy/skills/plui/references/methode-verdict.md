# Vérifier un projet contre les règles

À utiliser quand l'utilisateur décrit un projet (dimensions, surface de plancher, hauteur, places de stationnement).

**Projet fourni sous forme de plan** : placer d'abord le projet sur le cadastre et faire confirmer les cotes par
l'utilisateur (`references/projet-sur-cadastre.md`). Le verdict ne s'appuie que sur des mesures au statut `valide`.

## Données à réunir
- Fiche de la parcelle (`parcelle.py`) : largeur et profondeur, surface, prescriptions, bâtiments existants.
- Projet : emprise au sol (débords de toiture compris), surface de plancher, hauteur au faîtage et à l'égout,
  pente de toit, distances aux limites et à la voie, places de stationnement, espaces verts et pleine terre.
  Demander ce qui manque plutôt que de supposer.

## Articles à contrôler (zone U)
| Article | Sujet | Commande |
|---|---|---|
| U 6 | Implantation par rapport aux voies (recul) | `--article 6` |
| U 7 | Implantation par rapport aux limites séparatives | `--article 7` |
| U 8 | Constructions les unes par rapport aux autres | `--article 8` |
| U 9 | Emprise au sol | `--article 9` |
| U 10 | Hauteur | `--article 10` |
| U 11 | Aspect extérieur, toitures, clôtures | `--article 11` |
| U 12 et commun 12 | Stationnement | `--article 12`, `--commun 12` |
| U 13 | Espaces libres, pleine terre, plantations | `--article 13` |

## Prescription d'implantation sur voie (code 15)
Quand la fiche contient « Implantation des constructions par rapport aux voies et aux emprises publiques », son
PDF (`urlfic`) reprend l'article 10 des dispositions communes, page 41 du règlement du 19/02/2026. Il vaut pour
une maison individuelle et s'ajoute aux articles 6 et 7 de la zone :
- **Recul d'alignement** : toute nouvelle construction est interdite dans la marge figurée sur le plan de zonage.
  La distance en mètres est lue sur le plan, pas dans le PDF.
- **Bande constructible** : les constructions ne peuvent s'implanter que sur 25 m de profondeur mesurés depuis
  l'alignement. Au-delà : extensions accolées à l'existant, limitées à 10 m² d'emprise au sol, et annexes de
  2,50 m de haut au plus et 15 m² au plus.
Pour une parcelle profonde (plus de 25 m), calculer la profondeur disponible avant de conclure. Le même texte est
attaché aux prescriptions linéaires et surfaciques (`lin_15_1`, `surf_15_1`), qui diffèrent seulement par leur
figuré. Le texte du PDF concerne aussi la diversité commerciale (changement de destination des locaux commerciaux
en rez-de-chaussée), qui ne concerne pas une maison.

## Format du verdict
| Point | Projet | Règle (page) | Verdict |
|---|---|---|---|
| Emprise au sol | 112 m² | 30 % du terrain (p. 71) | conforme / non conforme / à vérifier |

- « à vérifier » quand une donnée manque ou qu'une règle dépend d'une appréciation du service instructeur.
- Après le tableau : pistes de mise en conformité, puis rappel que seul le service urbanisme de la commune
  peut se prononcer, et recommandation d'un certificat d'urbanisme opérationnel.
