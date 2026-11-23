import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildScale, pxToTime, timeToPx, toMs, toISO, phase } from './timeline.ts';
import { actorFamilies, applyFilters, emptyFilters } from './filters.ts';
import { parseHash, buildHash } from './url.ts';
import type { Actor, Incident } from './types.ts';

const incidents: Incident[] = JSON.parse(readFileSync('public/data/index.json', 'utf8'));
const actors: Record<string, Actor> = JSON.parse(readFileSync('public/data/actors.json', 'utf8'));
const scale = buildScale(incidents, '1993-01-01', '2003-09-30');

test('la scala copre tutto il periodo ed è monotona', () => {
  assert.equal(scale.months[0].key, '1993-01');
  assert.equal(scale.months.at(-1)!.key, '2003-09');
  let prev = -1;
  for (let px = 0; px <= scale.total; px += 37) {
    const t = pxToTime(scale, px);
    assert.ok(t >= prev, `non monotona a ${px}`);
    prev = t;
  }
});

test('andata e ritorno px -> data -> px', () => {
  for (const iso of ['1993-03-23', '1996-10-20', '1998-08-02', '2003-06-30']) {
    const px = timeToPx(scale, toMs(iso));
    assert.equal(toISO(pxToTime(scale, px)), iso);
  }
});

test('i mesi densi ricevono più spazio', () => {
  const m = (k: string) => scale.months.find((x) => x.key === k)!;
  assert.ok(m('1996-10').px > 3 * m('1994-03').px);
});

test('fasi di un incidente', () => {
  const i = { start: '1996-10-20', end: '1996-10-20' };
  assert.equal(phase(i, toMs('1996-10-19')), 'future');
  assert.equal(phase(i, toMs('1996-10-25')), 'active');
  assert.equal(phase(i, toMs('1997-01-01')), 'past');
});

test('filtro per attore include le affiliazioni (FRD dentro APR, ALC dentro MLC)', () => {
  const fam = actorFamilies(actors);
  assert.ok(fam.get('APR')!.has('FRD'));
  assert.ok(fam.get('MLC')!.has('ALC'));
  const f = emptyFilters();
  f.actors.add('MLC');
  const res = applyFilters(incidents, f, fam);
  assert.ok(res.length > 0 && res.every((i) => i.actors.some((a) => fam.get('MLC')!.has(a))));
  assert.ok(res.some((i) => i.id === 'P4-043'));
});

test('filtri combinati', () => {
  const fam = actorFamilies(actors);
  const f = emptyFilters();
  f.periods.add(4); f.cats.add('violenza_sessuale');
  const res = applyFilters(incidents, f, fam);
  assert.ok(res.length > 0 && res.every((i) => i.period === 4 && i.cats.includes('violenza_sessuale')));
});

test('hash URL', () => {
  const s = parseHash('#t=1996-10&lang=en&i=P2-031');
  assert.deepEqual(s, { t: '1996-10-01', lang: 'en', i: 'P2-031' });
  assert.equal(buildHash(s), '#t=1996-10-01&lang=en&i=P2-031');
  assert.deepEqual(parseHash('#i=<script>'), {});
});

test('dati: ogni incidente ha coordinate e date valide', () => {
  for (const i of incidents) {
    assert.ok(Number.isFinite(i.lat) && Number.isFinite(i.lon), i.id);
    assert.ok(i.lat > -14 && i.lat < 6 && i.lon > 11 && i.lon < 32, `${i.id} fuori RDC`);
    assert.ok(toMs(i.start) <= toMs(i.end), i.id);
  }
});
