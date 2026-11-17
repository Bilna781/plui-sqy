# Licences, sources et mentions légales

PLUi SQY est un projet **non officiel**, bénévole et **sans but commercial** : aucune vente, aucune publicité,
aucun service payant. Il n'est ni édité, ni validé, ni soutenu par Saint-Quentin-en-Yvelines, l'IGN, le BRGM,
le ministère de la Transition écologique ou tout autre service de l'État. Aucun logo officiel n'est utilisé.

## Licences du projet

| Contenu | Licence | Fichier |
|---|---|---|
| Code (scripts, workflows, skill) | MIT | [LICENSE](LICENSE) |
| Documentation, fiches rédigées, illustrations, logo | CC BY 4.0 | [LICENSE-docs](LICENSE-docs) |
| Polices Archivo, Public Sans et IBM Plex Mono (logo, site, illustrations) | SIL Open Font License 1.1 | non redistribuées ; chargées depuis Google Fonts. Dans le logo, les textes sont convertis en tracés. La police Marianne, réservée à l'État, n'est pas utilisée. |

Ces licences couvrent uniquement le travail des contributeurs. Elles ne s'appliquent pas aux données et documents
des tiers listés ci-dessous, qui restent soumis à leurs propres conditions.

## Données et documents de tiers

### Documents du PLUi de Saint-Quentin-en-Yvelines
- Producteur : communauté d'agglomération de Saint-Quentin-en-Yvelines.
- Source utilisée : Géoportail de l'Urbanisme (https://www.geoportail-urbanisme.gouv.fr), dont les CGU placent
  les données d'urbanisme sous la Licence Ouverte.
- Ce dépôt **ne redistribue pas les PDF** du PLUi : il donne leurs liens officiels, leur empreinte et de courts
  extraits cités, avec la version et la date de chaque document. Les extraits ne sont pas modifiés ; toute
  reformulation est signalée comme telle.
- Le site saint-quentin-en-yvelines.fr interdit la reproduction de ses contenus sans accord préalable et réserve
  l'usage de son logo : aucun contenu éditorial de ce site n'est reproduit, aucun logo n'est utilisé.
- Les éléments soumis aux droits de tiers dans les documents (photos, études, fonds de carte) sont exclus.

### Géoplateforme IGN : géocodage, altimétrie, BD TOPO (WFS), Plan IGN et orthophotographies (WMS), isochrones
- Producteur : Institut national de l'information géographique et forestière (IGN).
- Licence : Licence Ouverte / Open Licence Etalab 2.0 (https://cartes.gouv.fr/cgu/).
- Mention : « © IGN – <produit> – <date de consultation> », ajoutée automatiquement à chaque fiche et image.
- Les SCAN 25 et SCAN 100, soumis à une licence spécifique, ne sont pas utilisés.
- Limites respectées (par seconde et par adresse IP) : géocodage 50, WFS 30, WMS-Raster 40, altimétrie 5,
  isochrone 5. Les scripts font une requête par service et par analyse.

### API Carto (modules Cadastre, Géoportail de l'Urbanisme, Nature)
- Opérateur : IGN. API Carto « conserve la licence des sources de données » (https://apicarto.ign.fr/api/doc/).
- Cadastre : données cadastrales sous Licence Ouverte. Aucun nom de propriétaire n'est récupéré ; ne pas croiser
  ces données pour identifier des personnes.
- Géoportail de l'Urbanisme : Licence Ouverte (https://www.geoportail-urbanisme.gouv.fr/cgu/).
- Nature : zonages issus des données du Muséum national d'Histoire naturelle, sous leur licence d'origine.

### Géorisques
- Éditeur : ministère de la Transition écologique ; opérateur : BRGM.
- Licence : Licence Ouverte V 2.0 (https://www.georisques.gouv.fr/cgu), avec obligation de mentionner la paternité
  et la date de dernière mise à jour. Mention reprise dans chaque fiche :
  « Ministère de la Transition écologique, de la Biodiversité et des Négociations Internationales sur le Climat
  et la Nature – Données originales téléchargées sur https://www.georisques.gouv.fr, consultées le <date> ».
- Limite : 1 000 requêtes par minute et par adresse IP.
- Les CGU précisent que ces données n'engagent pas la responsabilité de l'État.

## Avertissement
- Les résultats sont une aide à la lecture du PLUi. Ils ne remplacent ni un certificat d'urbanisme, ni l'avis du
  service instructeur, ni un conseil juridique. Seuls les documents officiels font foi.
- Les règles sont extraites automatiquement et peuvent comporter des erreurs. Chaque résultat indique la version
  du PLUi utilisée, sa date de publication et la date de consultation des API.
- Depuis le 1er janvier 2023, un PLU est exécutoire après sa publication sur le Géoportail de l'Urbanisme et sa
  transmission au préfet (code de l'urbanisme, art. L153-23).
- Le logiciel est fourni « en l'état », sans garantie (voir LICENSE).

## Données personnelles
- Le projet ne collecte aucune donnée. Une adresse saisie est envoyée uniquement aux API publiques ci-dessus ;
  les fiches restent sur la machine de l'utilisateur.
- Aucune adresse de particulier n'est publiée dans ce dépôt : les tests publics utilisent des lieux publics,
  les adresses témoins privées sont stockées dans un secret GitHub et n'apparaissent jamais dans les journaux.
- Ne publiez pas votre adresse dans une issue ou une discussion.

## Contact et retrait
Pour une correction ou une demande de retrait, ouvrez une issue (sans donnée personnelle) ou utilisez le contact
indiqué dans SECURITY.md.
