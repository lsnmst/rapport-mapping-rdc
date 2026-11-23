"""Build aligned FR/EN incident records for one chapter of Section I."""
import json, re, sys

CHAP = {
    1: (r"CHAPITRE I\. MARS 1993", r"CHAPTER I\. MARCH 1993"),
    2: (r"CHAPITRE II\. JUILLET 1996", r"CHAPTER II\. JULY 1996"),
    3: (r"CHAPITRE III\. AOÛT 1998", r"CHAPTER III\. AUGUST 1998"),
    4: (r"CHAPITRE IV\. JANVIER 2001", r"CHAPTER IV\. JANUARY 2001"),
}
END = (r"CHAPITRE [IV]+\.|CHAPTER [IV]+\.")
FNREF = re.compile(r"\s(\d{1,4})\s*\.?\s*$")


def chapter_items(items, start_pat):
    out, on = [], False
    for x in items:
        if x["type"] == "heading" and x.get("page") and x["page"] > 40:
            if re.match(start_pat, x["text"]):
                on = True; out.append(x); continue
            if on and re.match(END, x["text"]):
                break
        if on:
            out.append(x)
    return out


def fix_numbering(items):
    """Source PDF repeats some paragraph numbers (e.g. two '132.'): renumber by sequence, keep printed number."""
    prev, flags = None, []
    for x in items:
        if x["type"] != "para":
            continue
        x["num_printed"] = x["num"]
        if prev is not None and x["num"] != prev + 1:
            flags.append((x["num"], prev + 1))
            x["num"] = prev + 1
        prev = x["num"]
    return flags


def structure(items):
    """Walk items: track heading (province), last para (context), bullets = incidents."""
    heading, prov, sub, para, recs, k = None, None, None, None, [], 0
    contexts = {}
    for x in items:
        t = x["type"]
        if t == "heading":
            if re.match(r"^[A-H]\.", x["text"]):
                heading, prov, sub = x["text"], None, None
            else:
                sub = x["text"]
        elif t == "subheading" and x.get("level") == "province":
            prov, sub = x["text"], None
        elif t in ("orphan", "subheading"):
            sub = x["text"]
        elif t == "para":
            para, k = x, 0
            contexts[x["num"]] = {"text": x["text"], "page": x["page"], "fn": x["fn"],
                                  "section": heading, "sub": sub}
        elif t == "bullet":
            k += 1
            m = FNREF.search(x["text"])
            text = x["text"][: m.start()].strip() if m else x["text"]
            recs.append({
                "para": para["num"] if para else None,
                "seq": k,
                "section": heading, "prov": prov, "sub": sub,
                "text": text,
                "footnote": int(m.group(1)) if m else None,
                "page": x["page"],
            })
    return recs, contexts


def main(chap, out):
    data = {}
    for lang, pat in zip(("fr", "en"), CHAP[chap]):
        d = json.load(open(f"work/{lang}.json"))
        items = chapter_items(d["items"], pat)
        flags = [(x["num_printed"], x["num"]) for x in items if x["type"] == "para" and x["num_printed"] != x["num"]]
        recs, ctx = structure(items)
        for r in recs:
            r["sources"] = d["notes"].get(str(r["footnote"])) if r["footnote"] else None
        data[lang] = (recs, ctx, flags)
    fr, en = data["fr"][0], data["en"][0]
    key = lambda r: (r["para"], r["seq"])
    en_by = {key(r): r for r in en}
    incidents, unmatched = [], []
    for i, r in enumerate(fr, 1):
        e = en_by.get(key(r))
        if not e:
            unmatched.append(key(r))
        incidents.append({
            "id": f"P{chap}-{i:03d}",
            "period": chap,
            "para": r["para"], "seq": r["seq"],
            "section": {"fr": r["section"], "en": e["section"] if e else None},
            "prov": {"fr": r["prov"], "en": e["prov"] if e else None},
            "sub": {"fr": r["sub"], "en": e["sub"] if e else None},
            "text": {"fr": r["text"], "en": e["text"] if e else None},
            "sources": {"fr": r["sources"], "en": e["sources"] if e else None},
            "page": {"fr": r["page"], "en": e["page"] if e else None},
        })
    ctx = {n: {"fr": c, "en": data["en"][1].get(n)} for n, c in data["fr"][1].items()}
    json.dump({"incidents": incidents, "context": ctx,
               "numbering_fixes": {"fr": data["fr"][2], "en": data["en"][2]},
               "unmatched_fr": unmatched,
               "extra_en": [key(r) for r in en if key(r) not in {key(x) for x in fr}]},
              open(out, "w"), ensure_ascii=False, indent=1)
    print(f"period {chap}: fr={len(fr)} en={len(en)} unmatched={unmatched} "
          f"fixes fr={data['fr'][2]} en={data['en'][2]}")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
