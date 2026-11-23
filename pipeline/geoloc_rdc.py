#!/usr/bin/env python3
"""
geoloc_rdc.py — Scarica dizionari geografici della RDC e geolocalizza i toponimi
degli incidenti del Rapporto Mapping (1993-2003) incrociando più fonti.

Uso:
    python geoloc_rdc.py download                 # scarica le fonti in data/raw/
    python geoloc_rdc.py match pilota_periodo1_luoghi_v2.json   # incrocia e classifica
    python geoloc_rdc.py all pilota_periodo1_luoghi_v2.json     # entrambe le cose

Output in out/:
    geocode_luoghi.csv       una riga per toponimo (verde/giallo/rosso, candidati)
    geocode_incidenti.csv    una riga per incidente (luogo principale e precisione)
    geocode.geojson          punti scelti + alternative
    revisione.html           mappa Leaflet per la revisione dei casi gialli

Dipendenze: pip install geopandas pyogrio shapely pandas requests rapidfuzz unidecode
(rapidfuzz e unidecode sono facoltative ma consigliate)
"""
from __future__ import annotations

import argparse, csv, io, json, math, re, sys, unicodedata, zipfile
from collections import defaultdict
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("out")
HDX_API = "https://data.humdata.org/api/3/action"
UA = {"User-Agent": "mapping-report-rdc-geoloc/0.1 (research, non-commercial)"}

# --------------------------------------------------------------------------------------
# Fonti
# --------------------------------------------------------------------------------------
HDX_SOURCES = {
    # chiave: (id dataset preferito, query di ricerca di riserva, formati preferiti)
    "codab": ("cod-ab-cod", "Democratic Republic of the Congo Subnational Administrative Boundaries",
              ["geopackage", "gpkg", "shp", "zipped shapefile"]),
    "osm": ("hotosm_cod_populated_places", "Democratic Republic of the Congo Populated Places (OpenStreetMap Export)",
            ["geopackage", "gpkg", "shp", "zipped shapefile"]),
    "rgc": ("609a58ef-f2fa-44e2-87f0-6e46dac4d45a", "DR Congo - Settlements",
            ["geopackage", "gpkg", "shp", "zipped shapefile", "csv"]),
}
GEONAMES_URL = "https://download.geonames.org/export/dump/CD.zip"
UCDP_URLS = [  # dalla più recente; se nessuna funziona, scaricare a mano da https://ucdp.uu.se/downloads/
    "https://ucdp.uu.se/downloads/ged/ged261-csv.zip",
    "https://ucdp.uu.se/downloads/ged/ged251-csv.zip",
]
UCDP_COUNTRY_ID = 490          # codice Gleditsch-Ward della RDC usato da UCDP
YEARS = (1993, 2003)

# Gruppi di fonti: OSM, RGC e GRID3 condividono dati (importazioni), quindi contano come "moderno";
# UCDP e GeoNames sono indipendenti e più vicini alla toponomastica degli anni '90.
FAMILY = {"osm": "moderno", "rgc": "moderno", "grid3": "moderno", "geonames": "storico", "ucdp": "storico"}

# Province del 1993-2003 (11) -> province attuali (26)
OLD_TO_NEW = {
    "Katanga": ["Haut-Katanga", "Lualaba", "Haut-Lomami", "Tanganyika"],
    "Nord-Kivu": ["Nord-Kivu"],
    "Sud-Kivu": ["Sud-Kivu"],
    "Maniema": ["Maniema"],
    "Kinshasa": ["Kinshasa"],
    "Bas-Congo": ["Kongo-Central"],
    "Bandundu": ["Kwango", "Kwilu", "Mai-Ndombe"],
    "Équateur": ["Équateur", "Mongala", "Nord-Ubangi", "Sud-Ubangi", "Tshuapa"],
    "Orientale": ["Tshopo", "Ituri", "Bas-Uele", "Haut-Uele"],
    "Kasaï-Occidental": ["Kasaï", "Kasaï-Central"],
    "Kasaï-Oriental": ["Kasaï-Oriental", "Lomami", "Sankuru"],
}

CLUSTER_KM = 10.0     # punti di fonti diverse entro questa distanza = stesso luogo
SIM_STRONG = 92       # somiglianza minima per considerare un nome "uguale"
SIM_WEAK = 85         # somiglianza minima per proporlo come candidato


