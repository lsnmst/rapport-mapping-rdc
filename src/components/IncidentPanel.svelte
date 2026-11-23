<script lang="ts">
  import type { Actor, Incident, IncidentText, Lang, Vocab } from '../lib/types.ts';
  import { loadContext, loadTexts } from '../lib/data.ts';
  import { fmtIncidentDate, label, t } from '../lib/i18n.ts';

  interface Props {
    incident: Incident;
    lang: Lang;
    vocab: Vocab;
    actors: Record<string, Actor>;
    pdf: { url_fr: string; url_en: string };
    onclose: () => void;
  }
  let { incident, lang, vocab, actors, pdf, onclose }: Props = $props();

  let text = $state<IncidentText | null>(null);
  let context = $state<string | null>(null);
  let showContext = $state(false);
  let error = $state<string | null>(null);
  let closeBtn = $state<HTMLButtonElement>();

  $effect(() => {
    const id = incident.id;
    text = null; context = null; showContext = false; error = null;
    loadTexts().then((all) => { if (incident.id === id) text = all[id]; }).catch((e) => (error = String(e)));
    closeBtn?.focus();
  });

  async function toggleContext() {
    showContext = !showContext;
    if (showContext && context === null) {
      const all = await loadContext();
      const c = all[String(incident.para)];
      context = c ? (c[lang] ?? c.fr) : '';
    }
  }

  const actorName = (id: string) => actors[id]?.[lang] ?? id;
  const pdfUrl = $derived.by(() => {
    const page = text?.page?.[lang] ?? text?.page?.fr;
    const url = lang === 'fr' ? pdf.url_fr : pdf.url_en;
    return page ? `${url}#page=${page}` : url;
  });
  const paragraphText = $derived(text ? (text.text[lang] ?? text.text.fr) : '');

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') onclose();
  }
</script>

<svelte:window onkeydown={onKey} />

