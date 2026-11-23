"""Parser del formato di annotazione compatto -> JSON (luoghi + atti), con validazione.

## P2-001 | puntuale | Sud-Kivu
L Uvira | ville | E* | in=Uvira:territoire,Kiliba:village | rel=3@Kolwezi>Kapata | n=nota libera
A AFDL,APR,FAZ:sostegno > civils hutu | hutu | rifugiati | donne,bambini | uccisione,saccheggio | au moins 30 | minimo | affermato | nota

rel:  3@X>Y (3 km da X verso Y) · 40@X^nord-ouest · ~X (vicino a X) · ?@X (a qualche km da X)
ruolo: E evento, R riferimento, C contenitore, O origine, D destinazione; * = luogo principale
"""
import re, sys, json
from registry import ATTORI, VIOL, RUOLI, AMBITI, CERTEZZE


def parse_rel(s):
    s = s.strip()
    if s.startswith("~"):
        return {"vicino_a": s[1:].strip()}
    m = re.match(r"^(\?|[\d.]+)@([^>^]+)(?:>(.+)|\^(.+))?$", s)
    if not m:
        raise ValueError(f"rel non valida: {s}")
    km = m.group(1)
    d = {"distanza_km": "qualche" if km == "?" else float(km), "da": m.group(2).strip()}
    if m.group(3): d["verso"] = m.group(3).strip()
    if m.group(4): d["direzione"] = m.group(4).strip()
    return d


def parse(text):
    incs, cur, errs = {}, None, []
    for n, raw in enumerate(text.splitlines(), 1):
        ln = raw.strip()
        if not ln or ln.startswith("#") and not ln.startswith("##"):
            continue
        try:
            if ln.startswith("##"):
                f = [x.strip() for x in ln[2:].split("|")]
                cur = {"id": f[0], "ambito": f[1], "old_province": f[2] if len(f) > 2 else None,
                       "luoghi": [], "atti": []}
                if f[1] not in AMBITI: errs.append(f"r{n} {f[0]}: ambito '{f[1]}'")
                incs[f[0]] = cur
            elif ln.startswith("L "):
                f = [x.strip() for x in ln[2:].split("|")]
                role = f[2].rstrip("*")
                p = {"nome": f[0], "tipo": f[1], "ruolo": RUOLI[role]}
                if f[2].endswith("*"): p["principale"] = True
                for extra in f[3:]:
                    k, _, v = extra.partition("=")
                    if k == "in":
                        p["dentro"] = [{"nome": a.split(":")[0].strip(), "tipo": a.split(":")[1].strip()}
                                       for a in v.split(",")]
                    elif k == "rel":
                        p["rel"] = parse_rel(v)
                    elif k == "n":
                        p["nota"] = v
                cur["luoghi"].append(p)
            elif ln.startswith("A "):
                left, _, right = ln[2:].partition(">")
                f = [x.strip() for x in right.split("|")]
                f += [""] * (9 - len(f))
                autori = []
                for a in left.split(","):
                    a = a.strip()
                    aid, _, ruolo = a.partition(":")
                    if aid not in ATTORI: errs.append(f"r{n} {cur['id']}: attore sconosciuto '{aid}'")
                    autori.append({"id": aid, "ruolo": ruolo or "autore"})
                viol = [v.strip() for v in f[4].split(",") if v.strip()]
                for v in viol:
                    if v not in VIOL: errs.append(f"r{n} {cur['id']}: violazione sconosciuta '{v}'")
                cert = f[7] or "affermato"
                if cert not in CERTEZZE: errs.append(f"r{n} {cur['id']}: certezza '{cert}'")
                act = {"autori": autori,
                       "vittime": {"gruppo": f[0], "identita": [x.strip() for x in f[1].split(",") if x.strip()],
                                   "condizione": f[2] or "civili",
                                   "categorie": [x.strip() for x in f[3].split(",") if x.strip()]},
                       "violazioni": viol, "categorie": sorted({VIOL.get(v, "altro") for v in viol}),
                       "certezza": cert}
                if f[5]: act["numero"] = {"testo": f[5], "precisione": f[6] or "indeterminato"}
                if f[8]: act["nota"] = f[8]
                cur["atti"].append(act)
            else:
                errs.append(f"r{n}: riga non riconosciuta: {ln[:60]}")
        except Exception as e:
            errs.append(f"r{n}: {e}: {ln[:60]}")
    for i in incs.values():
        i["categorie"] = sorted({c for a in i["atti"] for c in a["categorie"]})
        if not any(p["ruolo"] == "evento" for p in i["luoghi"]): errs.append(f"{i['id']}: nessun luogo evento")
        if not i["atti"]: errs.append(f"{i['id']}: nessun atto")
    return incs, errs


if __name__ == "__main__":
    incs, errs = parse(open(sys.argv[1], encoding="utf-8").read())
    print(len(incs), "incidenti;", len(errs), "errori")
    for e in errs: print("  ", e)
    if len(sys.argv) > 2:
        json.dump(incs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
