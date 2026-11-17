# Vérifier un projet contre les règles

À utiliser quand l'utilisateur décrit un projet (dimensions, surface de plancher, hauteur, places de stationnement).

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

## Format du verdict
| Point | Projet | Règle (page) | Verdict |
|---|---|---|---|
| Emprise au sol | 112 m² | 30 % du terrain (p. 71) | conforme / non conforme / à vérifier |

- « à vérifier » quand une donnée manque ou qu'une règle dépend d'une appréciation du service instructeur.
- Après le tableau : pistes de mise en conformité, puis rappel que seul le service urbanisme de la commune
  peut se prononcer, et recommandation d'un certificat d'urbanisme opérationnel.
