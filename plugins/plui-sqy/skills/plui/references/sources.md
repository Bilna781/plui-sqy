# Sources, licences et mentions

Toujours terminer une réponse par les mentions de `CREDITS.txt` (généré à chaque fiche avec la date du jour).

| Source | Licence | Mention |
|---|---|---|
| PLUi de Saint-Quentin-en-Yvelines, via le Géoportail de l'Urbanisme | Licence Ouverte | version, date de publication, date de consultation |
| IGN Géoplateforme (géocodage, cadastre, BD TOPO, altimétrie, Plan IGN, orthophotos, isochrones) | Licence Ouverte Etalab 2.0 | « © IGN – Géoplateforme – consulté le … » |
| API Carto Nature (MNHN) | licence d'origine | source citée |
| Géorisques | Licence Ouverte 2.0 | « Ministère de la Transition écologique, de la Biodiversité et des Négociations Internationales sur le Climat et la Nature – Données originales téléchargées sur https://www.georisques.gouv.fr, consultées le … » |

Ne jamais reproduire le contenu éditorial du site saint-quentin-en-yvelines.fr ni utiliser son logo.
Citer le règlement par courts extraits, avec la page, sans modifier le texte.

Limites de requêtes à respecter : géocodage 50/s, WFS 30/s, WMS 40/s, altimétrie 5/s, isochrone 5/s par IP ;
Géorisques 1 000 par minute. Le script fait une requête par service et par fiche.

## Limites d'extraction des documents du PLUi
Les documents ont été lus par extraction de **texte brut** des PDF. Ni les cartes ni les images n'ont été analysées.
- **Plans de zonage et plans de servitudes** : cartes, donc aucune règle exploitable. La zone et les servitudes
  d'une parcelle viennent du Géoportail de l'Urbanisme.
- **PPRI de la vallée de la Bièvre (arrêté 661ARR)** : police du PDF mal encodée. Seuls les titres et les zones
  (rouge, bleue, marron) ont été lus, pas les prescriptions chiffrées de chaque zone. Le skill peut signaler qu'une
  parcelle est en zone de PPRI, pas dire ce que cette zone impose : renvoyer au PDF ou au service instructeur.
- **Annexe 9 du règlement (guide éco-jardin du PNR)** : texte décalé d'une lettre, décodé ensuite. Noms de plantes et
  chiffres peu fiables, non repris dans le skill.
- **Annexes 2, 3, 5, 7, 8 et 10** : texte propre, noms et chiffres relus dans le PDF (`references/annexes-reglement.md`).
  Les noms scientifiques de l'annexe 3 reprennent les quelques coquilles du PDF.
- **Titre VII du règlement (inventaire patrimonial) et documents hors règlement** : analysés dans un graphe de
  connaissances, pas intégrés au skill. Seules les prescriptions indiquées par la fiche (`urlfic`) sont à lire.

