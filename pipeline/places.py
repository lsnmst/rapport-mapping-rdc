"""Heuristic toponym candidates from French incident text, with administrative-level hints."""
import json, re, sys
from collections import Counter

NAME = r"([A-ZÉÈÎÔ][\w’'\-]+(?:[\s\-](?:[A-ZÉÈÎÔ][\w’'\-]+|du|de|des|la|wa))*)"
LEVEL = [
    ("territoire", r"(?:du |le |les )?territoires? d[eu’']\s?" + NAME),
    ("chefferie", r"(?:la )?(?:chefferie|collectivité(?:-chefferie)?|secteur) (?:des |de la |du |de |d’)?\s?" + NAME),
    ("groupement", r"(?:du |le )?groupements? (?:de |des |du |d’)?\s?" + NAME),
    ("localite", r"(?:village|localité|cité|quartier|commune|camp|colline|centre de négoce|site) (?:de |des |du |d’|de la )?\s?" + NAME),
    ("ville", r"(?:la )?ville d[eu’']\s?" + NAME),
    ("lieu", r"\b(?:à|au|dans|vers|entre|près de|de) " + NAME),
]
STOP = set("""Le La Les Un Une Des En Au Aux Du De Dans Entre Après Avant Lors Selon Kasaïens Katangais FAZ JUFERI
UFERI UDPS AFDL APR FAB Mayi-Mayi Hutu Hunde Nyanga Nande Tutsi Banyarwanda Garde Gouverneur Mobiles Gécamines
Zaïre Rwanda Burundi Ouganda Interahamwe ex-FAR Équipe Mapping Président Kinshasa-Est MSF CICR Nouveau Zaïrois
Kasaïen Katangais Mobutu Kengo Tshisekedi Birindwa Église Union Conférence Division Brigade Mars Avril Mai Juin Juillet
Août Septembre Octobre Novembre Décembre Janvier Février Régie Banyamulenge Shi Hema Lendu Bembe""".split())


def extract(text):
    found = []
    for lvl, pat in LEVEL:
        for m in re.finditer(pat, text):
            n = m.group(1).strip(" -’'")
            first = n.split()[0]
            if first in STOP or n in STOP or len(n) < 3:
                continue
            found.append((lvl, n))
    seen, out = set(), []
    for lvl, n in found:  # keep most specific level per name
        if n not in seen:
            seen.add(n); out.append({"name": n, "level_hint": lvl})
    return out


if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    allp = Counter()
    for inc in d["incidents"]:
        inc["places_candidates"] = extract(inc["text"]["fr"])
        for p in inc["places_candidates"]:
            allp[p["name"]] += 1
    json.dump(d, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    n = sum(len(i["places_candidates"]) for i in d["incidents"])
    print("incidents", len(d["incidents"]), "candidate mentions", n, "unique", len(allp))
    for inc in d["incidents"]:
        print(inc["id"], "|", "; ".join(f'{p["name"]} ({p["level_hint"]})' for p in inc["places_candidates"]))
