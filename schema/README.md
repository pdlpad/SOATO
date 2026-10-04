# Схемы

- `region.schema.json`, `district.schema.json` — JSON-файлы `data/regions/*.json`, `data/districts/*/*.json`.
- Махалли — CSV `data/mahallas/<регион>/<район>.csv`, колонки:
  `mahalla_id, name, district_soato, area_km2, populated_area_km2, pop_2026_est,
  density_gross, density_populated, method, quality_flags`.
  Пустое значение = данных нет (не ноль).
- Точки — GeoJSON `data/points/<регион>/<район>.geojson` (EPSG:4326).