# --------------------------------------------------------------------------------------
# Normalizzazione e somiglianza dei nomi
# --------------------------------------------------------------------------------------
try:
    from unidecode import unidecode as _deaccent
except ImportError:
    def _deaccent(s: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

try:
    from rapidfuzz import fuzz as _fuzz

    def similarity(a: str, b: str) -> float:
        return _fuzz.ratio(a, b)
except ImportError:
    from difflib import SequenceMatcher

    def similarity(a: str, b: str) -> float:
        return 100 * SequenceMatcher(None, a, b).ratio()

GENERIC = {"village", "localite", "cite", "camp", "colline", "groupement", "chefferie", "secteur",
           "territoire", "territory", "ville", "town", "city", "centre", "center", "quartier", "commune",
           "province", "district", "area", "region", "de", "du", "des", "la", "le", "les", "d", "l", "of", "the",
           "riviere", "fleuve", "gare", "paroisse", "monastere", "ferme", "marche", "militaire", "formation"}


def norm(name: str) -> str:
    """Forma canonica per il confronto: minuscole, senza accenti, varianti ortografiche unificate."""
    s = _deaccent(str(name)).lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = " ".join(w for w in s.split() if w not in GENERIC)
    s = s.replace("tsh", "ch").replace("tch", "ch").replace("ou", "u").replace("y", "i")
    s = re.sub(r"(.)\1+", r"\1", s)          # lettere doppie
    return s.replace(" ", "")


# --------------------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------------------
def _get(url: str, **kw):
    import requests
    r = requests.get(url, headers=UA, timeout=120, **kw)
    r.raise_for_status()
    return r


def _download(url: str, dest: Path) -> Path:
    import requests
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  già presente: {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  scarico {url}")
    with requests.get(url, headers=UA, stream=True, timeout=600) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.rename(dest)
    return dest


def hdx_package(pkg_id: str, query: str) -> dict:
    try:
        return _get(f"{HDX_API}/package_show", params={"id": pkg_id}).json()["result"]
    except Exception as e:
        print(f"  id '{pkg_id}' non trovato ({e}); cerco: {query!r}")
        res = _get(f"{HDX_API}/package_search", params={"q": query, "rows": 5}).json()["result"]["results"]
        if not res:
            raise SystemExit(f"Nessun dataset HDX trovato per {query!r}: scaricalo a mano in {RAW}/")
        for r in res:
            print(f"    candidato: {r['name']} — {r['title']}")
        return res[0]


def download_hdx(key: str):
    pkg_id, query, prefs = HDX_SOURCES[key]
    pkg = hdx_package(pkg_id, query)
    print(f"[{key}] {pkg['title']}")
    resources = pkg.get("resources", [])
    for pref in prefs:
        chosen = [r for r in resources if pref in (r.get("format", "") + " " + r.get("name", "")).lower()]
        if chosen:
            break
    else:
        chosen = resources
    if key == "codab":
        # tutti i livelli: tieni tutte le risorse del formato scelto (spesso una per livello o un unico gpkg)
        pass
    else:
        chosen = chosen[:1]
    for r in chosen:
        fname = Path(r["url"].split("?")[0]).name or f"{key}_{r['id']}"
        _download(r["url"], RAW / key / fname)


def download_all():
    for key in HDX_SOURCES:
        try:
            download_hdx(key)
        except Exception as e:
            print(f"  ERRORE {key}: {e}")
    print("[geonames]")
    _download(GEONAMES_URL, RAW / "geonames" / "CD.zip")
    print("[ucdp]")
    for url in UCDP_URLS:
        try:
            _download(url, RAW / "ucdp" / Path(url).name)
            break
        except Exception as e:
            print(f"  non disponibile: {url} ({e})")
    else:
        print(f"  Scarica a mano il CSV GED da https://ucdp.uu.se/downloads/ in {RAW/'ucdp'}/")
    g = RAW / "grid3"
    g.mkdir(parents=True, exist_ok=True)
    if not any(g.iterdir()):
        print("[grid3] Scarica a mano 'GRID3 COD - Settlement Names' (v4.0) da Columbia Academic Commons\n"
              f"        (https://academiccommons.columbia.edu, cerca 'GRID3 COD Settlement Names') e mettilo in {g}/")


# --------------------------------------------------------------------------------------
# Caricamento
# --------------------------------------------------------------------------------------
def _vector_paths(folder: Path):
    """Restituisce (percorso leggibile da pyogrio, layer) per gpkg/shp/geojson anche dentro zip."""
    import pyogrio
    out = []
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.lower().endswith((".gpkg", ".shp", ".geojson")):
                        out.append(f"/vsizip/{p}/{n}")
        elif p.suffix.lower() in (".gpkg", ".shp", ".geojson"):
            out.append(str(p))
    res = []
    for path in out:
        try:
            layers = [l[0] for l in pyogrio.list_layers(path)]
        except Exception:
            layers = [None]
        res += [(path, l) for l in layers]
    return res


def _name_columns(cols):
    keys = ("name", "nom", "alt_name", "old_name", "toponyme", "localite", "village")
    return [c for c in cols if any(k in c.lower() for k in keys)
            and not re.search(r"(id|code|pcode|source|type|date)$", c.lower())]


def load_admin():
    """Confini COD-AB: dict livello -> GeoDataFrame con colonna 'adm_name'."""
    import geopandas as gpd
    levels = {}
    for path, layer in _vector_paths(RAW / "codab"):
        m = re.search(r"adm(?:in)?[_ ]?(\d)", f"{path} {layer}".lower())
        if not m:
            continue
        lvl = int(m.group(1))
        gdf = gpd.read_file(path, layer=layer).to_crs(4326)
        cand = [c for c in gdf.columns if re.fullmatch(rf"adm{lvl}_?(fr|name|nom|en)", c.lower())] \
            or [c for c in gdf.columns if c.lower().startswith(f"adm{lvl}") and "pcode" not in c.lower()]
        if not cand or gdf.geometry.geom_type.iloc[0] not in ("Polygon", "MultiPolygon"):
            continue
        gdf = gdf.rename(columns={cand[0]: "adm_name"})[["adm_name", "geometry"]]
        if lvl not in levels or len(gdf) > len(levels[lvl]):
            levels[lvl] = gdf
            print(f"  admin livello {lvl}: {len(gdf)} poligoni ({Path(path).name}:{layer}, colonna {cand[0]})")
    if 1 not in levels:
        print("  ATTENZIONE: livello provinciale (adm1) non trovato: i controlli di provincia saranno disattivati")
    return levels


def _points_from_frame(df, source, name_cols, lat="lat", lon="lon", extra=None):
    rows = []
    for rec in df.itertuples(index=False):
        rec = rec._asdict()
        try:
            y, x = float(rec[lat]), float(rec[lon])
        except (TypeError, ValueError):
            continue
        names = set()
        for c in name_cols:
            v = rec.get(c)
            if isinstance(v, str) and v.strip():
                names.update(n.strip() for n in re.split(r"[;,/|]", v) if n.strip())
        for n in names:
            k = norm(n)
            if len(k) >= 3:
                rows.append({"source": source, "name": n, "key": k, "lat": y, "lon": x,
                             "info": (extra(rec) if extra else "")})
    return rows


def load_vector_settlements(key):
    import geopandas as gpd
    rows = []
    for path, layer in _vector_paths(RAW / key):
        gdf = gpd.read_file(path, layer=layer)
        if gdf.crs is not None:
            gdf = gdf.to_crs(4326)
        if gdf.empty:
            continue
        gdf = gdf[gdf.geometry.notna()].copy()
        pts = gdf.geometry.representative_point()
        gdf["lat"], gdf["lon"] = pts.y, pts.x
        cols = _name_columns([c for c in gdf.columns if c != "geometry"])
        place = next((c for c in gdf.columns if c.lower() in ("place", "type", "class", "categorie")), None)
        rows += _points_from_frame(gdf.drop(columns="geometry"), key, cols,
                                   extra=(lambda r, p=place: str(r.get(p, "")) if p else ""))
        print(f"  {key}: {Path(path).name}:{layer} -> colonne nome {cols}")
    for p in (RAW / key).rglob("*.csv"):
        import pandas as pd
        df = pd.read_csv(p, low_memory=False)
        lat = next((c for c in df.columns if c.lower() in ("lat", "latitude", "y")), None)
        lon = next((c for c in df.columns if c.lower() in ("lon", "long", "longitude", "x")), None)
        if lat and lon:
            rows += _points_from_frame(df, key, _name_columns(df.columns), lat, lon)
            print(f"  {key}: {p.name} (csv)")
    print(f"  {key}: {len(rows)} nomi")
    return rows


def load_geonames():
    import pandas as pd
    z = RAW / "geonames" / "CD.zip"
    if not z.exists():
        return []
    cols = ["geonameid", "name", "asciiname", "alternatenames", "lat", "lon", "fclass", "fcode",
            "cc", "cc2", "a1", "a2", "a3", "a4", "pop", "elev", "dem", "tz", "mod"]
    with zipfile.ZipFile(z) as zf:
        df = pd.read_csv(zf.open("CD.txt"), sep="\t", names=cols, dtype=str, quoting=csv.QUOTE_NONE)
    df = df[df.fclass.isin(["P", "A", "S", "T", "L"])]  # abitati, amministrativi, siti (camp), rilievi (colline), aree
    rows = _points_from_frame(df, "geonames", ["name", "asciiname", "alternatenames"],
                              extra=lambda r: f"{r['fclass']}.{r['fcode']}")
    print(f"  geonames: {len(rows)} nomi")
    return rows


def load_ucdp():
    import pandas as pd
    files = sorted((RAW / "ucdp").glob("*"))
    if not files:
        return []
    f = files[-1]
    if f.suffix == ".zip":
        with zipfile.ZipFile(f) as zf:
            n = next(n for n in zf.namelist() if n.endswith(".csv"))
            df = pd.read_csv(zf.open(n), low_memory=False)
    else:
        df = pd.read_csv(f, low_memory=False)
    df = df[(df["country_id"] == UCDP_COUNTRY_ID) & df["year"].between(*YEARS)].copy()
    df = df[df["where_prec"] <= 3]  # 1 = luogo esatto, 2 = entro 25 km, 3 = secondo livello amm.
    df["place"] = df["where_coordinates"].astype(str).str.replace(
        r"\b(town|village|city|province|territory|district|area|airport|camp|region)\b", "", regex=True)
    df["place"] = df["place"].str.replace(r"\(.*?\)", "", regex=True).str.strip(" ,")
    rows = _points_from_frame(df, "ucdp", ["place"], "latitude", "longitude",
                              extra=lambda r: f"prec={r['where_prec']} {r['date_start']} id={r['id']}")
    # deduplica stesso nome+coordinate
    seen, out = set(), []
    for r in rows:
        k = (r["key"], round(r["lat"], 3), round(r["lon"], 3))
        if k not in seen:
            seen.add(k)
            out.append(r)
    print(f"  ucdp: {len(df)} eventi RDC {YEARS[0]}-{YEARS[1]}, {len(out)} luoghi distinti")
    return out


def tag_admin(rows, admin):
    """Aggiunge a ogni punto i nomi di provincia (adm1) e territorio (adm2) in cui cade."""
    if not rows or not admin:
        return rows
    import geopandas as gpd
    gdf = gpd.GeoDataFrame(rows, geometry=gpd.points_from_xy([r["lon"] for r in rows],
                                                             [r["lat"] for r in rows]), crs=4326)
    for lvl in (1, 2, 3):
        if lvl in admin:
            j = gpd.sjoin(gdf[["geometry"]], admin[lvl], how="left", predicate="within")
            j = j[~j.index.duplicated()]
            gdf[f"adm{lvl}"] = j["adm_name"]
    return gdf.drop(columns="geometry").to_dict("records")


# --------------------------------------------------------------------------------------
# Incrocio e classificazione
# --------------------------------------------------------------------------------------
def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


class Gazetteer:
    def __init__(self, rows):
        self.rows = rows
        self.by_prefix = defaultdict(list)
        for r in rows:
            self.by_prefix[r["key"][:2]].append(r)

    def search(self, name, min_sim=SIM_WEAK):
        k = norm(name)
        if len(k) < 3:
            return []
        pool = self.by_prefix.get(k[:2], [])
        out = []
        for r in pool:
            if abs(len(r["key"]) - len(k)) > 3:
                continue
            s = 100.0 if r["key"] == k else similarity(k, r["key"])
            if s >= min_sim:
                out.append({**r, "sim": round(s, 1)})
        return out


def _same(a, b):
    return a is not None and b is not None and norm(a) == norm(b)


def cluster(matches):
    clusters = []
    for m in sorted(matches, key=lambda m: -m["sim"]):
        for c in clusters:
            if haversine((m["lat"], m["lon"]), c["center"]) <= CLUSTER_KM:
                c["members"].append(m)
                break
        else:
            clusters.append({"center": (m["lat"], m["lon"]), "members": [m]})
    for c in clusters:
        mem = c["members"]
        c["sources"] = sorted({m["source"] for m in mem})
        c["families"] = sorted({FAMILY[m["source"]] for m in mem})
        c["best_sim"] = max(m["sim"] for m in mem)
        best = max(mem, key=lambda m: (m["sim"], m["source"] != "ucdp"))
        c["center"] = (best["lat"], best["lon"])
        c["adm1"], c["adm2"] = best.get("adm1"), best.get("adm2")
        c["names"] = sorted({f"{m['source']}:{m['name']}" for m in mem})
    return clusters


def admin_match(name, admin, lvl, provinces):
    """Cerca un nome tra i poligoni amministrativi (es. territoire = adm2)."""
    if lvl not in admin:
        return None
    gdf = admin[lvl]
    k = norm(name)
    best = None
    for idx, row in gdf.iterrows():
        s = 100.0 if norm(row["adm_name"]) == k else similarity(k, norm(row["adm_name"]))
        if s >= SIM_STRONG and (best is None or s > best[0]):
            best = (s, idx, row)
    if not best:
        return None
    s, idx, row = best
    pt = row.geometry.representative_point()
    in_prov = True
    if provinces and 1 in admin:
        prov = admin[1][admin[1].contains(pt)]
        in_prov = any(_same(p, q) for p in prov["adm_name"] for q in provinces)
    return {"lat": pt.y, "lon": pt.x, "sim": s, "adm_name": row["adm_name"], "in_province": in_prov}


# --- Schema dei luoghi (annotazione per ruolo) -----------------------------------------
# ruolo: evento | riferimento | contenitore | origine | destinazione
# Si geolocalizzano evento/origine/destinazione; riferimento e contenitore servono come "ancore".
GEOCODE_ROLES = ("evento", "origine", "destinazione")
BEARING = {"nord": 0, "nord-est": 45, "est": 90, "sud-est": 135, "sud": 180, "sud-ouest": 225,
           "ouest": 270, "nord-ouest": 315}
INNER_SITES = {"gare", "quartier", "commune", "camp militaire", "centre de formation", "rivière", "cité"}
OLD_ALIASES = {"Bas-Zaïre": "Bas-Congo", "Shaba": "Katanga", "Haut-Zaïre": "Orientale",
               "Province Orientale": "Orientale"}


def bearing(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    y = math.sin(lo2 - lo1) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def offset(p, km, brg):
    la, lo, b, d = math.radians(p[0]), math.radians(p[1]), math.radians(brg), km / 6371
    la2 = math.asin(math.sin(la) * math.cos(d) + math.cos(la) * math.sin(d) * math.cos(b))
    lo2 = lo + math.atan2(math.sin(b) * math.sin(d) * math.cos(la), math.cos(d) - math.sin(la) * math.sin(la2))
    return (math.degrees(la2), math.degrees(lo2))


def province_polygon(old, admin):
    old = OLD_ALIASES.get(old, old)
    news = OLD_TO_NEW.get(old, [])
    if 1 not in admin or not news:
        return None
    g = admin[1][admin[1]["adm_name"].map(lambda n: any(_same(n, p) for p in news))]
    if not len(g):
        return None
    return g.union_all() if hasattr(g, "union_all") else g.unary_union


class Resolver:
    """Geolocalizza i luoghi di un incidente, risolvendo prima le ancore (riferimenti, contenitori)."""

    def __init__(self, inc, gaz, admin):
        self.inc, self.gaz, self.admin = inc, gaz, admin
        self.provinces = OLD_TO_NEW.get(OLD_ALIASES.get(inc.get("old_province"), inc.get("old_province")), [])
        self.cache = {}

    # punto rapido per un'ancora (città, villaggio di riferimento, territoire)
    def anchor(self, name, tipo=None):
        key = (norm(name), tipo)
        if key in self.cache:
            return self.cache[key]
        pt = None
        if tipo in ("territoire", "chefferie", "commune"):
            m = admin_match(name, self.admin, {"territoire": 2, "chefferie": 3, "commune": 3}[tipo], self.provinces)
            if m:
                pt = {"lat": m["lat"], "lon": m["lon"], "src": f"codab:{m['adm_name']}", "precisione": tipo}
        if pt is None:
            cl = [c for c in cluster(self.gaz.search(name, SIM_STRONG)) if self._in_prov(c)]
            if cl:
                c = max(cl, key=lambda c: (len(c["sources"]), c["best_sim"]))
                pt = {"lat": c["center"][0], "lon": c["center"][1], "src": " | ".join(c["names"][:3]),
                      "precisione": "localita", "adm2": c["adm2"]}
        self.cache[key] = pt
        return pt

    def _in_prov(self, c):
        return not self.provinces or 1 not in self.admin or any(_same(c["adm1"], p) for p in self.provinces)

    def geocode(self, place):
        name, tipo = place["nome"], place.get("tipo")
        dentro = place.get("dentro", [])
        rel = place.get("rel", {})
        res = {"incident": self.inc["id"], "toponimo": name, "ruolo": place["ruolo"], "tipo": tipo,
               "principale": place.get("principale", False), "stato": "rosso", "lat": None, "lon": None,
               "precisione": None, "fonti": "", "nota": place.get("nota", ""), "alternative": ""}
        notes = []

        # province intere
        if tipo == "province":
            poly = province_polygon(name, self.admin) or province_polygon(self.inc.get("old_province"), self.admin)
            if poly is not None:
                pt = poly.representative_point()
                res.update(stato="verde", lat=pt.y, lon=pt.x, precisione="province_historique", fonti="codab")
            return res

        # unità amministrative
        if tipo in ("territoire", "chefferie", "commune"):
            a = self.anchor(name, tipo)
            if a and a["precisione"] == tipo:
                res.update(stato="verde", lat=a["lat"], lon=a["lon"], precisione=tipo, fonti=a["src"])
                return res
            notes.append(f"{tipo} non trovato nei confini COD-AB")

        # ancore dal testo: contenitori di tipo città, 'da', 'vicino_a'
        terr_hints = [d["nome"] for d in dentro if d.get("tipo") == "territoire"]
        city = next((d["nome"] for d in dentro if d.get("tipo") == "ville"), None)
        ref_name = rel.get("da") or rel.get("vicino_a") or city
        ref = self.anchor(ref_name) if ref_name else None
        km = rel.get("distanza_km") if isinstance(rel.get("distanza_km"), (int, float)) else None
        radius = max(15.0, 2.5 * km) if km else (25.0 if ref_name else None)

        # siti interni a una città (gare, quartier...) il cui nome è quello della città stessa
        if city and ref and (norm(name) == norm(city) or tipo in INNER_SITES and not self.gaz.search(name, SIM_STRONG)):
            res.update(stato="verde" if norm(name) == norm(city) else "giallo", lat=ref["lat"], lon=ref["lon"],
                       precisione="ville", fonti=ref["src"])
            notes.append(f"sito interno a {city}: collocato al centro della città")
            res["nota"] = "; ".join([res["nota"]] + notes).strip("; ")
            return res

        matches = self.gaz.search(name)
        clusters = cluster(matches)
        if ref and radius:
            near = [c for c in clusters if haversine(c["center"], (ref["lat"], ref["lon"])) <= radius]
            if clusters and not near:
                notes.append(f"candidati scartati perché a più di {radius:.0f} km da {ref_name}")
            clusters = near

        def scope(c):
            in_terr = any(_same(c["adm2"], t) for t in terr_hints) if terr_hints and 2 in self.admin else None
            return self._in_prov(c), in_terr

        if clusters:
            scored = []
            for c in clusters:
                in_prov, in_terr = scope(c)
                s = (len(c["sources"]) + (1 if "storico" in c["families"] else 0) + (2 if in_terr else 0)
                     + (1 if in_prov else -3) + (2 if ref else 0) + (c["best_sim"] - 85) / 15)
                scored.append((s, c, in_prov, in_terr))
            scored.sort(key=lambda t: -t[0])
            _, best, in_prov, in_terr = scored[0]
            rivals = [c for s, c, p, t in scored[1:] if p and len(c["sources"]) >= 2]
            strong = best["best_sim"] >= SIM_STRONG
            corroborated = len(best["sources"]) >= 2 and ("storico" in best["families"] or len(best["sources"]) >= 3)
            # un'ancora dichiarata nel testo vale come conferma indipendente
            corroborated = corroborated or (ref is not None and len(best["sources"]) >= 1 and strong)
            ok = in_prov and strong and corroborated and in_terr is not False and not rivals and not notes
            if not in_prov: notes.append("fuori dalla provincia storica attesa")
            if in_terr is False: notes.append(f"fuori dal territoire atteso ({', '.join(terr_hints)})")
            if rivals: notes.append(f"{len(rivals)} altri luoghi omonimi plausibili")
            if not corroborated: notes.append("una sola fonte" if len(best["sources"]) == 1 else "solo fonti moderne")
            if not strong: notes.append(f"grafia simile ma non identica (sim {best['best_sim']})")
            if ref: notes.append(f"entro {radius:.0f} km da {ref_name}")
            alt = [f"{'/'.join(c['sources'])} {c['center'][0]:.4f},{c['center'][1]:.4f} [{c['adm2'] or '?'}] "
                   f"{'; '.join(c['names'][:3])}" for s, c, p, t in scored[1:6]]
            res.update(stato="verde" if ok else "giallo", lat=round(best["center"][0], 5),
                       lon=round(best["center"][1], 5), precisione="localita", fonti=" | ".join(best["names"]),
                       alternative=" || ".join(alt), adm1=best["adm1"], adm2=best["adm2"],
                       n_fonti=len(best["sources"]))
        elif ref and km and (rel.get("direzione") or rel.get("verso")):
            # nessun candidato: posizione stimata dalla relazione dichiarata (es. 3 km da X verso Y)
            if rel.get("direzione"):
                brg = BEARING.get(rel["direzione"])
            else:
                tgt = self.anchor(rel["verso"])
                brg = bearing((ref["lat"], ref["lon"]), (tgt["lat"], tgt["lon"])) if tgt else None
            if brg is not None:
                la, lo = offset((ref["lat"], ref["lon"]), km, brg)
                res.update(stato="giallo", lat=round(la, 5), lon=round(lo, 5), precisione="stimata",
                           fonti=f"calcolato: {km} km da {ref_name} ({ref['src']})")
                notes.append("posizione stimata dalla distanza e direzione indicate nel rapporto")
        elif ref:
            res.update(stato="giallo", lat=ref["lat"], lon=ref["lon"], precisione="vicino_a", fonti=ref["src"])
            notes.append(f"non trovato: collocato presso {ref_name}")
        else:
            for t in terr_hints:
                a = self.anchor(t, "territoire")
                if a:
                    res.update(stato="rosso", lat=a["lat"], lon=a["lon"], precisione="territoire", fonti=a["src"])
                    notes.append(f"non trovato: collocato al centro del territoire di {t}")
                    break
            else:
                notes.append("nessun candidato nelle fonti")
        res["nota"] = "; ".join([res["nota"]] + notes).strip("; ")
        return res


RANK = {"localita": 0, "ville": 1, "stimata": 1, "vicino_a": 2, "chefferie": 3, "commune": 3,
        "territoire": 4, "province_historique": 5}


def run_match(input_json: Path):
    print("Carico i confini amministrativi…")
    admin = load_admin()
    print("Carico le fonti di toponimi…")
    rows = []
    for key in ("osm", "rgc", "grid3"):
        if (RAW / key).exists():
            rows += load_vector_settlements(key)
    rows += load_geonames()
    rows += load_ucdp()
    if not rows:
        raise SystemExit("Nessuna fonte caricata: esegui prima 'download'.")
    print("Associo i punti a province e territori…")
    rows = tag_admin(rows, admin)
    gaz = Gazetteer(rows)

    data = json.loads(Path(input_json).read_text(encoding="utf-8"))
    incidents = data.get("incidents") or data.get("incidenti")  # formato pilota o dataset per periodo
    for inc in incidents:
        inc.setdefault("old_province", inc.get("provincia_storica"))
    places_out, inc_out = [], []
    for inc in incidents:
        rv = Resolver(inc, gaz, admin)
        results = [rv.geocode(p) for p in inc.get("luoghi", []) if p["ruolo"] in GEOCODE_ROLES]
        for r in results:
            r["ambito"] = inc.get("ambito")
        places_out += results
        ok = [r for r in results if r["lat"] is not None]
        ok.sort(key=lambda r: (not r["principale"], r["ruolo"] != "evento", r["stato"] != "verde",
                               RANK.get(r["precisione"], 9)))
        if not ok:
            poly = province_polygon(inc.get("old_province"), admin)
            pt = poly.representative_point() if poly is not None else None
            ok = [{"toponimo": inc.get("old_province"), "stato": "rosso", "precisione": "province_historique",
                   "lat": pt.y if pt else None, "lon": pt.x if pt else None, "fonti": "codab"}]
        p = ok[0]
        stati = [r["stato"] for r in results if r["ruolo"] == "evento"]
        inc_out.append({"incident": inc["id"], "ambito": inc.get("ambito"), "luogo_principale": p["toponimo"],
                        "stato": p["stato"], "precisione": p["precisione"], "lat": p["lat"], "lon": p["lon"],
                        "fonte": p["fonti"], "n_luoghi_evento": len(stati),
                        "verdi": stati.count("verde"), "gialli": stati.count("giallo"), "rossi": stati.count("rosso")})
    write_outputs(places_out, inc_out)



# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------
def write_outputs(places, incidents):
    OUT.mkdir(exist_ok=True)
    pf = ["incident", "ambito", "toponimo", "ruolo", "tipo", "principale", "stato", "precisione", "lat", "lon",
          "adm1", "adm2", "n_fonti", "fonti", "nota", "alternative"]
    with open(OUT / "geocode_luoghi.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, pf, extrasaction="ignore")
        w.writeheader()
        w.writerows(places)
    with open(OUT / "geocode_incidenti.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, list(incidents[0].keys()))
        w.writeheader()
        w.writerows(incidents)
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
              "properties": {k: p.get(k) for k in pf if k not in ("lat", "lon")}}
             for p in places if p.get("lat") is not None]
    gj = {"type": "FeatureCollection", "features": feats}
    (OUT / "geocode.geojson").write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    (OUT / "revisione.html").write_text(REVIEW_HTML.replace("__DATA__", json.dumps(gj, ensure_ascii=False)),
                                        encoding="utf-8")
    from collections import Counter
    cp = Counter(p["stato"] for p in places)
    ci = Counter(i["stato"] for i in incidents)
    print(f"\nToponimi:  {dict(cp)}  (totale {len(places)})")
    print(f"Incidenti: {dict(ci)}  (totale {len(incidents)})")
    print(f"File scritti in {OUT}/: geocode_luoghi.csv, geocode_incidenti.csv, geocode.geojson, revisione.html")


REVIEW_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Revisione geolocalizzazione</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#m{height:100%;margin:0;font:13px system-ui}#f{position:absolute;z-index:999;top:10px;right:10px;
background:#fff;padding:8px;border-radius:6px;box-shadow:0 1px 4px #0004}</style></head><body><div id="m"></div>
<div id="f"><label><input type="checkbox" value="verde" checked> verde</label>
<label><input type="checkbox" value="giallo" checked> giallo</label></div><script>
const data=__DATA__, col={verde:'#2a9d4b',giallo:'#e0a800',rosso:'#c0392b'};
const map=L.map('m').setView([-2.5,23.5],5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap'}).addTo(map);
let layer;function draw(){if(layer)layer.remove();const on=[...document.querySelectorAll('#f input:checked')].map(i=>i.value);
layer=L.geoJSON(data,{filter:f=>on.includes(f.properties.stato),pointToLayer:(f,ll)=>L.circleMarker(ll,
{radius:7,color:'#222',weight:1,fillColor:col[f.properties.stato],fillOpacity:.85}),onEachFeature:(f,l)=>{const p=f.properties;
l.bindPopup(`<b>${p.incident} — ${p.toponimo}</b><br>${p.stato} · ${p.precisione||''} · ${p.adm2||''}<br><small>${p.fonti||''}</small>
<br><i>${p.nota||''}</i>${p.alternative?'<br><small>Alternative: '+p.alternative+'</small>':''}`)}}).addTo(map);}
document.querySelectorAll('#f input').forEach(i=>i.onchange=draw);draw();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["download", "match", "all"])
    ap.add_argument("input", nargs="?", help="JSON dei toponimi (es. pilota_periodo1_luoghi.json)")
    a = ap.parse_args()
    if a.comando in ("download", "all"):
        download_all()
    if a.comando in ("match", "all"):
        if not a.input:
            ap.error("serve il file JSON dei toponimi")
        run_match(Path(a.input))


if __name__ == "__main__":
    main()
