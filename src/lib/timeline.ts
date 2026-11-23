/**
 * Scala temporale "elastica": lo scorrimento della pagina viene convertito in una data.
 * Ogni mese riceve uno spazio verticale proporzionale a (base + densità degli incidenti),
 * così i mesi densi (es. ottobre-novembre 1996) scorrono più lentamente di quelli vuoti.
 */
import type { Incident } from './types.ts';

export const DAY = 86_400_000;

export function toMs(iso: string): number {
  const [y, m, d] = iso.split('-').map(Number);
  return Date.UTC(y, m - 1, d);
}

export function toISO(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

export interface Month {
  key: string;      // yyyy-mm
  t0: number;       // inizio del mese (ms)
  t1: number;       // inizio del mese successivo (ms)
  px0: number;      // posizione di scorrimento all'inizio del mese
  px: number;       // altezza assegnata al mese
  count: number;    // incidenti che iniziano nel mese
}

export interface Scale {
  months: Month[];
  total: number;
  t0: number;
  t1: number;
}

export interface ScaleOptions {
  basePx?: number;        // altezza minima di un mese
  perIncidentPx?: number; // altezza aggiunta per ogni incidente (con radice quadrata, per non esagerare)
}

export function buildScale(incidents: Incident[], from: string, to: string, opts: ScaleOptions = {}): Scale {
  const basePx = opts.basePx ?? 60;
  const per = opts.perIncidentPx ?? 90;
  const counts = new Map<string, number>();
  for (const i of incidents) {
    const k = i.start.slice(0, 7);
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  const months: Month[] = [];
  let [y, m] = from.split('-').map(Number);
  const [ey, em] = to.split('-').map(Number);
  let px0 = 0;
  while (y < ey || (y === ey && m <= em)) {
    const key = `${y}-${String(m).padStart(2, '0')}`;
    const t0 = Date.UTC(y, m - 1, 1);
    const ny = m === 12 ? y + 1 : y;
    const nm = m === 12 ? 1 : m + 1;
    const t1 = Date.UTC(ny, nm - 1, 1);
    const count = counts.get(key) ?? 0;
    const px = Math.round(basePx + per * Math.sqrt(count));
    months.push({ key, t0, t1, px0, px, count });
    px0 += px;
    y = ny; m = nm;
  }
  return { months, total: px0, t0: months[0].t0, t1: months[months.length - 1].t1 };
}

function findMonthByPx(s: Scale, px: number): Month {
  let lo = 0, hi = s.months.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (s.months[mid].px0 <= px) lo = mid; else hi = mid - 1;
  }
  return s.months[lo];
}

function findMonthByTime(s: Scale, t: number): Month {
  let lo = 0, hi = s.months.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (s.months[mid].t0 <= t) lo = mid; else hi = mid - 1;
  }
  return s.months[lo];
}

/** posizione di scorrimento (px, 0..total) -> istante (ms) */
export function pxToTime(s: Scale, px: number): number {
  if (px <= 0) return s.t0;
  if (px >= s.total) return s.t1 - 1;
  const m = findMonthByPx(s, px);
  return m.t0 + ((px - m.px0) / m.px) * (m.t1 - m.t0);
}

/** istante (ms) -> posizione di scorrimento (px) */
export function timeToPx(s: Scale, t: number): number {
  if (t <= s.t0) return 0;
  if (t >= s.t1) return s.total;
  const m = findMonthByTime(s, t);
  return m.px0 + ((t - m.t0) / (m.t1 - m.t0)) * m.px;
}

export type Phase = 'future' | 'active' | 'past';

/**
 * Stato di un incidente rispetto al tempo corrente:
 * - future: non ancora iniziato
 * - active: in corso, oppure terminato da meno di `afterDays` giorni
 * - past:   concluso
 */
export function phase(i: { start: string; end: string }, now: number, afterDays = 30): Phase {
  const s = toMs(i.start);
  if (now < s) return 'future';
  const e = toMs(i.end) + DAY;
  return now <= e + afterDays * DAY ? 'active' : 'past';
}
