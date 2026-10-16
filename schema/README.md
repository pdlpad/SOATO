# Схемы

- `region.schema.json`, `district.schema.json` — JSON-файлы `data/regions/*.json`, `data/districts/*/*.json`.
- Махалли — CSV `data/mahallas/<регион>/<район>.csv`, колонки:
  `mahalla_id, name, district_soato, area_km2, populated_area_km2, pop_2026_est,
  density_gross, density_populated, method, quality_flags`.
  Пустое значение = данных нет (не ноль).
  `quality_flags = no_data` — строка-заглушка: махалля есть в списке района, но без оценки населения, метода и точки (`pop_2026_est` и `method` пусты, точки нет).
- Поля `calibration_factor` и `model_vs_official_gap` в `district.schema.json` вычисляются при расчёте оценок. Скрипта расчёта в репозитории нет, поэтому их точный смысл здесь не описан.
- В каждом районе число махалей с оценкой (`pop_2026_est` > 0) и число точек равны `mahallas_in_source` из `district.schema.json`. Это проверяют тесты.
- Точки — GeoJSON `data/points/<регион>/<район>.geojson` (EPSG:4326).
- Контуры махаллей — GeoJSON `data/polygons/<регион>/<район>.geojson` (EPSG:4326): по объекту `MultiPolygon` на махаллю, свойства `mahalla_id`, `name`, `district_soato`. Население и прочие цифры берите из CSV по `mahalla_id`. Для каждой махалли с оценкой контур есть; 6 контуров района 1714237 принадлежат махаллям со строкой `no_data`. Это проверяют тесты (в том числе что центроид лежит внутри контура). Контуры соседних махаллей местами перекрываются (у 365 махаллей внутренняя точка лежит внутри контура другой махалли).
