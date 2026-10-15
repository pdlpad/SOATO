import csv, json, unittest
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


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


if __name__ == "__main__":
    unittest.main()
