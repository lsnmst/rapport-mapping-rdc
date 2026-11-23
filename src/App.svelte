<script lang="ts">
  import { onMount } from 'svelte';
  import MapView from './components/MapView.svelte';
  import IncidentPanel from './components/IncidentPanel.svelte';
  import FiltersPanel from './components/FiltersPanel.svelte';
  import type { Filters, Lang, Padding } from './lib/types.ts';
  import { PERIOD_COLORS } from './lib/periods.ts';
  import { loadCore, type CoreData } from './lib/data.ts';
  import { buildScale, pxToTime, timeToPx, toMs, toISO, phase, DAY, type Scale } from './lib/timeline.ts';
  import { actorFamilies, applyFilters, actorCounts, emptyFilters, isEmpty } from './lib/filters.ts';
  import { parseHash, buildHash } from './lib/url.ts';
  import { t, label, fmtMonth, fmtIncidentDate } from './lib/i18n.ts';

  const STYLE_URL = import.meta.env.VITE_MAP_STYLE ?? 'https://tiles.openfreemap.org/styles/positron';
  const FROM = '1993-01-01';
  const TO = '2003-09-30';

  const initial = parseHash(location.hash);
  let lang = $state<Lang>(initial.lang ?? 'fr');   // il francese è la lingua originale del rapporto
  let data = $state<CoreData | null>(null);
  let loadError = $state<string | null>(null);
  let scale = $state<Scale | null>(null);
  let scrollY = $state(0);
  let vh = $state(800);
  let vw = $state(1200);
  let listCollapsed = $state(false);
  let awayAnchor: number | null = null;   // posizione di scroll quando la mappa è stata ingrandita
  let filters = $state<Filters>(emptyFilters());
  let selectedId = $state<string | null>(initial.i ?? null);
  let filtersOpen = $state(false);
  let listOpen = $state(false);
  let mapView: ReturnType<typeof MapView> | undefined = $state();

  const intro = $derived(Math.round(vh * 1.1));
  const overview = $derived(scrollY < intro * 0.6);   // apertura: tutti i punti, prima dello storyscrolling
  const desktop = $derived(vw >= 900);
  // spazio occupato dai pannelli: la mappa centra la RDC nell'area libera
  const padding = $derived<Padding>(desktop
    ? { top: 70, bottom: 40, right: overview ? 40 : listCollapsed ? 70 : 350, left: overview ? Math.min(600, vw * 0.42) : 40 }
    : { top: 60, bottom: overview ? 40 : 190, left: 12, right: 12 });
  const now = $derived(scale ? pxToTime(scale, scrollY - intro) : toMs(FROM));
  const families = $derived(data ? actorFamilies(data.actors) : new Map());
  const filtered = $derived(data ? applyFilters(data.incidents, filters, families) : []);
  const visible = $derived(filtered.filter((i) => toMs(i.start) <= now));
  const active = $derived(filtered.filter((i) => phase(i, now) === 'active'));
  const selected = $derived(data?.incidents.find((i) => i.id === selectedId) ?? null);
  const periodNow = $derived.by(() => {
    if (!data) return 1;
    const iso = toISO(now);
    for (const p of ['4', '3', '2', '1']) if (iso >= data.vocab.periodRanges[p][0]) return Number(p);
    return 1;
  });
  const counts = $derived.by(() => {
    const ac = data ? actorCounts(data.incidents, families) : new Map<string, number>();
    const cc = new Map<string, number>();
    for (const i of data?.incidents ?? []) for (const c of i.cats) cc.set(c, (cc.get(c) ?? 0) + 1);
    return { ac, cc };
  });
  const chapters = $derived.by(() => {
    if (!data || !scale) return [];
    return ['1', '2', '3', '4'].map((p) => ({
      p,
      top: intro + timeToPx(scale!, toMs(data!.vocab.periodRanges[p][0])),
      n: filtered.filter((i) => String(i.period) === p).length,
    }));
  });

  // velatura della mappa e colore dei pannelli secondo il periodo corrente
  $effect(() => {
    const root = document.documentElement.style;
    if (overview) { root.removeProperty('--period-bg'); root.removeProperty('--period-ink'); return; }
    const c = PERIOD_COLORS[periodNow as 1 | 2 | 3 | 4];
    root.setProperty('--period-bg', c.bg);
    root.setProperty('--period-ink', c.ink);
  });

  // la mappa è stata ingrandita (clic, doppio clic, zoom sul mese): alla ripresa dello scroll torna all'insieme
  function onAway() { awayAnchor = scrollY; }
  $effect(() => {
    if (awayAnchor !== null && Math.abs(scrollY - awayAnchor) > 80) {
      awayAnchor = null;
      mapView?.resetView();
    }
  });

  onMount(() => {
    vh = innerHeight; vw = innerWidth;
    loadCore()
      .then((d) => {
        data = d;
        scale = buildScale(d.incidents, FROM, TO);
        requestAnimationFrame(() => {
          if (initial.t && scale) scrollTo({ top: intro + timeToPx(scale, toMs(initial.t)) });
          scrollY = window.scrollY;
        });
      })
      .catch((e) => (loadError = String(e)));

    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => { raf = 0; scrollY = window.scrollY; });
    };
    const onResize = () => { vh = innerHeight; vw = innerWidth; };
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onResize);
    return () => { removeEventListener('scroll', onScroll); removeEventListener('resize', onResize); };
  });

  // stato nell'URL (data, lingua, incidente aperto), aggiornato senza riempire la cronologia
  let hashTimer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    const state = { t: scrollY > intro ? toISO(now) : undefined, lang, i: selectedId ?? undefined };
    clearTimeout(hashTimer);
    hashTimer = setTimeout(() => history.replaceState(null, '', buildHash(state) || location.pathname), 250);
  });
  $effect(() => { document.documentElement.lang = lang; });

  function scrollToTime(ms: number) {
    if (!scale) return;
    const smooth = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    scrollTo({ top: intro + timeToPx(scale, ms) + 2, behavior: smooth ? 'smooth' : 'auto' });
  }
  function step(dir: 1 | -1) {
    const cur = Math.floor(now / DAY);
    const list = dir === 1
      ? filtered.find((i) => Math.floor(toMs(i.start) / DAY) > cur)
      : [...filtered].reverse().find((i) => Math.floor(toMs(i.start) / DAY) < cur);
    if (list) scrollToTime(toMs(list.start));
  }
  function open(id: string) {
    selectedId = id;
    const i = data?.incidents.find((x) => x.id === id);
    if (i) mapView?.focus(i, desktop ? 460 - padding.right + 40 : 0);
  }
  function closePanel() {
    selectedId = null;
    awayAnchor = null;
    mapView?.resetView();
  }
  function zoomMonth() {
    mapView?.zoomTo(active.length ? active : visible.slice(-10));
  }
