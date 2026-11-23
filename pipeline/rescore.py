"""Riclassifica geocode_luoghi.csv con regole più precise sugli omonimi e assegna la confidenza (high/low/none)."""
import re, sys, math, json
import pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from geoloc_rdc import norm, similarity, haversine, SIM_STRONG

ALT = re.compile(r"^(?P<src>[\w/]+)\s+(?P<lat>-?[\d.]+),(?P<lon>-?[\d.]+)\s+\[(?P<adm2>[^\]]*)\]\s+(?P<names>.*)$")
CITY_TYPES = {"ville", "cité", "localité"}


def parse_alt(s):
    out = []
    for part in str(s or "").split("||"):
        m = ALT.match(part.strip())
        if not m: continue
        names = [n.split(":", 1)[1].strip() for n in m.group("names").split(";") if ":" in n]
        out.append({"src": m.group("src").split("/"), "lat": float(m.group("lat")), "lon": float(m.group("lon")),
                    "adm2": m.group("adm2"), "names": names})
    return out


def rescore(row, terr_hints):
    if row.stato != "giallo" or row.precisione != "localita" or pd.isna(row.lat):
        return row.stato, None
    note = str(row.nota or "")
    k = norm(row.toponimo)
    best_adm2 = str(row.adm2 or "")
    nbest = int(row.n_fonti or 1)
    rivals = []
    for a in parse_alt(row.alternative):
        sim = max((similarity(k, norm(n)) for n in a["names"]), default=0)
        if sim < SIM_STRONG or len(a["src"]) < 2:
            continue                                   # nome solo somigliante o una sola fonte: non è un rivale
        if a["adm2"] == best_adm2 and haversine((row.lat, row.lon), (a["lat"], a["lon"])) < 40:
            continue                                   # stesso luogo spezzato in due gruppi
        if terr_hints and a["adm2"] not in terr_hints:
            continue                                   # fuori dal territoire indicato dal rapporto
        if len(a["src"]) < nbest - 1 and not terr_hints:
            continue                                   # molto meno attestato del candidato scelto
        rivals.append(a)
    blocking = [p for p in ("fuori dalla provincia", "fuori dal territoire", "una sola fonte", "solo fonti moderne",
                            "grafia simile", "non trovato", "stimata", "scartati") if p in note]
    in_terr = (best_adm2 in terr_hints) if terr_hints else None
    big_town = row.tipo in CITY_TYPES and nbest >= 4
    if not blocking and (not rivals or big_town or (in_terr and all(r["adm2"] != best_adm2 for r in rivals))):
        return "verde", f"riclassificato: {len(rivals)} omonimi residui"
    return row.stato, None


CONF = {"verde": "high", "giallo": "low", "rosso": "none"}

if __name__ == "__main__":
    L = pd.read_csv(sys.argv[1])
    data = json.load(open(sys.argv[2]))
    hints = {}
    for inc in data["incidenti"]:
        for l in inc["luoghi"]:
            hints[(inc["id"], l["nome"])] = {d["nome"] for d in l.get("dentro", []) if d.get("tipo") == "territoire"}
    new, why = [], []
    for _, r in L.iterrows():
        s, w = rescore(r, hints.get((r.incident, r.toponimo), set()))
        new.append(s); why.append(w)
    L["stato_v1"] = L.stato
    L["stato"] = new
    L["confidenza"] = L.stato.map(CONF)
    L.loc[L.lat.isna(), "confidenza"] = "none"
    L["nota_rescore"] = why
    L.to_csv(sys.argv[3], index=False, encoding="utf-8-sig")
    print(pd.crosstab(L.stato_v1, L.stato))
    print(L.confidenza.value_counts())
