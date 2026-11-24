<script lang="ts">
  import type {
    Act,
    Actor,
    Incident,
    IncidentText,
    Lang,
    Vocab,
  } from "../lib/types.ts";
  import { loadContext, loadTexts } from "../lib/data.ts";
  import { cap, fmtIncidentDate, label, t } from "../lib/i18n.ts";

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
  let contextAll = $state<{ fr: string | null; en: string | null } | null>(
    null,
  );
  let showContext = $state(false);
  let error = $state<string | null>(null);
  let closeBtn = $state<HTMLButtonElement>();

  $effect(() => {
    const id = incident.id;
    text = null;
    text = null;
    contextAll = null;
    error = null;
    loadTexts()
      .then((all) => {
        if (incident.id === id) text = all[id];
      })
      .catch((e) => (error = String(e)));
    loadContext().then((all) => {
      if (incident.id === id)
        contextAll = all[String(incident.para)] ?? { fr: "", en: "" };
    });
  });

  const contextText = $derived(
    contextAll ? (contextAll[lang] ?? contextAll.fr ?? "") : null,
  );
  const POS = { high: "posHigh", low: "posLow", none: "posNone" } as const;

  const actorName = (id: string) => actors[id]?.[lang] ?? id;
  const pdfUrl = $derived.by(() => {
    const page = text?.page?.[lang] ?? text?.page?.fr;
    const url = lang === "fr" ? pdf.url_fr : pdf.url_en;
    return page ? `${url}#page=${page}` : url;
  });
  const paragraphText = $derived(text ? (text.text[lang] ?? text.text.fr) : "");

  /** Condizione e categorie delle vittime, senza ripetere quello che il testo del rapporto dice già. */
  function victimDetails(act: Act): string[] {
    const said = act.victims.toLowerCase();
    return [
      ...act.status.map((s) => label(vocab, "victimStatus", s, lang)),
      ...act.groups.map((g) => label(vocab, "victimGroups", g, lang)),
    ].filter(
      (x, k, all) =>
        x && all.indexOf(x) === k && !said.includes(x.toLowerCase()),
    );
  }

  function onKey(e: KeyboardEvent) {
    if (e.key === "Escape") onclose();
  }
</script>

<svelte:window onkeydown={onKey} />

