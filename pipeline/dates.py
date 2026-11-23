"""Estrae intervalli di date (inizio, fine, precisione) dal testo francese degli incidenti."""
import re, json, sys, calendar

M = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
     "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}
MN = "|".join(M)
D = r"(1er|\d{1,2})"
Y = r"((?:19|20)\d\d)"
PERIODS = {1: ("1993-03-01", "1996-06-30"), 2: ("1996-07-01", "1998-07-31"),
           3: ("1998-08-01", "2001-01-31"), 4: ("2001-01-01", "2003-06-30")}


def d(n): return 1 if n == "1er" else int(n)
def last(y, m): return calendar.monthrange(y, m)[1]
def iso(y, m, dd): return f"{y:04d}-{m:02d}-{dd:02d}"


def parse(text, ctx_year):
    t = text[:260].replace("’", "'")
    tl = t.lower()
    # 0. quindicine: "au cours de la deuxième quinzaine d'octobre 1996"
    m = re.search(rf"(première|deuxième|seconde) quinzaine (?:du mois )?(?:d'|de )\s*({MN})(?:\s+{Y})?", tl)
    if m and (m.group(3) or ctx_year):
        y = int(m.group(3)) if m.group(3) else ctx_year; mo = M[m.group(2)]
        return (iso(y, mo, 1), iso(y, mo, 15), "mese") if m.group(1) == "première" else (iso(y, mo, 16), iso(y, mo, last(y, mo)), "mese")
    # 1. intervallo con giorni: "entre le 22 et le 24 septembre 1996", "du 19 au 23 août 1995",
    #    "dans la nuit du 13 au 14 octobre 1996", "entre le 28 décembre 1998 et le 5 janvier 1999"
    m = re.search(rf"{D}\s+({MN})\s+{Y}?\s*(?:et le|au|et)\s+{D}\s+({MN})\s+{Y}", tl)
    if m:
        y2 = int(m.group(6)); y1 = int(m.group(3)) if m.group(3) else y2
        return iso(y1, M[m.group(2)], d(m.group(1))), iso(y2, M[m.group(5)], d(m.group(4))), "giorno"
    m = re.search(rf"(?:entre le|du|nuit du|les)\s+{D}\s+(?:et(?: le)?|au)\s+{D}\s+({MN})(?:\s+{Y})?", tl)
    if m:
        y = int(m.group(4)) if m.group(4) else ctx_year
        if y: return iso(y, M[m.group(3)], d(m.group(1))), iso(y, M[m.group(3)], d(m.group(2))), "giorno"
    # 2. giorno singolo
    m = re.search(rf"{D}\s+({MN})(?:\s+{Y})?", tl)
    if m and (m.group(3) or ctx_year):
        y = int(m.group(3)) if m.group(3) else ctx_year
        dd = d(m.group(1))
        if dd <= last(y, M[m.group(2)]):
            approx = bool(re.search(r"(aux alentours|vers le|autour du|environs du)", tl[:max(0, m.start()) + 5]))
            return iso(y, M[m.group(2)], dd), iso(y, M[m.group(2)], dd), "giorno_circa" if approx else "giorno"
    # 3. intervallo di mesi: "entre juin et décembre 1999", "de 1998 à 1999", "entre mai et juin 1997"
    m = re.search(rf"(?:entre|de|d')\s*({MN})\s+(?:{Y}\s+)?(?:et|à)\s+({MN})\s+{Y}", tl)
    if m:
        y2 = int(m.group(4)); y1 = int(m.group(2)) if m.group(2) else y2
        return iso(y1, M[m.group(1)], 1), iso(y2, M[m.group(3)], last(y2, M[m.group(3)])), "mese"
    # 4. mese singolo, con fine/début/mi-
    m = re.search(rf"(fin|début|mi-|courant|cours du mois d'|cours du mois de|mois d'|mois de)?\s*({MN})\s+{Y}", tl)
    if m:
        y, mo = int(m.group(3)), M[m.group(2)]
        q = (m.group(1) or "").strip()
        if q == "fin": return iso(y, mo, 20), iso(y, mo, last(y, mo)), "mese"
        if q == "début": return iso(y, mo, 1), iso(y, mo, 10), "mese"
        if q == "mi-": return iso(y, mo, 10), iso(y, mo, 20), "mese"
        return iso(y, mo, 1), iso(y, mo, last(y, mo)), "mese"
    m = re.search(rf"(?:en|au cours d[eu']|fin|début|vers la fin d[e'])\s*({MN})\b", tl)
    if m and ctx_year:
        mo = M[m.group(1)]
        return iso(ctx_year, mo, 1), iso(ctx_year, mo, last(ctx_year, mo)), "mese_anno_dedotto"
    # 5. anni / intervalli di anni / semestri / trimestri
    m = re.search(rf"(?:entre|de)\s+(?:la (?:fin|mi-)\s*(?:de\s*)?)?{Y}\s+(?:et|à)\s+(?:(?:janvier|juin)\s+)?{Y}", tl)
    if m: return f"{m.group(1)}-01-01", f"{m.group(2)}-12-31", "anni"
    m = re.search(rf"(premier|deuxième|second) (trimestre|semestre) (?:de |d')?(?:l'année )?{Y}", tl)
    if m:
        y = int(m.group(3)); first = m.group(1) == "premier"
        if m.group(2) == "trimestre": return (f"{y}-01-01", f"{y}-03-31", "trimestre") if first else (f"{y}-04-01", f"{y}-06-30", "trimestre")
        return (f"{y}-01-01", f"{y}-06-30", "semestre") if first else (f"{y}-07-01", f"{y}-12-31", "semestre")
    m = re.search(rf"(fin|début)\s+(?:de\s+)?(?:l'année\s+)?{Y}", tl)
    if m:
        y = int(m.group(2))
        return (f"{y}-09-01", f"{y}-12-31", "anno_parte") if m.group(1) == "fin" else (f"{y}-01-01", f"{y}-04-30", "anno_parte")
    m = re.search(rf"\b(?:en|au cours de(?: l'année)?|courant|depuis|à compter de|à partir de|dès)\s+{Y}", tl)
    if m: return f"{m.group(1)}-01-01", f"{m.group(1)}-12-31", "anno"
    m = re.search(Y, tl)
    if m: return f"{m.group(1)}-01-01", f"{m.group(1)}-12-31", "anno"
    return None


def run(files):
    out = {}
    for f in files:
        data = json.load(open(f))
        p = data["periodo"]
        prev_year = int(PERIODS[p][0][:4]); prev = None
        for inc in data["incidenti"]:
            r = parse(inc["testo"]["fr"], prev_year)
            if r is None and prev and re.search(r"même période", inc["testo"]["fr"][:80]):
                r = (prev["inizio"], prev["fine"], "come_incidente_precedente")
            if r is None:
                ctx = data["contesto"].get(str(inc["paragrafo"]), {}).get("fr") or {}
                r = parse(ctx.get("text", ""), prev_year)
                if r: r = (r[0], r[1], r[2] + "_dal_contesto")
            if r is None:
                r = (PERIODS[p][0], PERIODS[p][1], "periodo")
            inc["data"] = {"inizio": r[0], "fine": r[1], "precisione": r[2]}
            if r[2] not in ("periodo",) and r[0][:4].isdigit():
                prev_year = int(r[1][:4]) if r[2] in ("giorno", "giorno_circa", "mese") else prev_year
            out[inc["id"]] = inc["data"]; prev = inc["data"]
        json.dump(data, open(f, "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    res = run(sys.argv[1:])
    from collections import Counter
    print(Counter(v["precisione"] for v in res.values()))
