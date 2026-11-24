import type { Action } from 'svelte/action';

interface Params {
  handle: string;                       // selettore della maniglia dentro il pannello
  enabled: boolean;                     // solo desktop
  onmove?: (moved: boolean) => void;    // true = spostato dall'utente, false = tornato al posto originale
}

/**
 * Rende un pannello `position: fixed` trascinabile dalla sua maniglia.
 * Doppio clic sulla maniglia: il pannello torna alla posizione iniziale.
 */
export const draggable: Action<HTMLElement, Params> = (node, params) => {
  let p = params;
  let dragging = false;
  let startX = 0, startY = 0, origX = 0, origY = 0;

  const handle = () => node.querySelector<HTMLElement>(p.handle);
  const onHandle = (e: Event) => !!handle()?.contains(e.target as Node)
    && !(e.target as HTMLElement).closest('button, a, input');

  function reset() {
    for (const k of ['left', 'top', 'right', 'bottom', 'height']) node.style.removeProperty(k);
    p.onmove?.(false);
  }

  function down(e: PointerEvent) {
    if (!p.enabled || e.button !== 0 || !onHandle(e)) return;
    const r = node.getBoundingClientRect();
    startX = e.clientX; startY = e.clientY; origX = r.left; origY = r.top;
    node.style.height = `${r.height}px`;   // l'altezza resta quella di partenza anche senza top/bottom
    dragging = true;
    node.setPointerCapture(e.pointerId);
    e.preventDefault();
  }

  function move(e: PointerEvent) {
    if (!dragging) return;
    const r = node.getBoundingClientRect();
    const x = Math.min(Math.max(0, origX + e.clientX - startX), innerWidth - r.width);
    const y = Math.min(Math.max(48, origY + e.clientY - startY), innerHeight - 48);
    Object.assign(node.style, { left: `${x}px`, top: `${y}px`, right: 'auto', bottom: 'auto' });
    p.onmove?.(true);
  }

  function up(e: PointerEvent) {
    if (!dragging) return;
    dragging = false;
    node.releasePointerCapture(e.pointerId);
  }

  function dbl(e: MouseEvent) {
    if (p.enabled && onHandle(e)) reset();
  }

  node.addEventListener('pointerdown', down);
  node.addEventListener('pointermove', move);
  node.addEventListener('pointerup', up);
  node.addEventListener('pointercancel', up);
  node.addEventListener('dblclick', dbl);

  return {
    update(next) {
      if (p.enabled && !next.enabled) reset();   // passaggio a layout mobile: posizione originale
      p = next;
    },
    destroy() {
      node.removeEventListener('pointerdown', down);
      node.removeEventListener('pointermove', move);
      node.removeEventListener('pointerup', up);
      node.removeEventListener('pointercancel', up);
      node.removeEventListener('dblclick', dbl);
    },
  };
};