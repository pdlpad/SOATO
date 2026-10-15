# Справочник махаллей Узбекистана с привязкой к СОАТО

## English

Reference dataset of **~9,500 mahallas** (neighbourhoods) of Uzbekistan, linked to **SOATO** district codes (7-digit, district level). For each mahalla: area, populated area, estimated population as of 01.01.2026, gross and populated density, and a centroid point (EPSG:4326).

> Population by mahalla is a **model estimate** (GHS-POP and OSM buildings), not official statistics. Each district's total is calibrated to its official 2026 population.

- `data/mahallas/<region>/<district>.csv`: mahalla table. Column descriptions are in [`schema/`](schema/README.md).
- `data/points/<region>/<district>.geojson`: centroids. `data/districts/` and `data/regions/` hold metadata.
- Rows with `quality_flags = no_data` are placeholders (no estimate, no point). Filter them out.
- No mahalla boundary polygons are included.
- Licence: data under [CC BY 4.0](DATA_LICENSE.md), code under MIT. The data contains OpenStreetMap-derived values: © OpenStreetMap contributors. Sources: [SOURCES.md](SOURCES.md).
- Status: in development.

```python
import csv

with open("data/mahallas/1735/1735401.csv", encoding="utf-8", newline="") as f:
    rows = [r for r in csv.DictReader(f) if r["quality_flags"] != "no_data"]

print(len(rows), rows[0]["name"], rows[0]["pop_2026_est"])  # 71 Өрнек МФЙ 3663.0
```

Until a DOI is assigned, cite the repository: https://github.com/pdlpad/SOATO

---

## Русский

Набор данных по махаллям (≈9 500) с оценкой населения на 01.01.2026, плотностью
и точкой-центроидом. Привязка к СОАТО — **до уровня района** (7-значный ключ).

> Население по махаллям — **оценка модели** (GHS-POP / здания OSM, калибровка по
> официальным данным района), а не официальная статистика.

Статус: в разработке.

## Источники и лицензия

- Данные: [CC BY 4.0](DATA_LICENSE.md), код: MIT.
- Оценка населения махаллей основана на данных OpenStreetMap: © OpenStreetMap contributors (ODbL).
- Подробнее: [SOURCES.md](SOURCES.md), [DATA_LICENSE.md](DATA_LICENSE.md).
