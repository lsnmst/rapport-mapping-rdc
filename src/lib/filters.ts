import type { Actor, Filters, Incident } from './types.ts';

/** Relazioni per cui un attore "fa parte" di un altro ai fini del filtro (es. FRD -> APR, ALC -> MLC). */
const MEMBER_REL = ['alias', 'nuovo nome', 'componente', 'unità', 'fazione', 'ala armata', 'successore', 'erede'];

/** Per ogni attore, l'insieme degli attori che il filtro deve includere quando lo si seleziona. */
export function actorFamilies(actors: Record<string, Actor>): Map<string, Set<string>> {
  const children = new Map<string, Set<string>>();
  for (const [id, a] of Object.entries(actors)) {
    for (const [parent, , , rel] of a.aff ?? []) {
      if (MEMBER_REL.some((r) => rel.includes(r))) {
        if (!children.has(parent)) children.set(parent, new Set());
        children.get(parent)!.add(id);
      }
    }
  }
  const fam = new Map<string, Set<string>>();
  const visit = (id: string, acc: Set<string>) => {
    if (acc.has(id)) return;
    acc.add(id);
    for (const c of children.get(id) ?? []) visit(c, acc);
  };
  for (const id of Object.keys(actors)) {
    const acc = new Set<string>();
    visit(id, acc);
    fam.set(id, acc);
  }
  return fam;
}

export function emptyFilters(): Filters {
  return { actors: new Set(), cats: new Set(), periods: new Set() };
}

export function isEmpty(f: Filters): boolean {
  return f.actors.size === 0 && f.cats.size === 0 && f.periods.size === 0;
}

/** Filtri combinati in AND tra gruppi (attore, categoria, periodo) e in OR all'interno di ogni gruppo. */
export function matches(i: Incident, f: Filters, fam: Map<string, Set<string>>): boolean {
  if (f.periods.size && !f.periods.has(i.period)) return false;
  if (f.cats.size && !i.cats.some((c) => f.cats.has(c))) return false;
  if (f.actors.size) {
    let ok = false;
    for (const sel of f.actors) {
      const members = fam.get(sel) ?? new Set([sel]);
      if (i.actors.some((a) => members.has(a))) { ok = true; break; }
    }
    if (!ok) return false;
  }
  return true;
}

export function applyFilters(list: Incident[], f: Filters, fam: Map<string, Set<string>>): Incident[] {
  return isEmpty(f) ? list : list.filter((i) => matches(i, f, fam));
}

/** Numero di incidenti per attore (con le famiglie), per ordinare e mostrare il filtro. */
export function actorCounts(list: Incident[], fam: Map<string, Set<string>>): Map<string, number> {
  const out = new Map<string, number>();
  for (const [id, members] of fam) {
    let n = 0;
    for (const i of list) if (i.actors.some((a) => members.has(a))) n++;
    if (n) out.set(id, n);
  }
  return out;
}
