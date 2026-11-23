#!/usr/bin/env python3
"""Converte incidenti_completo.json nei file dati dell'app (public/data/).

    python scripts/build_data.py ../dataset/incidenti_completo.json public/data

- index.json   leggero, caricato all'avvio: date, posizioni, confidenza, attori, categorie
- texts.json   testi FR/EN, fonti, atti (vittime, violazioni, formule numeriche), caricato alla prima apertura di una scheda
- context.json paragrafi di contesto FR/EN per numero di paragrafo, caricato su richiesta
- vocab.json   etichette FR/EN del vocabolario controllato, attori, periodi
Le note libere dell'annotazione (in italiano) non vengono pubblicate.
"""
import json, sys
from pathlib import Path

VOCAB = {
    "categories": {
        "uccisioni": ("Meurtres et massacres", "Killings and massacres"),
        "violenza_sessuale": ("Violences sexuelles", "Sexual violence"),
        "tortura_maltrattamenti": ("Torture et mauvais traitements", "Torture and ill-treatment"),
        "privazione_liberta": ("Détentions, enlèvements, disparitions", "Detention, abduction, disappearance"),
        "sfollamento_espulsione": ("Déplacements forcés et expulsions", "Forced displacement and expulsion"),
        "distruzione_saccheggio": ("Pillages et destructions", "Looting and destruction"),
        "attacchi_beni_protetti": ("Attaques contre camps, hôpitaux, écoles, lieux de culte",
                                   "Attacks on camps, hospitals, schools, places of worship"),
        "persecuzione_discriminazione": ("Persécution et discrimination", "Persecution and discrimination"),
        "decessi_per_condizioni_imposte": ("Décès dus aux conditions imposées", "Deaths from imposed conditions"),
        "bambini_soldato": ("Recrutement d'enfants", "Child recruitment"),
    },
    "violations": {
        "uccisione": ("meurtres", "killings"), "esecuzione_sommaria": ("exécutions sommaires", "summary executions"),
        "massacro": ("massacre", "massacre"), "uso_della_forza_letale": ("usage de la force létale", "use of lethal force"),
        "bombardamento_indiscriminato": ("bombardements indiscriminés", "indiscriminate shelling"),
        "mutilazione": ("mutilations", "mutilation"), "occultamento_cadaveri": ("dissimulation des corps", "concealment of bodies"),
        "violenza_sessuale": ("violences sexuelles", "sexual violence"), "tortura": ("torture", "torture"),
        "trattamenti_inumani": ("traitements cruels, inhumains ou dégradants", "cruel, inhuman or degrading treatment"),
        "percosse": ("coups", "beatings"), "ferimento": ("blessés", "injuries"), "minaccia": ("menaces", "threats"),
        "arresto_arbitrario": ("arrestations arbitraires", "arbitrary arrests"),
        "detenzione_arbitraria": ("détention arbitraire", "arbitrary detention"), "rapimento": ("enlèvements", "abductions"),
        "sparizione_forzata": ("disparitions forcées", "enforced disappearances"),
        "reclutamento_forzato": ("enrôlement forcé", "forced recruitment"), "lavoro_forzato": ("travail forcé", "forced labour"),
        "reclutamento_minori": ("recrutement d'enfants", "child recruitment"),
        "sfollamento_forzato": ("déplacement forcé", "forced displacement"), "espulsione_forzata": ("expulsions", "expulsions"),
        "rimpatrio_forzato": ("rapatriement forcé", "forced repatriation"),
        "restrizione_movimento": ("restrictions de mouvement", "movement restrictions"),
        "saccheggio": ("pillages", "looting"), "distruzione_incendio": ("incendies", "arson"),
        "distruzione_beni": ("destruction de biens", "destruction of property"),
        "requisizione_beni": ("réquisitions", "requisition of property"),
        "perquisizione_arbitraria": ("perquisitions arbitraires", "arbitrary searches"),
        "attacco_scuola": ("attaque contre une école", "attack on a school"),
        "attacco_sanita": ("attaque contre des structures sanitaires", "attack on health facilities"),
        "attacco_luogo_di_culto": ("attaque contre un lieu de culte", "attack on a place of worship"),
        "attacco_convogli": ("attaque contre des convois", "attack on convoys"),
        "attacco_villaggi": ("attaque contre des villages", "attack on villages"), "attacco": ("attaque", "attack"),
        "attacco_campo_rifugiati": ("attaque contre un camp", "attack on a camp"),
        "attacco_personale_umanitario": ("attaque contre le personnel humanitaire", "attack on humanitarian personnel"),
        "persecuzione": ("persécution", "persecution"),
        "licenziamento_discriminatorio": ("licenciements discriminatoires", "discriminatory dismissals"),
        "sospensione_arbitraria": ("suspensions arbitraires", "arbitrary suspensions"),
        "decessi_per_privazioni": ("décès par privations", "deaths from deprivation"),
        "decessi_durante_trasferimento": ("décès pendant le transfert", "deaths during transfer"),
        "negazione_assistenza": ("refus d'assistance", "denial of assistance"),
        "ostruzione_aiuti": ("entrave à l'aide humanitaire", "obstruction of humanitarian aid"),
    },
    "victimStatus": {
        "civili": ("civils", "civilians"), "rifugiati": ("réfugiés", "refugees"), "sfollati": ("déplacés", "displaced persons"),
        "refoulés": ("refoulés", "refoulés"), "militanti": ("militants politiques", "political activists"),
        "militari": ("militaires", "soldiers"), "combattenti": ("combattants", "combatants"),
        "fuori combattimento": ("hors de combat", "hors de combat"), "detenuti": ("détenus", "detainees"),
        "disarmati": ("désarmés", "unarmed"), "personale umanitario": ("personnel humanitaire", "humanitarian personnel"),
        "personale sanitario": ("personnel de santé", "health personnel"), "personale ONU": ("personnel de l'ONU", "UN personnel"),
    },
    "victimGroups": {
        "donne": ("femmes", "women"), "bambini": ("enfants", "children"), "minori": ("mineurs", "minors"),
        "anziani": ("personnes âgées", "elderly people"), "disabili": ("personnes handicapées", "persons with disabilities"),
        "malati": ("malades et blessés", "sick and wounded"), "donne incinte": ("femmes enceintes", "pregnant women"),
    },
    "certainty": {
        "affermato": ("", ""), "condizionale": ("rapporté au conditionnel", "reported in the conditional"),
        "sospetto": ("auteurs soupçonnés", "suspected perpetrators"),
        "antefatto": ("fait antérieur rappelé par le rapport", "earlier event recalled by the report"),
    },
    "numberPrecision": {
        "esatto": ("chiffre précis", "exact figure"), "minimo": ("minimum", "minimum"), "intervallo": ("fourchette", "range"),
        "approssimato": ("approximatif", "approximate"), "ordine_di_grandezza": ("ordre de grandeur", "order of magnitude"),
        "indeterminato": ("indéterminé", "undetermined"),
    },
    "roles": {
        "autore": ("", ""), "sostegno": ("en soutien", "in support"), "mandante": ("donneur d'ordre", "ordering"),
        "complicità": ("complicité", "complicity"), "istigazione": ("incitation", "incitement"),
        "minore": ("dans une moindre mesure", "to a lesser extent"), "affiliato": ("associé", "associated"),
    },
    "scope": {
        "puntuale": ("un lieu", "single site"), "multi-sito": ("plusieurs lieux", "several sites"),
        "itinerario": ("itinéraire", "route"), "areale": ("zone", "area"), "provinciale": ("province", "province"),
    },
    "placeRole": {
        "evento": ("lieu de l'incident", "incident site"), "origine": ("provenance", "origin"),
        "destinazione": ("destination", "destination"), "riferimento": ("repère", "reference point"),
        "contenitore": ("situé dans", "located in"),
    },
    "confidence": {
        "high": ("Position fiable", "Reliable position"),
        "low": ("Position approximative", "Approximate position"),
        "none": ("Zone seulement (territoire ou province)", "Area only (territory or province)"),
    },
    "geoPrecision": {
        "localita": ("localité", "locality"), "ville": ("ville", "town"), "commune": ("commune", "commune"),
        "chefferie": ("chefferie / secteur", "chiefdom / sector"), "territoire": ("territoire", "territory"),
        "province_historique": ("province (limites de 1993-2003)", "province (1993-2003 boundaries)"),
        "stimata": ("estimée d'après la distance indiquée", "estimated from the stated distance"),
        "vicino_a": ("à proximité de", "near"),
    },
    "datePrecision": {
        "giorno": ("jour", "day"), "giorno_circa": ("aux alentours du", "around"), "mese": ("mois", "month"),
        "trimestre": ("trimestre", "quarter"), "semestre": ("semestre", "half-year"), "anno": ("année", "year"),
        "anno_parte": ("partie de l'année", "part of the year"), "anni": ("plusieurs années", "several years"),
        "periodo": ("toute la période", "whole period"),
    },
    "periods": {
        "1": ("Mars 1993 – juin 1996 : échec du processus de démocratisation et crise régionale",
              "March 1993 – June 1996: failure of the democratisation process and regional crisis"),
        "2": ("Juillet 1996 – juillet 1998 : la première guerre", "July 1996 – July 1998: the First War"),
        "3": ("Août 1998 – janvier 2001 : la deuxième guerre", "August 1998 – January 2001: the Second War"),
        "4": ("Janvier 2001 – juin 2003 : vers la transition", "January 2001 – June 2003: towards transition"),
    },
}
PERIOD_RANGES = {"1": ("1993-03-01", "1996-06-30"), "2": ("1996-07-01", "1998-07-31"),
                 "3": ("1998-08-01", "2001-01-31"), "4": ("2001-01-01", "2003-06-30")}


