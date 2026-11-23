# RDC 1993–2003 · Carte du Rapport Mapping / Mapping Report map

Carte chronologique des incidents décrits dans le *Rapport du Projet Mapping concernant les violations les plus graves des droits de l'homme et du droit international humanitaire commises entre mars 1993 et juin 2003 sur le territoire de la République démocratique du Congo* (HCDH, août 2010). Le temps avance en faisant défiler la page vers le bas et recule en la faisant défiler vers le haut.

A chronological map of the incidents described in the UN *Mapping Exercise Report* on the DRC, 1993–2003 (OHCHR, August 2010). Time moves forward as you scroll down and back as you scroll up.

- Rapport (FR, version originale) : https://www.ohchr.org/sites/default/files/Documents/Countries/CD/DRC_MAPPING_REPORT_FINAL_FR.pdf
- Report (EN, unofficial translation): https://www.ohchr.org/sites/default/files/Documents/Countries/CD/DRC_MAPPING_REPORT_FINAL_EN.pdf

## Démarrer / Getting started

```bash
npm install
npm run dev        # http://localhost:5173
npm test           # tests de la logique (Node ≥ 22.6)
npm run check      # vérification TypeScript / Svelte
npm run build      # site statique dans dist/
```

Le fond de carte par défaut est OpenFreeMap (sans clé). Pour un autre style : `VITE_MAP_STYLE=<url du style> npm run dev`.

**GitHub Pages** : activer *Settings → Pages → Source: GitHub Actions*. Chaque push sur `main` lance `.github/workflows/deploy.yml`.

## Structure

| Dossier | Contenu |
|---|---|
| `src/` | application Svelte 5 + TypeScript + MapLibre GL |
| `src/lib/timeline.ts` | échelle temporelle « élastique » : défilement ↔ date |
| `public/data/` | données publiées (générées par `npm run data`) |
| `dataset/` | jeu de données complet : 614 incidents FR/EN, lieux, auteurs, victimes, violations, dates, géolocalisation |
| `pipeline/` | extraction depuis les PDF, annotations, géolocalisation |
| `pipeline/annotations/` | annotations ligne par ligne de chaque incident (format texte, voir `pipeline/dsl.py`) |

## Méthode

1. **Extraction** (`pipeline/parse.py`, `build_period.py`) : chaque puce (•) de la Section I du rapport est un incident ; alignement FR/EN par numéro de paragraphe. 614 incidents extraits sur les 617 annoncés par le rapport.
2. **Annotation** (`pipeline/annotations/*.txt`) : lieux par rôle (lieu de l'incident, repère, provenance, destination), actes (auteurs présumés, victimes, violations, chiffres tels que formulés par le rapport, degré de certitude). Les auteurs suivent un registre unique avec alias et affiliations dans le temps (`pipeline/registry.py`).
3. **Dates** (`pipeline/dates.py`) : début, fin et précision, extraites du texte.
4. **Géolocalisation** (`pipeline/geoloc_rdc.py`, `rescore.py`) : croisement de OpenStreetMap, RGC, GRID3, GeoNames et UCDP GED, contrôle par les limites COD-AB et par les relations spatiales du texte (« à 3 km de Kolwezi en direction de Kapata »).
   - **high** : nom identique, confirmé par plusieurs sources indépendantes, dans le territoire attendu ;
   - **low** : position plausible mais incertaine (source unique, graphie différente, homonymes, position estimée) ;
   - **none** : seule la zone est connue (territoire ou province) ; affichée comme une zone diffuse.

## Choix éditoriaux

- Le rapport décrit des violations **présumées** et ne se prononce pas sur la responsabilité pénale individuelle. Aucun nom de personne n'est ajouté aux données structurées.
- Les filtres portent sur l'auteur présumé, le type de violation et la période. Il n'y a pas de filtre par appartenance ethnique des victimes : elle figure dans la fiche, telle que le rapport la décrit.
- Les nombres de victimes ne sont pas additionnés : chaque fiche reprend la formule du rapport (« au moins 38 », « plusieurs centaines »).

## Licences et crédits

Texte du rapport : © Nations Unies, reproduit à des fins d'information non commerciale avec mention de la source. Géolocalisation : © contributeurs OpenStreetMap (ODbL), Référentiel Géographique Commun (CC BY-NC), GRID3, GeoNames (CC BY), UCDP GED (CC BY). Fond de carte : OpenFreeMap / OpenMapTiles / OpenStreetMap.
