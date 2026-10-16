#!/usr/bin/env python3
"""Готовит облегчённые контуры махаллей для страницы карты: docs/polygons/<район>.json.

Запуск из корня репозитория: python3 tools/build_web_polygons.py
Читает data/polygons/*/*.geojson, упрощает контуры (алгоритм Дугласа-Пекера) и пишет по файлу на район,
плюс docs/polygons/index.json с границами районов. Исходные контуры в data/ не меняются.
Код распространяется по лицензии MIT (см. LICENSE).

Формат docs/polygons/<район>.json (все координаты - целые в единицах 1e-5 градуса):
  {"v":1,"u":1e-05,"m":[[mahalla_id,[полигон,...]],...]}
  полигон = [внешнее кольцо, дыра, ...]; кольцо = плоский список [x0,y0,dx1,dy1,...],
  первая точка абсолютная, дальше разности с предыдущей точкой; замыкающая точка не хранится.
"""
import glob
import json
import math
import multiprocessing
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "polygons"
OUT = ROOT / "docs" / "polygons"
UNIT = 1e-5          # градусов на единицу целочисленной сетки (около 1,1 м)
TOL_M = 2.5          # допуск упрощения, метров
MIN_RING_AREA_M2 = 4.0


def dp_open(pts, eps):
    """Дуглас-Пекер для ломаной (итеративно). pts - список (x, y) в метрах."""
    n = len(pts)
    if n < 3:
        return list(range(n))
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        dx, dy = pts[b][0] - ax, pts[b][1] - ay
        norm2 = dx * dx + dy * dy
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i][0] - ax, pts[i][1] - ay
            if norm2 == 0:
                d2 = px * px + py * py
            else:
                t = (px * dx + py * dy) / norm2
                t = 0.0 if t < 0 else 1.0 if t > 1 else t
                qx, qy = px - t * dx, py - t * dy
                d2 = qx * qx + qy * qy
            if d2 > best:
                best, bi = d2, i
        if best > eps * eps:
            keep[bi] = True
            stack.append((a, bi))
            stack.append((bi, b))
    return [i for i in range(n) if keep[i]]


def simplify_ring(ring, eps_m):
    """Упрощает замкнутое кольцо (первая точка равна последней). Возвращает точки без замыкающей."""
    pts = ring[:-1]
    n = len(pts)
    if n <= 4:
        return pts
    lat0 = math.radians(sum(p[1] for p in pts) / n)
    kx, ky = 111320.0 * math.cos(lat0), 110570.0
    m = [(p[0] * kx, p[1] * ky) for p in pts]
    # делим кольцо в самой дальней от старта точке и упрощаем обе половины
    far = max(range(n), key=lambda i: (m[i][0] - m[0][0]) ** 2 + (m[i][1] - m[0][1]) ** 2)
    first = dp_open(m[:far + 1], eps_m)
    second = dp_open(m[far:] + [m[0]], eps_m)
    idx = first[:-1] + [far + i for i in second[:-1]]
    return [pts[i] for i in idx]


def ring_area_m2(pts):
    lat0 = math.radians(sum(p[1] for p in pts) / len(pts))
    kx, ky = 111320.0 * math.cos(lat0), 110570.0
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 * kx * ky


def quantize(pts):
    q = []
    for x, y in pts:
        p = (round(x / UNIT), round(y / UNIT))
        if not q or p != q[-1]:
            q.append(p)
    if len(q) > 1 and q[0] == q[-1]:
        q.pop()
    return q


def encode_ring(q):
    flat = [q[0][0], q[0][1]]
    for (x1, y1), (x2, y2) in zip(q, q[1:]):
        flat += [x2 - x1, y2 - y1]
    return flat


def process_polygon(rings, tol):
    out = []
    for k, ring in enumerate(rings):
        pts = simplify_ring(ring, tol)
        if len(pts) < 3 or ring_area_m2(pts) < MIN_RING_AREA_M2:
            if k == 0:
                return None
            continue
        q = quantize(pts)
        if len(q) < 3:
            if k == 0:
                return None
            continue
        out.append(q)
    return out


def process_feature(geometry, tol):
    polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    result = [p for p in (process_polygon(rings, tol) for rings in polys) if p]
    if not result:  # крошечная махалля: оставляем самый крупный контур с мягким допуском
        biggest = max(polys, key=lambda r: ring_area_m2(r[0][:-1]))
        result = [p for p in [process_polygon(biggest, 0.3)] if p]
    return result


def process_file(path):
    path = pathlib.Path(path)
    gj = json.loads(path.read_text(encoding="utf-8"))
    members, minx, miny, maxx, maxy = [], 1e9, 1e9, -1e9, -1e9
    for ft in gj["features"]:
        polys = process_feature(ft["geometry"], TOL_M)
        enc = []
        for poly in polys:
            for q in poly:
                for x, y in q:
                    minx, maxx, miny, maxy = min(minx, x), max(maxx, x), min(miny, y), max(maxy, y)
            enc.append([encode_ring(q) for q in poly])
        members.append([ft["properties"]["mahalla_id"], enc])
    members.sort(key=lambda m: m[0])
    text = json.dumps({"v": 1, "u": UNIT, "m": members}, separators=(",", ":"))
    return path.stem, text, [minx, miny, maxx, maxy], len(members)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    files = sorted(glob.glob(str(SRC / "*" / "*.geojson")))
    with multiprocessing.Pool() as pool:
        results = pool.map(process_file, files, chunksize=4)
    index, total = {}, 0
    for stem, text, bbox, count in results:
        (OUT / f"{stem}.json").write_text(text, encoding="utf-8")
        index[stem] = {"b": bbox, "n": count}
        total += len(text.encode("utf-8"))
    (OUT / "index.json").write_text(json.dumps({"u": UNIT, "d": index}, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    return len(results), total


if __name__ == "__main__":
    n, size = build()
    print(f"written: {n} district files, {size / 1e6:.1f} MB -> {OUT}")