</script>

{#if loadError}
  <p class="fatal">{loadError}</p>
{:else}
  <MapView bind:this={mapView} incidents={filtered} {now} {overview} {padding} selected={selectedId} {lang} styleUrl={STYLE_URL}
    onselect={open} onaway={onAway} />
  <div class="tint" class:on={!overview} aria-hidden="true"></div>
{/if}

<header class="top">
  <h1>{t(lang, 'title')}</h1>
  <nav>
    <button class="btn" onclick={() => (filtersOpen = !filtersOpen)} aria-expanded={filtersOpen}>
      {t(lang, 'filters')}{#if !isEmpty(filters)} •{/if}
    </button>
    <div class="lang" role="group" aria-label={t(lang, 'language')}>
      <button class:on={lang === 'fr'} aria-pressed={lang === 'fr'} onclick={() => (lang = 'fr')}>FR</button>
      <button class:on={lang === 'en'} aria-pressed={lang === 'en'} onclick={() => (lang = 'en')}>EN</button>
    </div>
  </nav>
</header>

{#if data && scale}
  <!-- La lunghezza della pagina è il tempo: scorrere verso il basso fa avanzare la data. -->
  <main class="track" style:height="{intro + scale.total + vh}px">
    <section class="card intro" style:top="{vh * 0.18}px">
      <p class="eyebrow">1993 – 2003</p>
      <h2>{t(lang, 'title')}</h2>
      <p class="lead">{t(lang, 'subtitle')}</p>
      <p>{t(lang, 'introBody')}</p>
      <p class="warn" role="note">{t(lang, 'warning')}</p>
      <p class="small">{t(lang, 'alleged')}</p>
      <p class="hint">↓ {t(lang, 'scrollHint')}</p>
    </section>

    {#each chapters as c (c.p)}
      <section class="card chapter" style:top="{c.top}px">
        <p class="eyebrow">{c.n} {t(lang, 'shown')}</p>
        <h2>{label(data.vocab, 'periods', c.p, lang)}</h2>
      </section>
    {/each}

    <section class="card outro" style:top="{intro + scale.total + vh * 0.2}px">
      <h2>{t(lang, 'outroTitle')}</h2>
      <p class="small">{t(lang, 'outroBody')}</p>
      <p><a href={lang === 'fr' ? data.source.url_fr : data.source.url_en} target="_blank" rel="noopener">{t(lang, 'readReport')}</a></p>
    </section>
  </main>

  {#if !overview}
    <div class="hud" aria-live="polite">
      <p class="period">{label(data.vocab, 'periods', String(periodNow), lang)}</p>
      <p class="now">{fmtMonth(lang, now)}</p>
      <p class="count">{visible.length} / {filtered.length} {t(lang, 'shown')}</p>
      <div class="steps">
        <button class="btn" onclick={() => step(-1)} aria-label={t(lang, 'prev')}>‹</button>
        <button class="btn" onclick={() => step(1)} aria-label={t(lang, 'next')}>›</button>
        <button class="btn" onclick={zoomMonth}>{t(lang, 'zoomMonth')}</button>
        <button class="btn list-toggle" onclick={() => (listOpen = !listOpen)} aria-expanded={listOpen}>
          {t(lang, 'activeNow')} ({active.length})
        </button>
      </div>
      <p class="small help">{t(lang, 'mapHelp')}</p>
    </div>

    {#if desktop && listCollapsed}
      <button class="btn expand" onclick={() => (listCollapsed = false)} aria-label={t(lang, 'showList')}>
        ‹ {active.length}
      </button>
    {:else}
      <section class="active" class:open={listOpen} aria-label={t(lang, 'activeNow')}>
        <div class="active-head">
          <h2>{t(lang, 'activeNow')}</h2>
          {#if desktop}
            <button class="collapse" onclick={() => (listCollapsed = true)} aria-label={t(lang, 'hideList')}>›</button>
          {/if}
        </div>
        <div class="active-list">
          {#if active.length === 0}
            <p class="small">{t(lang, 'noneActive')}</p>
          {:else}
            <ul>
              {#each active as i (i.id)}
                <li>
                  <button onclick={() => open(i.id)} class:sel={i.id === selectedId}>
                    <span class="place">{i.place}</span>
                    <span class="small">{fmtIncidentDate(lang, i.start, i.end, i.dp)} · {i.actors.map((a) => data!.actors[a]?.[lang].replace(/\s*\(.*\)$/, '')).join(', ')}</span>
                  </button>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
        <div class="legend" aria-label={t(lang, 'legend')}>
          <p><span class="sym s-high"></span>{label(data.vocab, 'confidence', 'high', lang)}</p>
          <p><span class="sym s-low"></span>{label(data.vocab, 'confidence', 'low', lang)}</p>
          <p><span class="sym s-none"></span>{label(data.vocab, 'confidence', 'none', lang)}</p>
          <p><span class="sym s-past"></span>{t(lang, 'past')}</p>
        </div>
      </section>
    {/if}
  {/if}

  {#if filtersOpen}
    <FiltersPanel {filters} {lang} vocab={data.vocab} actors={data.actors} actorCounts={counts.ac} catCounts={counts.cc}
      onchange={(f) => (filters = f)} onclose={() => (filtersOpen = false)} />
  {/if}

  {#if selected}
    <IncidentPanel incident={selected} {lang} vocab={data.vocab} actors={data.actors} pdf={data.source}
      onclose={closePanel} />
  {/if}
{:else if !loadError}
  <p class="loading">{t(lang, 'loading')}</p>
{/if}

<style>
  .top {
    position: fixed; top: 0; left: 0; right: 0; z-index: 10;
    display: flex; justify-content: space-between; align-items: center; gap: 1rem;
    padding: 0.6rem 1rem; background: var(--panel-bg); backdrop-filter: blur(6px); transition: background-color 0.8s;
    border-bottom: 1px solid var(--rule);
  }
  .top h1 { margin: 0; font: 600 1rem/1.2 var(--serif); }
  nav { display: flex; gap: 0.6rem; align-items: center; }
  .lang { display: flex; border: 1px solid var(--rule); border-radius: 4px; overflow: hidden; }
  .lang button { border: 0; background: none; padding: 0.3rem 0.6rem; cursor: pointer; font: 600 0.8rem var(--sans); color: var(--muted); }
  .lang button.on { background: var(--ink); color: #fff; }
  .btn { border: 1px solid var(--rule); background: #fff; border-radius: 4px; padding: 0.35rem 0.7rem; cursor: pointer; font: 0.85rem var(--sans); color: var(--ink); }

  .track { position: relative; z-index: 2; pointer-events: none; }
  .card {
    position: absolute; left: clamp(1rem, 4vw, 3rem); width: min(520px, calc(100vw - 2rem));
    pointer-events: auto; background: var(--panel-bg); border: 1px solid var(--rule);
    border-radius: 6px; padding: 1.25rem 1.5rem; box-shadow: 0 2px 16px rgb(0 0 0 / 0.08);
  }
  .card h2 { margin: 0.2rem 0 0.6rem; font: 600 1.6rem/1.2 var(--serif); }
  .intro h2 { font-size: 2rem; }
  .eyebrow { margin: 0; font: 600 0.75rem var(--mono); color: var(--accent); text-transform: uppercase; letter-spacing: 0.08em; }
  .lead { font: 1.1rem/1.5 var(--serif); }
  .warn { background: #f3e1df; padding: 0.5rem 0.7rem; border-radius: 4px; font-size: 0.9rem; }
  .small { font-size: 0.8rem; color: var(--muted); }
  .hint { font-weight: 600; color: var(--accent); }

  .tint {
    position: fixed; inset: 0; z-index: 1; pointer-events: none;
    background: var(--period-bg, transparent); mix-blend-mode: multiply;
    opacity: 0; transition: opacity 0.6s, background-color 0.8s;
  }
  .tint.on { opacity: 0.55; }

  .hud {
    position: fixed; left: clamp(1rem, 4vw, 3rem); bottom: 1.25rem; z-index: 5;
    background: var(--panel-bg); border: 1px solid var(--rule); border-radius: 6px;
    padding: 0.8rem 1rem; max-width: min(440px, calc(100vw - 2rem));
    transition: background-color 0.8s;
  }
  .hud p { margin: 0; }
  .period { font-size: 0.8rem; color: var(--period-ink, var(--muted)); font-weight: 600; }
  .now { font: 600 2rem/1.1 var(--serif); text-transform: capitalize; margin: 0.2rem 0 !important; }
  .count { font: 0.8rem var(--mono); color: var(--muted); }
  .steps { display: flex; gap: 0.4rem; margin-top: 0.5rem; flex-wrap: wrap; }
  .help { margin-top: 0.4rem !important; }

  .active {
    position: fixed; top: 3.4rem; right: 1rem; bottom: 1rem; z-index: 5; width: 310px;
    display: flex; flex-direction: column;
    background: var(--panel-bg); border: 1px solid var(--rule); border-radius: 6px; padding: 0.8rem;
    transition: background-color 0.8s;
  }
  .active-head { display: flex; justify-content: space-between; align-items: center; }
  .active h2 { margin: 0 0 0.4rem; font: 600 0.75rem var(--sans); text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
  .collapse { background: none; border: 0; font-size: 1.3rem; cursor: pointer; color: var(--muted); line-height: 1; }
  .expand { position: fixed; top: 3.6rem; right: 1rem; z-index: 5; background: var(--panel-bg); }
  .active-list { flex: 1; overflow-y: auto; min-height: 0; }
  .active ul { list-style: none; margin: 0; padding: 0; }
  .active li button {
    display: block; width: 100%; text-align: left; background: none; border: 0; border-bottom: 1px solid var(--rule);
    padding: 0.45rem 0.2rem; cursor: pointer; font: inherit; color: var(--ink);
  }
  .active li button:hover, .active li button.sel { background: rgb(255 255 255 / 0.6); }
  .place { display: block; font-weight: 600; }
  .list-toggle { display: none; }

  .legend { border-top: 1px solid var(--rule); padding-top: 0.5rem; margin-top: 0.5rem; font-size: 0.8rem; }
  .legend p { margin: 0.15rem 0; display: flex; align-items: center; gap: 0.5rem; }
  .sym { display: inline-block; width: 14px; height: 14px; border-radius: 50%; flex: none; }
  .s-high { background: #b3261e; border: 2px solid #fff; box-shadow: 0 0 0 1px #b3261e55; }
  .s-low { background: #b3261e80; border: 1px solid #b3261e; transform: scale(0.65); }
  .s-none { background: radial-gradient(#b3261e88, #b3261e00 70%); width: 18px; height: 18px; }
  .s-past { background: #6b5e57; opacity: 0.5; transform: scale(0.5); }

  .loading, .fatal { position: fixed; inset: 0; display: grid; place-items: center; margin: 0; }

  @media (max-width: 900px) {
    .top h1 { font-size: 0.85rem; }
    .list-toggle { display: inline-block; }
    .active { display: none; left: 1rem; right: 1rem; width: auto; top: auto; bottom: 11rem; max-height: 45vh; }
    .help { display: none; }
    .active.open { display: block; }
    .now { font-size: 1.5rem; }
  }
</style>
