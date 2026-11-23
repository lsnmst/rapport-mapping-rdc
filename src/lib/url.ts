import type { Lang } from './types.ts';

export interface UrlState {
  t?: string;      // data corrente yyyy-mm-dd
  lang?: Lang;
  i?: string;      // incidente aperto
}

export function parseHash(hash: string): UrlState {
  const p = new URLSearchParams(hash.replace(/^#/, ''));
  const out: UrlState = {};
  const t = p.get('t');
  if (t && /^\d{4}-\d{2}(-\d{2})?$/.test(t)) out.t = t.length === 7 ? `${t}-01` : t;
  const lang = p.get('lang');
  if (lang === 'fr' || lang === 'en') out.lang = lang;
  const i = p.get('i');
  if (i && /^P[1-4]-\d{3}$/.test(i)) out.i = i;
  return out;
}

export function buildHash(s: UrlState): string {
  const p = new URLSearchParams();
  if (s.t) p.set('t', s.t);
  if (s.lang) p.set('lang', s.lang);
  if (s.i) p.set('i', s.i);
  const q = p.toString();
  return q ? `#${q}` : '';
}
