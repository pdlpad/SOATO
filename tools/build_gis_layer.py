#!/usr/bin/env python3
"""Собирает готовый слой махаллей для QGIS/ArcGIS: контуры и цифры в одном GeoJSON (EPSG:4326).

Запуск из корня репозитория:
  python3 tools/build_gis_layer.py                 # облегчённый слой: data/layers/mahallas_2026_simplified.geojson
  python3 tools/build_gis_layer.py --full OUT.geojson   # контуры без упрощения (около 80 МБ)

Берёт контуры (data/polygons или docs/polygons) и цифры из data/mahallas. Тестовые записи (quality_flags
содержит test_record) и строки no_data в слой не попадают. Код распространяется по лицензии MIT (см. LICENSE).
"""
import argparse
import csv
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_map import DISPLAY  # noqa: E402
from translit import to_latin  # noqa: E402

DATA = ROOT / "data"
DOCS_POLYGONS = ROOT / "docs" / "polygons"
DEFAULT_OUT = DATA / "layers" / "mahallas_2026_simplified.geojson"
HIDDEN_FLAGS = {"no_data", "test_record"}


def num(text):
    return float(text) if text else None


def rows_by_id():
    """mahalla_id -> (строка CSV, район, регион)."""
    regions = {}
    for p in glob.glob(str(DATA / "regions" / "*.json")):
        o = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        regions[o["soato"]] = DISPLAY.get(o["soato"], o["name"])
    out = {}
    for p in sorted(glob.glob(str(DATA / "mahallas" / "*" / "*.csv"))):
        p = pathlib.Path(p)
        district = json.loads((DATA / "districts" / p.parent.name / f"{p.stem}.json").read_text(encoding="utf-8"))
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                out[int(row["mahalla_id"])] = (row, district["name_soato"], regions[p.parent.name], p.parent.name)
    return out


def properties(row, district, region, region_code):
    kk = region_code == "1735"  # названия махаллей в Каракалпакстане каракалпакские
    return {
        "mahalla_id": int(row["mahalla_id"]), "name": row["name"], "name_latn": to_latin(row["name"], karakalpak=kk),
        "district_soato": row["district_soato"], "district": district, "district_latn": to_latin(district),
        "region": region, "region_latn": to_latin(region),
        "area_km2": num(row["area_km2"]), "populated_area_km2": num(row["populated_area_km2"]),
        "pop_2026_est": num(row["pop_2026_est"]), "density_gross": num(row["density_gross"]),
        "density_populated": num(row["density_populated"]), "method": row["method"] or None,
        "quality_flags": row["quality_flags"] or None,
    }


def full_geometries():
    for p in sorted(glob.glob(str(DATA / "polygons" / "*" / "*.geojson"))):
        for ft in json.loads(pathlib.Path(p).read_text(encoding="utf-8"))["features"]:
            yield ft["properties"]["mahalla_id"], ft["geometry"]


def decode_ring(flat, unit):
    pts, x, y = [], 0, 0
    for i in range(0, len(flat), 2):
        x, y = (flat[0], flat[1]) if i == 0 else (x + flat[i], y + flat[i + 1])
        pts.append([round(x * unit, 5), round(y * unit, 5)])
    pts.append(pts[0])
    return pts


def web_geometries():
    for p in sorted(glob.glob(str(DOCS_POLYGONS / "*.json"))):
        if p.endswith("index.json"):
            continue
        o = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        for mid, polys in o["m"]:
            coords = [[decode_ring(r, o["u"]) for r in poly] for poly in polys]
            yield mid, {"type": "MultiPolygon", "coordinates": coords}


def build(full=False):
    info = rows_by_id()
    feats = []
    for mid, geometry in (full_geometries() if full else web_geometries()):
        row, district, region, region_code = info[mid]
        if set(filter(None, row["quality_flags"].split(";"))) & HIDDEN_FLAGS:
            continue
        feats.append((mid, {"type": "Feature", "properties": properties(row, district, region, region_code),
                            "geometry": geometry}))
    feats.sort(key=lambda t: t[0])
    lines = (json.dumps(f, ensure_ascii=False, separators=(",", ":")) for _, f in feats)
    head = '{"type":"FeatureCollection","name":"mahallas_2026","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[\n'
    return head + ",\n".join(lines) + "\n]}\n", len(feats)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Слой махаллей для QGIS/ArcGIS")
    ap.add_argument("--full", metavar="OUT", help="собрать слой из полных контуров data/polygons в указанный файл")
    args = ap.parse_args()
    text, n = build(full=bool(args.full))
    out = pathlib.Path(args.full) if args.full else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"written: {n} mahallas -> {out} ({len(text.encode('utf-8')) / 1e6:.1f} MB)")