def fren(d):
    return {k: {"fr": v[0], "en": v[1]} for k, v in d.items()}


def status_tokens(s):
    s = (s or "").replace(" e ", ", ")
    out = []
    for part in [p.strip() for p in s.split(",") if p.strip()]:
        if part.endswith("fuori combattimento"):
            out += [part.replace(" fuori combattimento", ""), "fuori combattimento"]
        elif part.endswith(" detenuti"):
            out += [part.replace(" detenuti", ""), "detenuti"]
        elif part.endswith(" disarmati"):
            out += [part.replace(" disarmati", ""), "disarmati"]
        else:
            out.append(part)
    return [t for t in out if t]


def r5(x):
    return None if x is None else round(x, 4)


def main(src, outdir):
    D = json.load(open(src, encoding="utf-8"))
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    index, texts = [], {}
    for i in D["incidenti"]:
        pts = []
        for l in i["luoghi"]:
            g = l.get("geo")
            if l["ruolo"] in ("evento", "origine", "destinazione") and g and g.get("lat") is not None:
                pts.append({"n": l["nome"], "r": l["ruolo"], "lat": r5(g["lat"]), "lon": r5(g["lon"]),
                            "c": g["confidenza"], "p": g["precisione"], "main": bool(l.get("principale"))})
        gp = i["geo_principale"]
        index.append({
            "id": i["id"], "period": i["periodo"], "start": i["data"]["inizio"], "end": i["data"]["fine"],
            "dp": i["data"]["precisione"].replace("_dal_contesto", "").replace("_anno_dedotto", "")
                  .replace("come_incidente_precedente", "mese").replace("mesi", "mese"),
            "province": i["provincia_storica"], "scope": i["ambito"],
            "place": gp["luogo"], "lat": r5(gp["lat"]), "lon": r5(gp["lon"]), "conf": gp["confidenza"],
            "gp": gp["precisione"], "points": pts,
            "actors": i["autori"], "cats": i["categorie"],
            "para": i["paragrafo"],
        })
        texts[i["id"]] = {
            "text": i["testo"], "sources": i["fonti"], "page": i["pagina"],
            "places": [{"n": l["nome"], "r": l["ruolo"], "t": l.get("tipo"),
                        "c": (l.get("geo") or {}).get("confidenza"), "p": (l.get("geo") or {}).get("precisione")}
                       for l in i["luoghi"] if l["ruolo"] != "contenitore"],
            "acts": [{
                "actors": [{"id": au["id"], "role": au["ruolo"]} for au in a["autori"]],
                "victims": a["vittime"]["gruppo"],
                "status": status_tokens(a["vittime"]["condizione"]),
                "groups": a["vittime"]["categorie"],
                "viol": a["violazioni"], "certainty": a["certezza"],
                "number": a.get("numero", {}).get("testo"), "np": a.get("numero", {}).get("precisione"),
            } for a in i["atti"]],
        }
    index.sort(key=lambda x: (x["start"], x["id"]))
    actors = {k: {"fr": v["fr"], "en": v["en"], "type": v.get("tipo"),
                  "aff": v.get("affiliazioni", []), "alias": v.get("alias", [])} for k, v in D["attori"].items()}
    vocab = {k: fren(v) for k, v in VOCAB.items()}
    vocab["periodRanges"] = PERIOD_RANGES
    vocab["categoryOrder"] = list(VOCAB["categories"])
    ctx = {}
    for p, paras in D["contesto"].items():
        for n, c in paras.items():
            ctx[n] = {"fr": (c.get("fr") or {}).get("text"), "en": (c.get("en") or {}).get("text"),
                      "section": (c.get("fr") or {}).get("section")}
    dump = lambda name, obj: (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    dump("index.json", index); dump("texts.json", texts); dump("context.json", ctx)
    dump("vocab.json", vocab); dump("actors.json", actors)
    dump("source.json", D["fonte"])
    for f in sorted(out.iterdir()):
        print(f"{f.name:14s} {f.stat().st_size/1024:8.0f} KB")
    unknown = {s for t in texts.values() for a in t["acts"] for s in a["status"]} - set(VOCAB["victimStatus"])
    if unknown: print("ATTENZIONE: condizioni senza traduzione:", unknown)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