<aside class="panel" aria-labelledby="incident-title">
  <header>
    <div>
      <p class="kicker">{incident.id} · {t(lang, 'paragraph')} {incident.para}</p>
      <h2 id="incident-title">{incident.place}</h2>
      <p class="date">{fmtIncidentDate(lang, incident.start, incident.end, incident.dp)}</p>
    </div>
    <button bind:this={closeBtn} class="close" onclick={onclose} aria-label={t(lang, 'close')}>×</button>
  </header>

  <dl class="meta">
    <dt>{t(lang, 'province')}</dt>
    <dd>{incident.province}</dd>
    <dt>{t(lang, 'geoConfidence')}</dt>
    <dd><span class="conf conf-{incident.conf}">{label(vocab, 'confidence', incident.conf, lang)}</span>
      {#if incident.gp}<span class="muted"> · {label(vocab, 'geoPrecision', incident.gp, lang)}</span>{/if}</dd>
  </dl>

  {#if error}
    <p class="error">{error}</p>
  {:else if !text}
    <p class="muted">{t(lang, 'loading')}</p>
  {:else}
    {#if text.places.length > 1}
      <section>
        <h3>{t(lang, 'places')}</h3>
        <ul class="places">
          {#each text.places as p}
            <li>
              {p.n} <span class="muted">({label(vocab, 'placeRole', p.r, lang)})</span>
              {#if p.c}<span class="dot conf-{p.c}" title={label(vocab, 'confidence', p.c, lang)}></span>{/if}
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    {#each text.acts as act, k}
      <section class="act">
        {#if text.acts.length > 1}<p class="kicker">{k + 1} / {text.acts.length}</p>{/if}
        <h3>{t(lang, 'perpetrators')}</h3>
        <p>
          {#each act.actors as a, j}
            {j ? ', ' : ''}<strong>{actorName(a.id)}</strong>{#if a.role !== 'autore'}<span class="muted"> ({label(vocab, 'roles', a.role, lang)})</span>{/if}
          {/each}
          {#if act.certainty !== 'affermato'}<span class="tag">{label(vocab, 'certainty', act.certainty, lang)}</span>{/if}
        </p>
        <h3>{t(lang, 'victims')}</h3>
        <p>
          <span lang="fr">{act.victims}</span>
          {#if act.status.length || act.groups.length}
            <span class="muted">
              — {[...act.status.map((s) => label(vocab, 'victimStatus', s, lang)), ...act.groups.map((g) => label(vocab, 'victimGroups', g, lang))].join(', ')}
            </span>
          {/if}
        </p>
        <h3>{t(lang, 'violations')}</h3>
        <p>{act.viol.map((v) => label(vocab, 'violations', v, lang)).join(', ')}</p>
        {#if act.number}
          <h3>{t(lang, 'figures')}</h3>
          <p><q lang="fr">{act.number}</q> <span class="muted">({label(vocab, 'numberPrecision', act.np, lang)})</span></p>
        {/if}
      </section>
    {/each}

    <section>
      <h3>{t(lang, 'reportText')}</h3>
      <blockquote lang={text.text[lang] ? lang : 'fr'}>{paragraphText}</blockquote>
      <p><a href={pdfUrl} target="_blank" rel="noopener">{t(lang, 'openPdf')}</a></p>
    </section>

    <section>
      <button class="link" onclick={toggleContext} aria-expanded={showContext}>{t(lang, 'showContext')}</button>
      {#if showContext}
        <h3>{t(lang, 'context')}</h3>
        <p class="context">{context ?? t(lang, 'loading')}</p>
      {/if}
    </section>

    {#if text.sources[lang] ?? text.sources.fr}
      <details>
        <summary>{t(lang, 'sources')}</summary>
        <p class="sources">{text.sources[lang] ?? text.sources.fr}</p>
      </details>
    {/if}
  {/if}
</aside>

<style>
  .panel {
    position: fixed; top: 0; right: 0; bottom: 0; z-index: 20;
    width: min(440px, 100vw); overflow-y: auto;
    background: var(--paper); color: var(--ink);
    box-shadow: -4px 0 24px rgb(0 0 0 / 0.18);
    padding: 1.25rem 1.5rem 3rem;
  }
  header { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
  h2 { margin: 0.1rem 0; font: 600 1.5rem/1.2 var(--serif); }
  h3 { margin: 1rem 0 0.2rem; font: 600 0.75rem/1.2 var(--sans); text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
  p { margin: 0.2rem 0; line-height: 1.5; }
  .kicker { font: 0.75rem var(--mono); color: var(--muted); margin: 0; }
  .date { font-weight: 600; }
  .close { font-size: 1.8rem; line-height: 1; background: none; border: 0; cursor: pointer; color: var(--ink); padding: 0 0.25rem; }
  .meta { display: grid; grid-template-columns: auto 1fr; gap: 0.25rem 0.75rem; margin: 1rem 0 0; font-size: 0.9rem; }
  .meta dt { color: var(--muted); }
  .meta dd { margin: 0; }
  .act { border-top: 1px solid var(--rule); margin-top: 1rem; }
  blockquote { margin: 0.4rem 0; padding-left: 0.9rem; border-left: 3px solid var(--rule); font: 1rem/1.6 var(--serif); }
  .context, .sources { font-size: 0.85rem; color: var(--muted); white-space: pre-line; }
  .muted { color: var(--muted); }
  .tag { margin-left: 0.4rem; font-size: 0.75rem; padding: 0.1rem 0.4rem; border-radius: 3px; background: var(--rule); }
  .places { margin: 0; padding-left: 1.1rem; }
  .conf { padding: 0.05rem 0.4rem; border-radius: 3px; font-size: 0.85rem; }
  .conf-high { background: #e6efe6; }
  .conf-low { background: #fbf1d6; }
  .conf-none { background: #f3e1df; }
  .dot { display: inline-block; width: 0.6rem; height: 0.6rem; border-radius: 50%; margin-left: 0.3rem; }
  .dot.conf-high { background: #2f7d32; } .dot.conf-low { background: #c99a06; } .dot.conf-none { background: #b3261e; }
  .link { background: none; border: 0; padding: 0; color: var(--accent); cursor: pointer; text-decoration: underline; font: inherit; margin-top: 1rem; }
  .error { color: #b3261e; }
  a { color: var(--accent); }
</style>
