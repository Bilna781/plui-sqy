---
name: veille
description: Vérifie si le PLUi de Saint-Quentin-en-Yvelines a changé depuis la version sur laquelle ce skill a été vérifié.
disable-model-invocation: true
allowed-tools: Bash(curl *) Bash(python3 *)
---
1. Lire la version de référence dans `${CLAUDE_PLUGIN_ROOT}/skills/plui/references/version.json`.
2. Interroger l'historique officiel :
   `curl -s "https://www.geoportail-urbanisme.gouv.fr/api/document?partition=DU_200058782"` et repérer l'entrée dont
   `effectiveStatus` vaut `EN_VIGUEUR` (champ `originalName`, date dans le nom = approbation ; `publicationDate`).
3. Si elle diffère de la référence : l'annoncer, avec les dates, et conseiller de mettre à jour le plugin
   (`/plugin marketplace update plui-sqy`) ou de vérifier chaque règle dans le règlement en vigueur.
4. Sinon : indiquer que le skill est à jour, avec la date de publication.
