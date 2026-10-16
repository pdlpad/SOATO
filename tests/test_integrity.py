import csv, importlib.util, json, math, unittest
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def polygons_of(geometry):
    """Список полигонов: каждый полигон - список колец (внешнее, затем дыры)."""
    return geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]


def ring_area_km2(ring):
    """Площадь кольца в км² в локальной равнопромежуточной проекции (хватает для проверки в пределах процентов)."""
    lat0 = math.radians(sum(y for _, y in ring) / len(ring))
    kx, ky = 111.32 * math.cos(lat0), 110.57
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 * kx * ky


def in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def in_polygon(x, y, rings):
    return in_ring(x, y, rings[0]) and not any(in_ring(x, y, h) for h in rings[1:])


class Integrity(unittest.TestCase):
    def test_regions(self):
        for p in (DATA / "regions").glob("*.json"):
            o = load(p)
            self.assertEqual(p.stem, o["soato"])
            self.assertRegex(o["soato"], r"^\d{4}$")
            self.assertTrue(o["name"])

    def test_districts_have_region(self):
        for p in (DATA / "districts").glob("*/*.json"):
            o = load(p)
            self.assertTrue((DATA / "regions" / f"{o['region_soato']}.json").exists(), p)
            self.assertEqual(p.parent.name, o["region_soato"])
            self.assertEqual(p.stem, o["soato"].replace("+", "_"))
            self.assertTrue(o["soato"].startswith(o["region_soato"]))

    def test_mahallas(self):
        seen = set()
        for p in (DATA / "mahallas").glob("*/*.csv"):
            self.assertTrue((DATA / "districts" / p.parent.name / f"{p.stem}.json").exists(), p)
            with p.open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    mid = int(r["mahalla_id"])
                    self.assertNotIn(mid, seen)
                    seen.add(mid)
                    self.assertTrue(r["name"])
                    self.assertEqual(r["district_soato"].replace("+", "_"), p.stem)
                    if r["pop_2026_est"]:
                        self.assertGreaterEqual(float(r["pop_2026_est"]), 0)

    def test_points(self):
        for p in (DATA / "points").glob("*/*.geojson"):
            mcsv = DATA / "mahallas" / p.parent.name / f"{p.stem}.csv"
            self.assertTrue(mcsv.exists(), p)
            with mcsv.open(encoding="utf-8", newline="") as f:
                ids = {int(r["mahalla_id"]) for r in csv.DictReader(f)}
            for ft in load(p)["features"]:
                x, y = ft["geometry"]["coordinates"]
                self.assertTrue(55 <= x <= 74 and 36 <= y <= 46, (p, x, y))
                self.assertIn(ft["properties"]["mahalla_id"], ids)

    def test_mahalla_points_coverage(self):
        for p in (DATA / "mahallas").glob("*/*.csv"):
            geo = load(DATA / "points" / p.parent.name / f"{p.stem}.geojson")
            ids = {ft["properties"]["mahalla_id"] for ft in geo["features"]}
            with p.open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    mid = int(r["mahalla_id"])
                    if r["quality_flags"] == "no_data":
                        self.assertEqual(r["pop_2026_est"], "", (p, mid))
                        self.assertNotIn(mid, ids, (p, mid))
                    else:
                        self.assertNotEqual(r["pop_2026_est"], "", (p, mid))
                        self.assertIn(mid, ids, (p, mid))

    def test_counts_match_source(self):
        for p in (DATA / "districts").glob("*/*.json"):
            o = load(p)
            with (DATA / "mahallas" / p.parent.name / f"{p.stem}.csv").open(encoding="utf-8", newline="") as f:
                with_pop = sum(1 for r in csv.DictReader(f) if r["pop_2026_est"] and float(r["pop_2026_est"]) > 0)
            points = len(load(DATA / "points" / p.parent.name / f"{p.stem}.geojson")["features"])
            self.assertEqual(with_pop, o["mahallas_in_source"], p)
            self.assertEqual(points, o["mahallas_in_source"], p)

    def test_region_polygons(self):
        gj = json.loads((DATA / "regions" / "regions.geojson").read_text(encoding="utf-8"))
        codes = {load(p)["soato"] for p in (DATA / "regions").glob("*.json")}
        self.assertEqual({f["properties"]["soato"] for f in gj["features"]}, codes)
        for f in gj["features"]:
            self.assertIn(f["geometry"]["type"], ("Polygon", "MultiPolygon"), f["properties"]["soato"])

    def test_mahalla_polygons(self):
        for p in (DATA / "mahallas").glob("*/*.csv"):
            with p.open(encoding="utf-8", newline="") as f:
                rows = {int(r["mahalla_id"]): r for r in csv.DictReader(f)}
            pts = {ft["properties"]["mahalla_id"]: ft["geometry"]["coordinates"]
                   for ft in load(DATA / "points" / p.parent.name / f"{p.stem}.geojson")["features"]}
            poly_path = DATA / "polygons" / p.parent.name / f"{p.stem}.geojson"
            self.assertTrue(poly_path.exists(), poly_path)
            seen = set()
            for ft in load(poly_path)["features"]:
                mid = ft["properties"]["mahalla_id"]
                self.assertIn(mid, rows, (poly_path, mid))
                self.assertNotIn(mid, seen, (poly_path, mid))
                seen.add(mid)
                self.assertEqual(ft["properties"]["name"], rows[mid]["name"], (poly_path, mid))
                self.assertEqual(ft["properties"]["district_soato"], rows[mid]["district_soato"], (poly_path, mid))
                self.assertIn(ft["geometry"]["type"], ("Polygon", "MultiPolygon"), (poly_path, mid))
                area = 0.0
                for rings in polygons_of(ft["geometry"]):
                    for k, ring in enumerate(rings):
                        self.assertGreaterEqual(len(ring), 4, (poly_path, mid))
                        self.assertEqual(ring[0], ring[-1], (poly_path, mid))
                        for x, y in ring:
                            self.assertTrue(55 <= x <= 74 and 36 <= y <= 46, (poly_path, mid, x, y))
                        area += ring_area_km2(ring) * (1 if k == 0 else -1)
                if rows[mid]["area_km2"]:
                    self.assertAlmostEqual(area / float(rows[mid]["area_km2"]), 1.0, delta=0.02, msg=(poly_path, mid))
                if mid in pts:
                    x, y = pts[mid]
                    self.assertTrue(any(in_polygon(x, y, rings) for rings in polygons_of(ft["geometry"])), (poly_path, mid))
            for mid, r in rows.items():
                if r["quality_flags"] != "no_data":
                    self.assertIn(mid, seen, (poly_path, mid))

    def test_web_polygons(self):
        docs = DATA.parent / "docs" / "polygons"
        index = load(docs / "index.json")
        for p in (DATA / "polygons").glob("*/*.geojson"):
            ids = {ft["properties"]["mahalla_id"] for ft in load(p)["features"]}
            web = load(docs / f"{p.stem}.json")
            self.assertEqual({m[0] for m in web["m"]}, ids, p)
            self.assertEqual(index["d"][p.stem]["n"], len(ids), p)
            for _, polys in web["m"]:
                self.assertTrue(polys)
                for rings in polys:
                    for ring in rings:
                        self.assertGreaterEqual(len(ring), 6, p)
                        self.assertEqual(len(ring) % 2, 0, p)
        self.assertEqual(len(index["d"]), len(list((DATA / "polygons").glob("*/*.geojson"))))

    def test_map_data_keeps_district_totals(self):
        spec = importlib.util.spec_from_file_location("build_map", DATA.parent / "tools" / "build_map.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        data = mod.build_data()
        page = {}
        for _name, k, pop, *_ in data["points"]:
            page[k] = page.get(k, 0) + pop
        for k, d in enumerate(data["districts"]):
            with (DATA / "mahallas" / d["c"][:4] / f"{d['c']}.csv").open(encoding="utf-8", newline="") as f:
                exact = sum(float(r["pop_2026_est"]) for r in csv.DictReader(f) if r["pop_2026_est"])
            self.assertEqual(page[k], round(exact), d["c"])

    def test_map_page_is_current(self):
        spec = importlib.util.spec_from_file_location("build_map", DATA.parent / "tools" / "build_map.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual((DATA.parent / "docs" / "index.html").read_text(encoding="utf-8"), mod.build_html(),
                         "docs/index.html устарел: запустите python3 tools/build_map.py")


if __name__ == "__main__":
    unittest.main()
