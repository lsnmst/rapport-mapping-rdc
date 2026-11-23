export type Lang = 'fr' | 'en';
export type Confidence = 'high' | 'low' | 'none';
export type Bi = { fr: string; en: string };

export interface Point {
  n: string;            // nome del luogo
  r: 'evento' | 'origine' | 'destinazione';
  lat: number;
  lon: number;
  c: Confidence;
  p: string | null;     // precisione geografica
  main: boolean;
}

export interface Incident {
  id: string;
  period: 1 | 2 | 3 | 4;
  start: string;        // ISO yyyy-mm-dd
  end: string;
  dp: string;           // precisione della data
  province: string;
  scope: string;
  place: string;
  lat: number;
  lon: number;
  conf: Confidence;
  gp: string | null;
  points: Point[];
  actors: string[];
  cats: string[];
  para: number;
}

export interface Act {
  actors: { id: string; role: string }[];
  victims: string;
  status: string[];
  groups: string[];
  viol: string[];
  certainty: string;
  number: string | null;
  np: string | null;
}

export interface IncidentText {
  text: Bi;
  sources: { fr: string | null; en: string | null };
  page: { fr: number | null; en: number | null };
  places: { n: string; r: string; t: string | null; c: Confidence | null; p: string | null }[];
  acts: Act[];
}

export interface Actor {
  fr: string;
  en: string;
  type: string;
  aff: [string, string | null, string | null, string][];
  alias: string[];
}

export type Vocab = Record<string, Record<string, Bi>> & {
  periodRanges: Record<string, [string, string]>;
  categoryOrder: string[];
};

export interface Filters {
  actors: Set<string>;
  cats: Set<string>;
  periods: Set<number>;
}
