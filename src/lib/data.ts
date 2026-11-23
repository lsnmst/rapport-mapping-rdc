import type { Actor, Incident, IncidentText, Vocab } from './types.ts';

const base = import.meta.env.BASE_URL;

async function get<T>(name: string): Promise<T> {
  const r = await fetch(`${base}data/${name}`);
  if (!r.ok) throw new Error(`${name}: ${r.status}`);
  return r.json() as Promise<T>;
}

export interface CoreData {
  incidents: Incident[];
  actors: Record<string, Actor>;
  vocab: Vocab;
  source: { url_fr: string; url_en: string };
}

export async function loadCore(): Promise<CoreData> {
  const [incidents, actors, vocab, source] = await Promise.all([
    get<Incident[]>('index.json'),
    get<Record<string, Actor>>('actors.json'),
    get<Vocab>('vocab.json'),
    get<{ url_fr: string; url_en: string }>('source.json'),
  ]);
  return { incidents, actors, vocab, source };
}

// testi e contesto: caricati una volta sola, alla prima scheda aperta
let textsP: Promise<Record<string, IncidentText>> | null = null;
let contextP: Promise<Record<string, { fr: string | null; en: string | null }>> | null = null;

export function loadTexts() {
  return (textsP ??= get<Record<string, IncidentText>>('texts.json'));
}

export function loadContext() {
  return (contextP ??= get<Record<string, { fr: string | null; en: string | null }>>('context.json'));
}
