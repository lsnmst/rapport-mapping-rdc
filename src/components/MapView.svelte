<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import type { Incident, Lang, Point } from '../lib/types.ts';
  import { DAY, toMs } from '../lib/timeline.ts';
  import { t } from '../lib/i18n.ts';

  interface Props {
    incidents: Incident[];          // incidenti filtrati
    now: number;                    // istante corrente (ms)
    selected: string | null;
    lang: Lang;
    styleUrl: string;
    onselect: (id: string) => void;
  }
  let { incidents, now, selected, lang, styleUrl, onselect }: Props = $props();

  const AFTER_DAYS = 30;            // per quanto un incidente resta "in corso" dopo la fine
  const DRC_BOUNDS: [[number, number], [number, number]] = [[12.0, -13.6], [31.5, 5.5]];
  const COLOR_ACTIVE = '#b3261e';
  const COLOR_PAST = '#6b5e57';

  let container: HTMLDivElement;
  let map: maplibregl.Map | null = null;
  let ready = $state(false);
  let popup: maplibregl.Popup | null = null;

  // Un punto per ogni luogo di evento/origine/destinazione; per gli incidenti senza punti, il centro dell'area.
  function toGeoJSON(list: Incident[]): GeoJSON.FeatureCollection {
    const features: GeoJSON.Feature[] = [];
    for (const i of list) {
      const t0d = Math.floor(toMs(i.start) / DAY);
      const t1d = Math.floor(toMs(i.end) / DAY);
      const pts: Point[] = i.points.length ? i.points : [{ n: i.place, r: 'evento', lat: i.lat, lon: i.lon, c: i.conf, p: i.gp, main: true }];
      for (const p of pts) {
        features.push({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
          properties: { id: i.id, name: p.n, role: p.r, conf: p.c, main: p.main ? 1 : 0, t0d, t1d },
        });
      }
    }
    return { type: 'FeatureCollection', features };
  }

  // Espressioni che dipendono dal tempo: aggiornate a ogni cambio di `now`.
  function timeExpressions(nowD: number) {
    const isPast: maplibregl.ExpressionSpecification = ['>', nowD, ['+', ['get', 't1d'], AFTER_DAYS]];
    return {
      filter: ['<=', ['get', 't0d'], nowD] as maplibregl.FilterSpecification,
      color: ['case', isPast, COLOR_PAST, COLOR_ACTIVE] as maplibregl.ExpressionSpecification,
      opacity: (active: number, past: number) =>
        ['case', isPast, past, active] as maplibregl.ExpressionSpecification,
    };
  }

  function applyTime() {
    if (!map || !ready) return;
    const nowD = Math.floor(now / DAY);
    const e = timeExpressions(nowD);
    const f = (conf: maplibregl.ExpressionSpecification) => ['all', conf, e.filter] as maplibregl.FilterSpecification;
    map.setFilter('area', f(['==', ['get', 'conf'], 'none']));
    map.setFilter('halo', f(['==', ['get', 'conf'], 'low']));
    map.setFilter('dot', f(['!=', ['get', 'conf'], 'none']));
    map.setPaintProperty('area', 'circle-color', e.color);
    map.setPaintProperty('area', 'circle-opacity', e.opacity(0.28, 0.08));
    map.setPaintProperty('halo', 'circle-stroke-color', e.color);
    map.setPaintProperty('halo', 'circle-stroke-opacity', e.opacity(0.7, 0.15));
    map.setPaintProperty('dot', 'circle-color', e.color);
    map.setPaintProperty('dot', 'circle-opacity', e.opacity(0.95, 0.35));
    map.setPaintProperty('dot', 'circle-radius', ['case', ['>', nowD, ['+', ['get', 't1d'], AFTER_DAYS]], 3,
      ['case', ['==', ['get', 'main'], 1], 6, 4.5]] as maplibregl.ExpressionSpecification);
  }

  function applyData() {
    if (!map || !ready) return;
    (map.getSource('incidents') as maplibregl.GeoJSONSource).setData(toGeoJSON(incidents));
    applyTime();
  }

  function applySelected() {
    if (!map || !ready) return;
    map.setFilter('selected', ['==', ['get', 'id'], selected ?? '']);
  }

  onMount(() => {
    const touch = matchMedia('(pointer: coarse)').matches;
    map = new maplibregl.Map({
      container,
      style: styleUrl,
      bounds: DRC_BOUNDS,
      fitBoundsOptions: { padding: 40 },
      // Touch: un dito fa scorrere la pagina (il tempo), due dita muovono la mappa.
      // Desktop: la rotella fa scorrere la pagina; Ctrl/⌘ + rotella fa lo zoom (gestito sotto).
      cooperativeGestures: touch,
      scrollZoom: touch,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.touchZoomRotate.disableRotation();
    if (!touch) {
      container.addEventListener('wheel', (e) => {
        if (!(e.ctrlKey || e.metaKey) || !map) return;
        e.preventDefault();
        const rect = container.getBoundingClientRect();
        const around = map.unproject([e.clientX - rect.left, e.clientY - rect.top]);
        map.easeTo({ zoom: map.getZoom() - e.deltaY * 0.004, around, duration: 0 });
      }, { passive: false });
    }

    map.on('load', () => {
      const m = map!;
      m.addSource('incidents', { type: 'geojson', data: toGeoJSON([]) });
      // confidenza "none": solo un'area sfumata attorno al centro del territorio o della provincia
      m.addLayer({
        id: 'area', type: 'circle', source: 'incidents',
        paint: {
          // ~50-70 km di raggio: ordine di grandezza di un territoire
          'circle-radius': ['interpolate', ['exponential', 2], ['zoom'], 4, 12, 8, 190],
          'circle-blur': 1,
          'circle-color': COLOR_ACTIVE,
          'circle-opacity': 0.25,
        },
      });
      // confidenza "low": anello di incertezza attorno al punto
      m.addLayer({
        id: 'halo', type: 'circle', source: 'incidents',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 9, 9, 22],
          'circle-color': 'rgba(0,0,0,0)',
          'circle-stroke-width': 1.5,
          'circle-stroke-color': COLOR_ACTIVE,
          'circle-stroke-opacity': 0.6,
        },
      });
      // tutti i punti con posizione (high e low)
      m.addLayer({
        id: 'dot', type: 'circle', source: 'incidents',
        paint: {
          'circle-radius': 5,
          'circle-color': COLOR_ACTIVE,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#ffffff',
        },
      });
      m.addLayer({
        id: 'selected', type: 'circle', source: 'incidents', filter: ['==', ['get', 'id'], ''],
        paint: { 'circle-radius': 11, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-width': 3, 'circle-stroke-color': '#111' },
      });

      for (const layer of ['dot', 'area']) {
        m.on('click', layer, (e) => {
          const f = e.features?.[0];
          if (f) onselect(String(f.properties!.id));
        });
        m.on('mouseenter', layer, (e) => {
          m.getCanvas().style.cursor = 'pointer';
          const f = e.features?.[0];
          if (!f) return;
          popup?.remove();
          popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 })
            .setLngLat(e.lngLat)
            .setText(`${f.properties!.name} · ${f.properties!.id}`)
            .addTo(m);
        });
        m.on('mouseleave', layer, () => {
          m.getCanvas().style.cursor = '';
          popup?.remove();
          popup = null;
        });
      }
      ready = true;
      applyData();
      applySelected();
    });
  });

  onDestroy(() => map?.remove());

  $effect(() => { void incidents; applyData(); });
  $effect(() => { void now; applyTime(); });
  $effect(() => { void selected; applySelected(); });

  /** Centra la mappa su un incidente (chiamato dal genitore quando si apre una scheda). */
  export function focus(i: Incident) {
    if (!map) return;
    const z = i.conf === 'none' ? 6 : 8;
    map.easeTo({ center: [i.lon, i.lat], zoom: Math.max(map.getZoom(), z), duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 800 });
  }
</script>

<div class="map" bind:this={container} role="region" aria-label={t(lang, 'mapLabel')}></div>

<style>
  .map {
    position: fixed;
    inset: 0;
    z-index: 0;
  }
</style>