<aside class="panel" aria-labelledby="incident-title">
  <header>
    <div>
      <p class="kicker">
        {incident.id} | {t(lang, "paragraph")}
        {incident.para}
      </p>
      <h2 id="incident-title">{cap(incident.place)}</h2>
      <p class="date">
        {cap(fmtIncidentDate(lang, incident.start, incident.end, incident.dp))}
      </p>
    </div>
    <button
      bind:this={closeBtn}
      class="close"
      onclick={onclose}
      aria-label={t(lang, "close")}>×</button
    >
  </header>

  <dl class="meta">
    <dt>{t(lang, "province")}</dt>
    <dd>{incident.province}</dd>
    <dt>
      {t(
        lang,
        incident.points.length > 1 ? "geoConfidenceMain" : "geoConfidence",
      )}
    </dt>
    <dd class="conf-line">
      <span class="sym s-{incident.conf}" aria-hidden="true"></span>{label(
        vocab,
        "confidence",
        incident.conf,
        lang,
      )}
      {#if incident.gp}<span class="muted">
          | {label(vocab, "geoPrecision", incident.gp, lang)}</span
        >{/if}
    </dd>
  </dl>

  {#if error}
    <p class="error">{error}</p>
  {:else if !text}
    <p class="muted">{t(lang, "loading")}</p>
  {:else}
    {#if text.places.length > 1}
      <section>
        <h3>{t(lang, "places")}</h3>
        <ul class="places">
          {#each text.places as p}
            <li>
              <span
                class="sym s-{p.c ?? 'none'}"
                role="img"
                aria-label={t(lang, POS[p.c ?? "none"])}
                title={t(lang, POS[p.c ?? "none"])}
              ></span>
              <span
                >{cap(p.n)}
                <span class="muted"
                  >({label(vocab, "placeRole", p.r, lang)})</span
                ></span
              >
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    {#each text.acts as act, k}
      <section class="act">
        {#if text.acts.length > 1}<p class="kicker">
            {k + 1} / {text.acts.length}
          </p>{/if}
        <h3>{t(lang, "perpetrators")}</h3>
        <p>
          {#each act.actors as a, j}
            {j ? ", " : ""}<strong>{actorName(a.id)}</strong
            >{#if a.role !== "autore"}<span class="muted">
                ({label(vocab, "roles", a.role, lang)})</span
              >{/if}
          {/each}
          {#if act.certainty !== "affermato"}<span class="tag"
              >{label(vocab, "certainty", act.certainty, lang)}</span
            >{/if}
        </p>
        <h3>{t(lang, "victims")}</h3>
        <p>
          <span lang="fr">{cap(act.victims)}</span>
          {#if victimDetails(act).length}
            <span class="muted">({victimDetails(act).join(", ")})</span>
          {/if}
        </p>
        <h3>{t(lang, "violations")}</h3>
        <p>
          {cap(
            act.viol.map((v) => label(vocab, "violations", v, lang)).join(", "),
          )}
        </p>
      </section>
    {/each}

    <section>
      <h3>{t(lang, "reportText")}</h3>
      <blockquote lang={text.text[lang] ? lang : "fr"}>
        {paragraphText}
      </blockquote>
      <p>
        <a href={pdfUrl} target="_blank" rel="noopener">{t(lang, "openPdf")}</a>
      </p>
    </section>

    <section>
      <h3>{t(lang, "context")}</h3>
      <p class="context">{contextText ?? t(lang, "loading")}</p>
    </section>

    {#if text.sources[lang] ?? text.sources.fr}
      <section>
        <h3>{t(lang, "sources")}</h3>
        <p class="sources">{text.sources[lang] ?? text.sources.fr}</p>
      </section>
    {/if}
  {/if}
</aside>

<style>
  .panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 20;
    width: min(440px, 100vw);
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--paper);
    color: var(--ink);
    box-shadow: -4px 0 24px rgb(0 0 0 / 0.18);
    padding: 1.25rem 1.5rem 3rem;
  }
  header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
  }
  h2 {
    margin: 0.1rem 0;
    font: 600 1.5rem/1.2 var(--serif);
  }
  h3 {
    margin: 1rem 0 0.2rem;
    font: 600 0.75rem/1.2 var(--sans);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
  }
  p {
    margin: 0.2rem 0;
    line-height: 1.5;
  }
  .kicker {
    font: 0.75rem var(--mono);
    color: var(--muted);
    margin: 0;
    margin-top: 0.5rem;
  }
  .date {
    font-weight: 600;
  }
  .close {
    font-size: 1.8rem;
    line-height: 1;
    background: none;
    border: 0;
    cursor: pointer;
    color: var(--ink);
    padding: 0 0.25rem;
  }
  .meta {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.25rem 0.75rem;
    margin: 1rem 0 0;
    font-size: 0.9rem;
  }
  .meta dt {
    color: var(--muted);
  }
  .meta dd {
    margin: 0;
  }
  .act {
    border-top: 1px solid var(--rule);
    margin-top: 1rem;
  }
  blockquote {
    margin: 0.4rem 0;
    padding-left: 0.9rem;
    border-left: 3px solid var(--rule);
    font: 0.9rem/1.6 var(--quote);
    line-height: 1.2rem;
  }
  .context,
  .sources {
    font-size: 0.85rem;
    color: var(--muted);
    white-space: pre-line;
  }
  .muted {
    color: var(--muted);
  }
  .tag {
    margin-left: 0.4rem;
    font-size: 0.75rem;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    background: var(--rule);
  }
  .places {
    margin: 0;
    padding-left: 1.1rem;
  }
  .conf {
    padding: 0.05rem 0.4rem;
    border-radius: 3px;
    font-size: 0.85rem;
  }
  .conf-high {
    background: #e6efe6;
  }
  .conf-low {
    background: #fbf1d6;
  }
  .conf-none {
    background: #f3e1df;
  }
  .places li {
    margin: 0.15rem 0;
  }
  .places .conf {
    font-size: 0.75rem;
    margin-left: 0.3rem;
    white-space: nowrap;
  }
  .error {
    color: #b3261e;
  }
  a {
    color: var(--accent);
  }
  .places {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .places li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.2rem 0;
  }
  .conf-line {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  /* stessi simboli della legenda della mappa */
  .sym {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex: none;
  }
  .s-high {
    background: #b3261e;
    border: 2px solid #fff;
    box-shadow: 0 0 0 1px #b3261e55;
  }
  .s-low {
    background: #b3261e80;
    border: 1px solid #b3261e;
    transform: scale(0.65);
  }
  .s-none {
    background: radial-gradient(#b3261e88, #b3261e00 70%);
    width: 18px;
    height: 18px;
    margin: -2px;
  }
  #incident-title {
    margin-top: 0.6rem;
  }
</style>
