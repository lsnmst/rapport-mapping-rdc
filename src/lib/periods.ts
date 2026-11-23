/**
 * Colori dei quattro periodi del rapporto.
 * bg:  pastello per la velatura della mappa e lo sfondo dei pannelli
 * ink: tono più scuro dello stesso colore, per i punti della vista d'insieme e i dettagli
 */
export const PERIOD_COLORS: Record<1 | 2 | 3 | 4, { bg: string; ink: string }> = {
  1: { bg: '#f4e6c8', ink: '#9a6b1f' },   // sabbia
  2: { bg: '#f5d6cf', ink: '#a8432f' },   // rosa
  3: { bg: '#d8e4f1', ink: '#3b6894' },   // azzurro
  4: { bg: '#dbeadb', ink: '#4a7f46' },   // verde salvia
};
