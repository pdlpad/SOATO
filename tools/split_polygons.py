#!/usr/bin/env python3
"""Раскладывает GeoJSON с контурами махаллей по районам: data/polygons/<регион>/<район>.geojson.

Запуск из корня репозитория: python3 tools/split_polygons.py путь/к/mahallalar_2026.geojson
Геометрия берётся из исходного файла без изменений. Атрибуты (название, СОАТО района) берутся
из data/mahallas, поэтому цифры населения живут только в CSV и не расходятся с контурами.
Код распространяется по лицензии MIT (см. LICENSE).
"""
import csv
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "polygons"


def index_mahallas():
    """mahalla_id -> (каталог региона, имя файла района, название, СОАТО района)."""
    idx = {}
    for path in sorted(glob.glob(str(DATA / "mahallas" / "*" / "*.csv"))):
        p = pathlib.Path(path)
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                idx[int(row["mahalla_id"])] = (p.parent.name, p.stem, row["name"], row["district_soato"])
    return idx


def split(source):
    gj = json.loads(pathlib.Path(source).read_text(encoding="utf-8"))
    idx = index_mahallas()
    groups = {}
    for ft in gj["features"]:
        mid = int(ft["properties"]["mahalla_id"])
        if mid not in idx:
            raise SystemExit(f"в data/mahallas нет махалли {mid}")
        region, stem, name, district = idx[mid]
        key = ft["properties"].get("soato_key")
        if key is not None and key.replace("+", "_") != stem:
            raise SystemExit(f"махалля {mid}: район в контурах {key}, в CSV {district}")
        if ft["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
            raise SystemExit(f"махалля {mid}: геометрия {ft['geometry']['type']}")
        feature = {"type": "Feature", "geometry": ft["geometry"],
                   "properties": {"mahalla_id": mid, "name": name, "district_soato": district}}
        groups.setdefault((region, stem), []).append((mid, feature))
    for (region, stem), items in sorted(groups.items()):
        items.sort(key=lambda t: t[0])
        out = OUT / region / f"{stem}.geojson"
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = (json.dumps(f, ensure_ascii=False, separators=(",", ":")) for _, f in items)
        out.write_text('{"type":"FeatureCollection","features":[\n' + ",\n".join(lines) + "\n]}\n", encoding="utf-8")
    return len(gj["features"]), len(groups)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    n, d = split(sys.argv[1])
    print(f"written: {n} polygons in {d} district files -> {OUT}")
