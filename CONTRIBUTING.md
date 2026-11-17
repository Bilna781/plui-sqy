# Contribuer

Merci ! Le projet est bénévole, non officiel et sans but commercial.

## Règles
- **Aucune donnée personnelle** : pas d'adresse de particulier dans le code, les tests, les issues ou les commits.
  Les tests publics utilisent des lieux publics ; les témoins privés vont dans le secret `PLUI_TEMOINS`.
- **Sources** : toute règle citée vient du règlement en vigueur, avec la page. Pas de reformulation présentée
  comme le texte officiel.
- **Pas de PDF dans git** : lien officiel et empreinte seulement.
- **Licences** : code sous MIT, documentation sous CC BY 4.0. En contribuant, vous acceptez ces licences.

## Travailler en local
```bash
git clone https://github.com/Bilna781/plui-sqy && cd plui-sqy
claude plugin marketplace add ./          # puis /plugin install plui-sqy@plui-sqy
uv run plugins/plui-sqy/skills/plui/scripts/parcelle.py --selftest
python3 veille/check.py
```

## Proposer un changement
1. Une branche par sujet, un commit par changement lisible.
2. Une PR qui décrit ce qui change et comment c'est vérifié.
3. Les contrôles automatiques (structure du plugin, autotest) doivent passer.

Code de conduite : [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
