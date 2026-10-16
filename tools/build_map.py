#!/usr/bin/env python3
"""Собирает docs/index.html: карта центроидов махаллей с фильтрами, поиском и инфографикой.

Запуск из корня репозитория: python3 tools/build_map.py
Читает data/ (районы, махалли, точки) и data/regions/regions.geojson (границы регионов).
Код распространяется по лицензии MIT (см. LICENSE).
"""
import csv
import glob
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATE = ROOT / "tools" / "map_template.html"
OUT = ROOT / "docs" / "index.html"
POLY_INDEX = ROOT / "docs" / "polygons" / "index.json"

# В data/regions/*.json три названия сокращены: заменяем их полными.
DISPLAY = {
    "1726": "Тошкент шаҳри",
    "1727": "Тошкент вилояти",
    "1735": "Қорақалпоғистон Республикаси",
}


def rings_of(geometry):
    """Все контуры полигона или мультиполигона одним списком колец (внешние и дыры)."""
    polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    return [[[round(x, 4), round(y, 4)] for x, y in ring] for poly in polys for ring in poly]


def build_data():
    gj = json.loads((DATA / "regions" / "regions.geojson").read_text(encoding="utf-8"))
    regions = []
    for f in sorted(gj["features"], key=lambda f: f["properties"]["soato"]):
        soato = f["properties"]["soato"]
        regions.append({"n": DISPLAY.get(soato, f["properties"]["name"]),
                        "rings": rings_of(f["geometry"]), "_soato": soato})
    region_index = {r["_soato"]: k for k, r in enumerate(regions)}

    poly_index = {}
    if POLY_INDEX.exists():
        pi = json.loads(POLY_INDEX.read_text(encoding="utf-8"))
        poly_index = {k: [round(v * pi["u"], 5) for v in d["b"]] for k, d in pi["d"].items()}

    districts = []
    for path in glob.glob(str(DATA / "districts" / "*" / "*.json")):
        o = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        code = o["soato"].replace("+", "_")
        d = {"n": o["name_soato"], "r": region_index[o["region_soato"]], "_code": code, "_region": o["region_soato"]}
        if code in poly_index:
            d["c"], d["b"] = code, poly_index[code]  # файл docs/polygons/<c>.json и границы района [minLon, minLat, maxLon, maxLat]
        districts.append(d)
    districts.sort(key=lambda d: (d["r"], d["n"], d["_code"]))

    points = []
    for k, d in enumerate(districts):
        pops = {}
        with open(DATA / "mahallas" / d["_region"] / f"{d['_code']}.csv", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row["pop_2026_est"]:
                    pops[int(row["mahalla_id"])] = float(row["pop_2026_est"])
        geo = json.loads((DATA / "points" / d["_region"] / f"{d['_code']}.geojson").read_text(encoding="utf-8"))
        for ft in geo["features"]:
            mid = ft["properties"]["mahalla_id"]
            lon, lat = ft["geometry"]["coordinates"]
            points.append([ft["properties"]["name"], k, round(pops[mid]), round(lon, 5), round(lat, 5), mid])

    for r in regions:
        del r["_soato"]
    for d in districts:
        del d["_code"]
        del d["_region"]
    return {"regions": regions, "districts": districts, "points": points}


def build_html(template=TEMPLATE):
    payload = json.dumps(build_data(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return pathlib.Path(template).read_text(encoding="utf-8").replace("__DATA__", payload)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Собрать страницу карты из шаблона и данных")
    ap.add_argument("--template", default=str(TEMPLATE), help="путь к шаблону (по умолчанию tools/map_template.html)")
    ap.add_argument("--out", default=str(OUT), help="куда записать HTML (по умолчанию docs/index.html)")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(args.template), encoding="utf-8")
    print("written:", out)
