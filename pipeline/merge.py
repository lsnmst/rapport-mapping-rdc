"""Unisce testo estratto (FR/EN) + annotazioni -> dataset unico per periodo."""
import json, re, sys, glob
sys.path.insert(0, "scripts")
from dsl import parse
from registry import ATTORI, MACRO

LEAK = re.compile(r"\s\d{2,4}\.?\s+(?:\d{1,2}\.\s+)?([A-ZÉ][^.;]{3,90})$")  # "237. Attaques contre ..." / "457. 10. Bas-Congo"
FNTAIL = re.compile(r"(?<=[a-zé»)])(\d{2,4})\.?$")                           # "territoire118."


LINES = set()
for _f in ("work/fr.txt", "work/en.txt"):
    for _l in open(_f, encoding="utf-8"):
        _s = re.sub(r"^\d{1,2}\.\s+", "", _l.strip())
        if 3 < len(_s) < 100: LINES.add(_s)


def clean(t):
    if not t: return t, None
    leak = None
    m = LEAK.search(t)
    if m and (m.group(1) in LINES or any(m.group(1).startswith(l) for l in LINES if len(l) > 25 and l[0].isupper()
                                          and m.group(1)[:25] == l[:25])):
        leak, t = m.group(1), t[:m.start()].rstrip()
    t = FNTAIL.sub("", t).rstrip()
    return t, leak

def build(period, ann_files, out):
    base = json.load(open(f"work/period{period}.json"))
    ann = {}
    for f in ann_files:
        incs, errs = parse(open(f, encoding="utf-8").read())
        assert not errs, (f, errs)
        ann.update(incs)
    res, leaks = [], []
    for x in base["incidents"]:
        a = ann.get(x["id"])
        if a is None:
            raise SystemExit(f"manca annotazione {x['id']}")
        for lang in ("fr", "en"):
            x["text"][lang], lk = clean(x["text"][lang])
            if lk and lang == "fr": leaks.append((x["id"], lk))
        res.append({
            "id": x["id"], "periodo": period, "paragrafo": x["para"], "n_nel_paragrafo": x["seq"],
            "sezione": x["section"], "provincia_sezione": x.get("prov"), "sottosezione": x["sub"],
            "provincia_storica": a["old_province"], "ambito": a["ambito"],
            "testo": x["text"], "fonti": x["sources"], "pagina": x["page"],
            "luoghi": a["luoghi"], "atti": a["atti"], "categorie": a["categorie"],
            "autori": sorted({au["id"] for at in a["atti"] for au in at["autori"]}),
        })
    extra = set(ann) - {r["id"] for r in res}
    ctx = base["context"]
    json.dump({"periodo": period, "incidenti": res, "contesto": ctx}, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"periodo {period}: {len(res)} incidenti, annotazioni in più: {extra or 'nessuna'}")
    for l in leaks: print("  sottotitolo rimosso dal testo:", l)
    return res

if __name__ == "__main__":
    build(int(sys.argv[1]), sys.argv[3:], sys.argv[2])
