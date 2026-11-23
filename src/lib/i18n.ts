import type { Bi, Lang, Vocab } from './types.ts';

const UI = {
  title: { fr: 'RDC 1993–2003 : la carte du Rapport Mapping', en: 'DRC 1993–2003: mapping the Mapping Report' },
  subtitle: {
    fr: "Plus de 600 incidents de violations graves des droits de l'homme et du droit international humanitaire documentés par les Nations Unies",
    en: 'More than 600 incidents of serious violations of human rights and international humanitarian law documented by the United Nations',
  },
  introBody: {
    fr: "Cette carte présente les incidents décrits dans le Rapport du Projet Mapping publié en 2010 par le Haut-Commissariat des Nations Unies aux droits de l'homme. Faites défiler la page vers le bas pour avancer dans le temps, vers le haut pour revenir en arrière.",
    en: 'This map presents the incidents described in the Mapping Exercise Report published in 2010 by the UN Office of the High Commissioner for Human Rights. Scroll down to move forward in time, up to go back.',
  },
  warning: {
    fr: 'Avertissement : les fiches décrivent des massacres, des actes de torture et des violences sexuelles.',
    en: 'Warning: the incident records describe massacres, torture and sexual violence.',
  },
  alleged: {
    fr: "Le rapport décrit des violations présumées ; il ne se prononce pas sur la responsabilité pénale individuelle.",
    en: 'The report describes alleged violations; it does not determine individual criminal responsibility.',
  },
  scrollHint: { fr: 'Faites défiler pour commencer', en: 'Scroll to begin' },
  outroTitle: { fr: 'Fin de la période couverte par le rapport (juin 2003)', en: 'End of the period covered by the report (June 2003)' },
  outroBody: {
    fr: "Sources : Rapport du Projet Mapping (HCDH, 2010), version française originale et traduction anglaise non officielle. Géolocalisation : OpenStreetMap, Référentiel Géographique Commun, GRID3, GeoNames, UCDP GED, limites administratives COD-AB (OCHA).",
    en: 'Sources: Mapping Exercise Report (OHCHR, 2010), original French version and unofficial English translation. Geolocation: OpenStreetMap, Référentiel Géographique Commun, GRID3, GeoNames, UCDP GED, COD-AB administrative boundaries (OCHA).',
  },
  readReport: { fr: 'Lire le rapport', en: 'Read the report' },
  filters: { fr: 'Filtres', en: 'Filters' },
  reset: { fr: 'Réinitialiser', en: 'Reset' },
  periods: { fr: 'Période', en: 'Period' },
  categories: { fr: 'Type de violation', en: 'Type of violation' },
  actors: { fr: 'Auteurs présumés', en: 'Alleged perpetrators' },
  searchActor: { fr: 'Rechercher un groupe…', en: 'Search a group…' },
  includesAffiliates: {
    fr: 'Inclut les unités, factions et ailes armées rattachées.',
    en: 'Includes affiliated units, factions and armed wings.',
  },
  shown: { fr: 'incidents affichés', en: 'incidents shown' },
  activeNow: { fr: 'En cours à cette date', en: 'Ongoing at this date' },
  noneActive: { fr: 'Aucun incident en cours à cette date.', en: 'No ongoing incident at this date.' },
  prev: { fr: 'Incident précédent', en: 'Previous incident' },
  next: { fr: 'Incident suivant', en: 'Next incident' },
  close: { fr: 'Fermer', en: 'Close' },
  legend: { fr: 'Légende', en: 'Legend' },
  active: { fr: 'en cours', en: 'ongoing' },
  past: { fr: 'passé', en: 'past' },
  date: { fr: 'Date', en: 'Date' },
  places: { fr: 'Lieux', en: 'Places' },
  province: { fr: 'Province (1993-2003)', en: 'Province (1993-2003)' },
  perpetrators: { fr: 'Auteurs présumés', en: 'Alleged perpetrators' },
  victims: { fr: 'Victimes', en: 'Victims' },
  violations: { fr: 'Violations', en: 'Violations' },
  figures: { fr: 'Chiffres (formule du rapport)', en: 'Figures (as worded in the report)' },
  reportText: { fr: 'Texte du rapport', en: 'Report text' },
  context: { fr: 'Contexte (paragraphe du rapport)', en: 'Context (report paragraph)' },
  sources: { fr: 'Sources citées par le rapport', en: 'Sources cited by the report' },
  paragraph: { fr: 'paragraphe', en: 'paragraph' },
  page: { fr: 'page', en: 'page' },
  openPdf: { fr: 'Ouvrir le PDF à cette page', en: 'Open the PDF at this page' },
  frenchOriginal: { fr: '', en: 'French original wording:' },
  loading: { fr: 'Chargement…', en: 'Loading…' },
  showContext: { fr: 'Afficher le contexte', en: 'Show context' },
  language: { fr: 'Langue', en: 'Language' },
  about: { fr: 'À propos', en: 'About' },
  mapLabel: { fr: 'Carte des incidents', en: 'Map of incidents' },
  mapHelp: {
    fr: 'Ctrl + molette ou deux doigts pour zoomer et déplacer la carte.',
    en: 'Ctrl + scroll or two fingers to zoom and pan the map.',
  },
  geoConfidence: { fr: 'Fiabilité de la position', en: 'Position reliability' },
} satisfies Record<string, Bi>;

export type UiKey = keyof typeof UI;

export function t(lang: Lang, key: UiKey): string {
  return UI[key][lang];
}

export function label(vocab: Vocab, group: string, key: string | null | undefined, lang: Lang): string {
  if (!key) return '';
  return vocab[group]?.[key]?.[lang] ?? key;
}

const locale = (lang: Lang) => (lang === 'fr' ? 'fr-FR' : 'en-GB');

export function fmtMonth(lang: Lang, ms: number): string {
  return new Intl.DateTimeFormat(locale(lang), { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(ms);
}

export function fmtDay(lang: Lang, ms: number): string {
  return new Intl.DateTimeFormat(locale(lang), { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(ms);
}

/** Data di un incidente formattata secondo la sua precisione. */
export function fmtIncidentDate(lang: Lang, start: string, end: string, dp: string): string {
  const s = Date.parse(start + 'T00:00:00Z');
  const e = Date.parse(end + 'T00:00:00Z');
  const around = lang === 'fr' ? 'vers le ' : 'around ';
  if (dp.startsWith('giorno')) {
    const pre = dp.startsWith('giorno_circa') ? around : '';
    return start === end ? pre + fmtDay(lang, s) : `${fmtDay(lang, s)} – ${fmtDay(lang, e)}`;
  }
  if (dp.startsWith('anno') || dp === 'anni' || dp === 'periodo') {
    const ys = start.slice(0, 4), ye = end.slice(0, 4);
    return ys === ye ? ys : `${ys} – ${ye}`;
  }
  const ms = fmtMonth(lang, s), me = fmtMonth(lang, e);
  return ms === me ? ms : `${ms} – ${me}`;
}

export function bi(b: Bi | undefined, lang: Lang): string {
  return b ? b[lang] || b.fr : '';
}
