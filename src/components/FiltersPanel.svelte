<script lang="ts">
  import type { Actor, Filters, Lang, Vocab } from '../lib/types.ts';
  import { label, t } from '../lib/i18n.ts';

  interface Props {
    filters: Filters;
    lang: Lang;
    vocab: Vocab;
    actors: Record<string, Actor>;
    actorCounts: Map<string, number>;
    catCounts: Map<string, number>;
    onchange: (f: Filters) => void;
    onclose: () => void;
  }
  let { filters, lang, vocab, actors, actorCounts, catCounts, onchange, onclose }: Props = $props();

  let query = $state('');

  const actorList = $derived.by(() => {
    const q = query.trim().toLowerCase();
    return [...actorCounts.entries()]
      .filter(([id]) => id !== 'NON_SPECIFICATO')
      .filter(([id]) => !q || actors[id][lang].toLowerCase().includes(q) || id.toLowerCase().includes(q)
        || actors[id].alias.some((a) => a.toLowerCase().includes(q)))
      .sort((a, b) => b[1] - a[1]);
  });

  function toggle<T>(set: Set<T>, v: T): Set<T> {
    const s = new Set(set);
    s.has(v) ? s.delete(v) : s.add(v);
    return s;
  }
  const setPeriods = (p: number) => onchange({ ...filters, periods: toggle(filters.periods, p) });
  const setCat = (c: string) => onchange({ ...filters, cats: toggle(filters.cats, c) });
  const setActor = (a: string) => onchange({ ...filters, actors: toggle(filters.actors, a) });
  const reset = () => onchange({ actors: new Set(), cats: new Set(), periods: new Set() });
</script>

<aside class="filters" aria-labelledby="filters-title">
  <header>
    <h2 id="filters-title">{t(lang, 'filters')}</h2>
    <div>
      <button class="link" onclick={reset}>{t(lang, 'reset')}</button>
      <button class="close" onclick={onclose} aria-label={t(lang, 'close')}>×</button>
    </div>
  </header>

  <fieldset>
    <legend>{t(lang, 'periods')}</legend>
    {#each [1, 2, 3, 4] as p}
      <label class="opt">
        <input type="checkbox" checked={filters.periods.has(p)} onchange={() => setPeriods(p)} />
        <span>{label(vocab, 'periods', String(p), lang)}</span>
      </label>
    {/each}
  </fieldset>

  <fieldset>
    <legend>{t(lang, 'categories')}</legend>
    {#each vocab.categoryOrder as c}
      <label class="opt">
        <input type="checkbox" checked={filters.cats.has(c)} onchange={() => setCat(c)} />
        <span>{label(vocab, 'categories', c, lang)}</span>
        <span class="n">{catCounts.get(c) ?? 0}</span>
      </label>
    {/each}
  </fieldset>

  <fieldset>
    <legend>{t(lang, 'actors')}</legend>
    <p class="hint">{t(lang, 'includesAffiliates')}</p>
    <input class="search" type="search" bind:value={query} placeholder={t(lang, 'searchActor')} aria-label={t(lang, 'searchActor')} />
    <div class="actors">
      {#each actorList as [id, n] (id)}
        <label class="opt">
          <input type="checkbox" checked={filters.actors.has(id)} onchange={() => setActor(id)} />
          <span>{actors[id][lang]}</span>
          <span class="n">{n}</span>
        </label>
      {/each}
    </div>
  </fieldset>
</aside>

<style>
  .filters {
    position: fixed; top: 0; left: 0; bottom: 0; z-index: 20;
    width: min(380px, 100vw); overflow-y: auto;
    background: var(--paper); color: var(--ink);
    box-shadow: 4px 0 24px rgb(0 0 0 / 0.18);
    padding: 1.25rem 1.25rem 3rem;
  }
  header { display: flex; justify-content: space-between; align-items: center; }
  h2 { margin: 0; font: 600 1.3rem var(--serif); }
  fieldset { border: 0; padding: 0; margin: 1.2rem 0 0; }
  legend { font: 600 0.75rem var(--sans); text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin-bottom: 0.4rem; }
  .opt { display: grid; grid-template-columns: auto 1fr auto; gap: 0.5rem; align-items: start; padding: 0.2rem 0; font-size: 0.9rem; cursor: pointer; }
  .n { color: var(--muted); font: 0.8rem var(--mono); }
  .hint { font-size: 0.8rem; color: var(--muted); margin: 0 0 0.4rem; }
  .search { width: 100%; padding: 0.4rem 0.5rem; border: 1px solid var(--rule); border-radius: 4px; font: inherit; margin-bottom: 0.4rem; }
  .close { font-size: 1.8rem; line-height: 1; background: none; border: 0; cursor: pointer; color: var(--ink); }
  .link { background: none; border: 0; color: var(--accent); cursor: pointer; text-decoration: underline; font: inherit; }
</style>
