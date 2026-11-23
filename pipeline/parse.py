"""Parse Mapping Report text (pdftotext -layout) into headings, paragraphs, bullets (incidents) and footnotes."""
import re, json, sys

FOOT_SEP = re.compile(r"^\s*_{5,}\s*$")
PAGENUM = re.compile(r"^\s{20,}(\d{1,3})\s*$")
PARA = re.compile(r"^(\d{1,4})(?:\.\s+|\s{3,})(\D.*)")
BULLET = re.compile(r"^\s*[•]\s+(.*)")
FNSTART = re.compile(r"^\s{0,3}(\d{1,4})\s*$|^\s{0,3}(\d{1,4})\s{1,3}(\S.*)$")
HEAD = re.compile(r"^(SECTION [IV]+\.|CHAPITRE [IVX]+\.|CHAPTER [IVX]+\.|[A-H]\.\s{2,}|[A-H]\.\t)")
FNREF = re.compile(r"(?<=[^\s\d])\s(\d{2,4})(?=[\s.,;:)]|$)")


def parse(path):
    raw = open(path, encoding="utf-8").read()
    lines = []
    for pi, pg in enumerate(raw.split("\f")):
        lines.append(("\f", pi + 1))
        lines.extend((l, pi + 1) for l in pg.split("\n"))
    body, notes = [], {}
    in_fn, cur_fn, page = False, None, None
    for ln, pdfpage in lines:
        if ln == "\f":
            in_fn = False; page = pdfpage
            continue
        if PAGENUM.match(ln) or ln.strip() == "Unofficial translation from French original":
            continue
        if FOOT_SEP.match(ln):
            in_fn = True
            continue
        if in_fn:
            m = FNSTART.match(ln)
            if m and (m.group(1) or m.group(2)):
                n = int(m.group(1) or m.group(2))
                if cur_fn is None or n == cur_fn + 1 or n not in notes:
                    cur_fn = n
                    notes[n] = (m.group(3) or "").strip()
                    continue
            if cur_fn is not None and ln.strip():
                notes[cur_fn] = (notes[cur_fn] + " " + ln.strip()).strip()
            continue
        body.append((page, ln))

    items, cur, last = [], None, 0
    def flush():
        if cur:
            cur["text"] = re.sub(r"\s+", " ", cur["text"]).strip()
            items.append(cur)
    for bi, (page, ln) in enumerate(body):
        s = ln.strip()
        if not s:
            continue
        if HEAD.match(s):
            flush(); cur = {"type": "heading", "text": s, "page": page}; continue
        prev_blank = bi == 0 or not body[bi - 1][1].strip()
        next_blank = bi + 1 >= len(body) or not body[bi + 1][1].strip()
        numbered = re.match(r"^\d{1,2}\.\s+[A-ZÉ][^.]{2,40}$", s) and not ln.startswith(" ")
        if numbered and prev_blank:
            flush(); cur = {"type": "subheading", "level": "province", "text": re.sub(r"^\d{1,2}\.\s+", "", s), "page": page}
            continue
        if cur and cur["type"] == "subheading" and not PARA.match(s) and not BULLET.match(ln) and not prev_blank:
            if cur.get("level") == "province":  # sottotitolo sotto la provincia
                flush(); cur = {"type": "subheading", "level": "zone", "text": s, "page": page}
            else:
                cur["text"] += " " + s
            continue
        if (prev_blank and next_blank and len(s) < 50 and not ln.startswith("  ")
                and not re.search(r"[.,;:»\d]$", s) and not BULLET.match(ln)
                and (s[0].isupper() or re.match(r"^\d\.\s+[A-ZÉ]", s))):
            lvl = "province" if re.match(r"^\d\.\s+", s) else "zone"
            flush(); cur = {"type": "subheading", "level": lvl, "text": re.sub(r"^\d\.\s+", "", s), "page": page}; continue
        m = PARA.match(s)
        if m:
            n = int(m.group(1))
            if last < n <= last + 6 or (n == last and last > 0):
                last = n
                flush(); cur = {"type": "para", "num": n, "num_printed": n, "text": m.group(2), "page": page}; continue
        m = BULLET.match(ln)
        if m:
            flush(); cur = {"type": "bullet", "text": m.group(1), "page": page}; continue
        if cur is None:
            continue
        # heading continuation lines (all caps)
        if cur["type"] == "heading" and s.isupper():
            cur["text"] += " " + s; continue
        if cur["type"] == "heading" and not s.isupper():
            flush(); cur = {"type": "orphan", "text": s, "page": page}; continue
        cur["text"] += " " + s
    flush()

    # fix duplicated numbers only when the following paragraph confirms the typo (132,132,134)
    paras = [x for x in items if x["type"] == "para"]
    for i in range(1, len(paras) - 1):
        a, b, c = paras[i - 1]["num_printed"], paras[i]["num_printed"], paras[i + 1]["num_printed"]
        if a == b and c == b + 2:
            paras[i]["num"] = b + 1
    # attach footnote refs
    for it in items:
        refs = [int(x) for x in FNREF.findall(it["text"]) if int(x) in notes]
        it["fn"] = refs
    return items, notes


if __name__ == "__main__":
    items, notes = parse(sys.argv[1])
    json.dump({"items": items, "notes": notes}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print(len(items), "items", len(notes), "notes")
