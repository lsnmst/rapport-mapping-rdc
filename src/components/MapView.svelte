<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import maplibregl from "maplibre-gl";
  import "maplibre-gl/dist/maplibre-gl.css";
  import type { Incident, Lang, Padding, Point } from "../lib/types.ts";
  import { DAY, toMs } from "../lib/timeline.ts";
  import { t } from "../lib/i18n.ts";
  import { PERIOD_COLORS } from "../lib/periods.ts";

  interface Props {
    incidents: Incident[]; // incidenti filtrati
    now: number; // istante corrente (ms)
    overview: boolean; // apertura: tutti gli incidenti, piccoli, senza filtro temporale
    selected: string | null;
    lang: Lang;
    styleUrl: string;
    padding: Padding; // spazio occupato dai pannelli: la RDC resta nell'area libera
    onselect: (id: string) => void;
    onaway: () => void; // la mappa è stata ingrandita rispetto alla vista d'insieme
    onbackground: () => void; // clic su un punto vuoto della mappa
  }
  let {
    incidents,
    now,
    overview,
    selected,
    lang,
    styleUrl,
    padding,
    onselect,
    onaway,
    onbackground,
  }: Props = $props();

  const AFTER_DAYS = 30; // per quanto un incidente resta "in corso" dopo la fine
  const DRC_BOUNDS: [[number, number], [number, number]] = [
    [12.2, -13.5],
    [31.3, 5.4],
  ];
  const COLOR_ACTIVE = "#b3261e";
  const COLOR_PAST = "#6b5e57";
  const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

  let container: HTMLDivElement;
  let map: maplibregl.Map | null = null;
  let ready = $state(false);
  let popup: maplibregl.Popup | null = null;
  let baseZoom = 0; // zoom della vista d'insieme
  let away = false;

  function overviewZoom(): number {
    return map?.cameraForBounds(DRC_BOUNDS, { padding })?.zoom ?? 0;
  }

  // Un punto per ogni luogo di evento/origine/destinazione; per gli incidenti senza punti, il centro dell'area.
  function toGeoJSON(list: Incident[]): GeoJSON.FeatureCollection {
    const features: GeoJSON.Feature[] = [];
    for (const i of list) {
      const t0d = Math.floor(toMs(i.start) / DAY);
      const t1d = Math.floor(toMs(i.end) / DAY);
      const pts: Point[] = i.points.length
        ? i.points
        : [
            {
              n: i.place,
              r: "evento",
              lat: i.lat,
              lon: i.lon,
              c: i.conf,
              p: i.gp,
              main: true,
            },
          ];
      for (const p of pts) {
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [p.lon, p.lat] },
          properties: {
            id: i.id,
            name: p.n,
            role: p.r,
            conf: p.c,
            main: p.main ? 1 : 0,
            period: i.period,
            t0d,
            t1d,
          },
        });
      }
    }
    return { type: "FeatureCollection", features };
  }

  type Expr = maplibregl.ExpressionSpecification;
  const byConf = (conf: "high" | "low" | "none"): Expr => [
    "==",
    ["get", "conf"],
    conf,
  ];
  const periodColor: Expr = [
    "match",
    ["get", "period"],
    1,
    PERIOD_COLORS[1].ink,
    2,
    PERIOD_COLORS[2].ink,
    3,
    PERIOD_COLORS[3].ink,
    PERIOD_COLORS[4].ink,
  ];

  const RENAME = toMs("1997-05-17"); // Zaïre → République démocratique du Congo
  const countryName = (): string =>
    now < RENAME
      ? lang === "fr"
        ? "Zaïre"
        : "Zaire"
      : lang === "fr"
        ? "République démocratique du Congo"
        : "Democratic Republic of the Congo";

  /**
   * Simboli:
   *  high  punto pieno, il più evidente (bordo bianco)
   *  low   punto più piccolo e semitrasparente, senza bordo bianco: visibile ma meno affermativo
   *  none  area sfumata (solo il territorio o la provincia sono noti)
   */
  function applyStyle() {
    if (!map || !ready) return;
    const m = map;
    if (overview) {
      for (const id of ["area", "low", "high"])
        m.setFilter(
          id,
          byConf(id === "area" ? "none" : (id as "high" | "low")),
        );
      m.setPaintProperty("high", "circle-color", periodColor);
      m.setPaintProperty("high", "circle-opacity", 0.85);
      m.setPaintProperty("high", "circle-radius", 2.6);
      m.setPaintProperty("high", "circle-stroke-width", 0.5);
      m.setPaintProperty("low", "circle-color", periodColor);
      m.setPaintProperty("low", "circle-opacity", 0.45);
      m.setPaintProperty("low", "circle-radius", 2);
      m.setPaintProperty("low", "circle-stroke-opacity", 0);
      m.setPaintProperty("area", "circle-color", periodColor);
      m.setPaintProperty("area", "circle-opacity", 0.12);
      m.setPaintProperty("area", "circle-radius", [
        "interpolate",
        ["exponential", 2],
        ["zoom"],
        4,
        6,
        8,
        90,
      ]);
      return;
    }
    const nowD = Math.floor(now / DAY);
    const started: maplibregl.FilterSpecification = [
      "<=",
      ["get", "t0d"],
      nowD,
    ];
    const isPast: Expr = [">", nowD, ["+", ["get", "t1d"], AFTER_DAYS]];
    const color: Expr = ["case", isPast, COLOR_PAST, COLOR_ACTIVE];
    const op = (a: number, p: number): Expr => ["case", isPast, p, a];
    m.setFilter("area", [
      "all",
      byConf("none"),
      started,
    ] as maplibregl.FilterSpecification);
    m.setFilter("low", [
      "all",
      byConf("low"),
      started,
    ] as maplibregl.FilterSpecification);
    m.setFilter("high", [
      "all",
      byConf("high"),
      started,
    ] as maplibregl.FilterSpecification);
    m.setPaintProperty("area", "circle-color", color);
    m.setPaintProperty("area", "circle-opacity", op(0.26, 0.06));
    m.setPaintProperty("area", "circle-radius", [
      "interpolate",
      ["exponential", 2],
      ["zoom"],
      4,
      12,
      8,
      190,
    ]);
    m.setPaintProperty("high", "circle-color", color);
    m.setPaintProperty("high", "circle-opacity", op(1, 0.4));
    m.setPaintProperty("high", "circle-radius", [
      "case",
      isPast,
      3,
      ["case", ["==", ["get", "main"], 1], 6.5, 5],
    ] as Expr);
    m.setPaintProperty("high", "circle-stroke-width", [
      "case",
      isPast,
      0.5,
      1.5,
    ] as Expr);
    m.setPaintProperty("low", "circle-color", color);
    m.setPaintProperty("low", "circle-opacity", op(0.5, 0.25));
    m.setPaintProperty("low", "circle-radius", [
      "case",
      isPast,
      2.5,
      4,
    ] as Expr);
    m.setPaintProperty("low", "circle-stroke-opacity", op(0.9, 0.3));
  }

  function applyData() {
    if (!map || !ready) return;
    (map.getSource("incidents") as maplibregl.GeoJSONSource).setData(
      toGeoJSON(incidents),
    );
    applyStyle();
  }

  function applySelected() {
    if (!map || !ready) return;
    map.setFilter("selected", ["==", ["get", "id"], selected ?? ""]);
  }

  /** Torna alla vista d'insieme della RDC. */
  export function resetView(animate = true) {
    if (!map) return;
    away = false;
    baseZoom = overviewZoom();
    map.fitBounds(DRC_BOUNDS, {
      padding,
      duration: animate && !reduced() ? 700 : 0,
    });
  }

  /** Centra la mappa su un incidente, lasciando libero lo spazio della scheda a destra. */
  export function focus(i: Incident, extraRight = 0) {
    if (!map) return;
    const pts = i.points.length ? i.points : [{ lat: i.lat, lon: i.lon }];
    const b = new maplibregl.LngLatBounds();
    for (const p of pts) b.extend([p.lon, p.lat]);
    map.fitBounds(b, {
      padding: { ...padding, right: padding.right + extraRight },
      maxZoom: i.conf === "none" ? 6.5 : 8.5,
      duration: reduced() ? 0 : 800,
    });
  }

  /** Ingrandisce sull'insieme degli incidenti indicati (es. quelli in corso nel mese corrente). */
  export function zoomTo(list: Incident[]) {
    if (!map || !list.length) return;
    const b = new maplibregl.LngLatBounds();
    for (const i of list)
      for (const p of i.points.length ? i.points : [i])
        b.extend([p.lon, p.lat]);
    map.fitBounds(b, { padding, maxZoom: 8, duration: reduced() ? 0 : 800 });
  }

  onMount(() => {
    const touch = matchMedia("(pointer: coarse)").matches;
    map = new maplibregl.Map({
      container,
      style: styleUrl,
      bounds: DRC_BOUNDS,
      fitBoundsOptions: { padding },
      // Touch: un dito fa scorrere la pagina (il tempo), due dita muovono la mappa.
      // Desktop: la rotella fa scorrere la pagina; doppio clic, +/− o Ctrl/⌘ + rotella fanno lo zoom.
      cooperativeGestures: touch,
      scrollZoom: touch,
      doubleClickZoom: true,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    });
    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      "bottom-right",
    );
    map.touchZoomRotate.disableRotation();
    if (!touch) {
      container.addEventListener(
        "wheel",
        (e) => {
          if (!(e.ctrlKey || e.metaKey) || !map) return;
          e.preventDefault();
          const rect = container.getBoundingClientRect();
          const around = map.unproject([
            e.clientX - rect.left,
            e.clientY - rect.top,
          ]);
          map.easeTo({
            zoom: map.getZoom() - e.deltaY * 0.004,
            around,
            duration: 0,
          });
        },
        { passive: false },
      );
    }
    // Ogni ingrandimento rispetto alla vista d'insieme viene segnalato: lo scroll successivo riporta indietro.
    map.on("moveend", () => {
      if (!map) return;
      if (!away && map.getZoom() > baseZoom + 0.35) {
        away = true;
        onaway();
      }
    });

    map.on("load", () => {
      const m = map!;
      // Le 11 province del periodo 1993–2003 (prima del découpage del 2015), linee sottili
      m.addSource("provinces", {
        type: "geojson",
        data: `${import.meta.env.BASE_URL}data/provinces_1993.geojson`,
      });
      m.addLayer({
        id: "provinces",
        type: "line",
        source: "provinces",
        paint: {
          "line-color": "#AC6767",
          "line-opacity": 0.3,
          "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.4, 8, 1],
        },
      });
      // Nasconde i confini provinciali attuali (26 province) della mappa di base, che sarebbero anacronistici
      for (const l of m.getStyle().layers ?? [])
        if (l.id.startsWith("boundary_state"))
          m.setLayoutProperty(l.id, "visibility", "none");
      baseZoom = overviewZoom();
      m.addSource("incidents", { type: "geojson", data: toGeoJSON([]) });
      m.addSource("country", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              geometry: { type: "Point", coordinates: [23.6, -3.2] },
              properties: {},
            },
          ],
        },
      });
      m.addLayer({
        id: "country-name",
        type: "symbol",
        source: "country",
        layout: {
          "text-field": countryName(),
          "text-font": ["Noto Sans Italic"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 13, 7, 20],
          "text-transform": "uppercase",
          "text-letter-spacing": 0.35,
          "text-max-width": 12,
          "text-allow-overlap": true,
        },
        paint: {
          "text-color": "#6b5e57",
          "text-opacity": 0.55,
          "text-halo-color": "#ffffff",
          "text-halo-width": 1,
        },
      });
      // La mappa di base scrive già il nome attuale del paese: lo togliamo solo per la RDC
      for (const l of m.getStyle().layers ?? [])
        if (l.type === "symbol" && l.id.includes("country"))
          m.setFilter(l.id, [
            "all",
            ...(l.filter ? [l.filter] : []),
            ["!=", ["get", "iso_a2"], "CD"],
          ] as maplibregl.FilterSpecification);
      m.addLayer({
        id: "area",
        type: "circle",
        source: "incidents",
        paint: { "circle-blur": 1, "circle-color": COLOR_ACTIVE },
      });
      m.addLayer({
        id: "low",
        type: "circle",
        source: "incidents",
        paint: {
          "circle-stroke-width": 1,
          "circle-stroke-color": COLOR_ACTIVE,
        },
      });
      m.addLayer({
        id: "high",
        type: "circle",
        source: "incidents",
        paint: { "circle-stroke-color": "#ffffff" },
      });
      m.addLayer({
        id: "selected",
        type: "circle",
        source: "incidents",
        filter: ["==", ["get", "id"], ""],
        paint: {
          "circle-radius": 11,
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-width": 3,
          "circle-stroke-color": "#111",
        },
      });

      for (const layer of ["high", "low", "area"]) {
        m.on("mouseenter", layer, (e) => {
          m.getCanvas().style.cursor = "pointer";
          const f = e.features?.[0];
          if (!f) return;
          popup?.remove();
          popup = new maplibregl.Popup({
            closeButton: false,
            closeOnClick: false,
            offset: 8,
          })
            .setLngLat(e.lngLat)
            .setText(`${f.properties!.name} | ${f.properties!.id}`)
            .addTo(m);
        });
        m.on("mouseleave", layer, () => {
          m.getCanvas().style.cursor = "";
          popup?.remove();
          popup = null;
        });
      }
      m.on("click", (e) => {
        const hit = m.queryRenderedFeatures(e.point, {
          layers: ["high", "low", "area"],
        });
        if (hit.length) onselect(String(hit[0].properties!.id));
        else onbackground();
      });
      ready = true;
      applyData();
      applySelected();
    });
  });

  onDestroy(() => map?.remove());

  let shownName = "";
  $effect(() => {
    void now;
    void lang;
    if (!map || !ready) return;
    const n = countryName();
    if (n !== shownName) {
      map.setLayoutProperty("country-name", "text-field", n);
      shownName = n;
    }
  });

  $effect(() => {
    void incidents;
    applyData();
  });
  $effect(() => {
    void now;
    void overview;
    applyStyle();
  });
  $effect(() => {
    void selected;
    applySelected();
  });
  // i pannelli cambiano dimensione (apertura, ridimensionamento): si ricalcola la vista d'insieme
  $effect(() => {
    void padding.left;
    void padding.right;
    void padding.top;
    void padding.bottom;
    if (ready && !away) resetView();
  });
</script>

<div
  class="map"
  bind:this={container}
  role="region"
  aria-label={t(lang, "mapLabel")}
></div>

<style>
  .map {
    position: fixed;
    inset: 0;
    z-index: 0;
  }
</style>
