# Справочник махаллей Узбекистана с привязкой к СОАТО

[![ci](https://github.com/pdlpad/SOATO/actions/workflows/ci.yml/badge.svg)](https://github.com/pdlpad/SOATO/actions/workflows/ci.yml)

**[Интерактивная карта](https://pdlpad.github.io/SOATO/)** · [English](#english)

Набор данных о **9 473 махаллях** Узбекистана. Для каждой махалли есть оценка населения на 01.01.2026, площадь, плотность, точка-центроид и контур-полигон (EPSG:4326). Махалли привязаны к СОАТО **до уровня района** (7-значный код). Охват: 14 регионов, 205 районов, 38 236 700 человек. Суммы по районам равны официальным (в пределах одного человека).

> Население по махаллям — **оценка модели** (GHS-POP и здания OSM), приведённая к официальным итогам по районам. Это не официальная статистика.

Статус: в разработке.

## Что внутри

```text
data/
  mahallas/<регион>/<район>.csv      таблица махаллей района
  points/<регион>/<район>.geojson    центроиды махаллей района
  polygons/<регион>/<район>.geojson  контуры махаллей района (MultiPolygon, по одной махалле на объект)
  districts/<регион>/<район>.json    метаданные района (официальное население, метод, калибровка)
  regions/<регион>.json              метаданные региона
  regions/regions.geojson            границы 14 регионов (Natural Earth)
  layers/mahallas_2026_simplified.geojson  готовый слой для QGIS/ArcGIS: контуры и цифры (9 471 махалля)
schema/                              описание полей и JSON Schema
tools/build_map.py                   сборка страницы карты в docs/index.html
tools/build_web_polygons.py          облегчённые контуры для карты (docs/polygons/)
tools/build_gis_layer.py             сборка слоя для QGIS/ArcGIS
tools/translit.py                    транслитерация названий в латиницу
tools/split_polygons.py              раскладка исходного GeoJSON с контурами по районам
tests/                               проверки целостности данных (запускаются в CI)
```

Имена файлов районов — это СОАТО-код района; знак `+` в коде заменён на `_`.

## Колонки `data/mahallas/*/*.csv`

| Колонка | Смысл |
|---|---|
| `mahalla_id` | идентификатор махалли |
| `name` | название |
| `district_soato` | СОАТО-код района (7 цифр) |
| `area_km2` | площадь махалли, км² |
| `populated_area_km2` | заселённая часть площади, км² |
| `pop_2026_est` | оценка населения на 01.01.2026, человек |
| `density_gross` | плотность на всю площадь, чел./км² |
| `density_populated` | плотность на заселённую площадь, чел./км² |
| `method` | на чём построена оценка: `здания OSM`, `GHS-POP` или `GHS-POP (дыра в OSM)` |
| `quality_flags` | флаги качества, через `;` (см. ниже) |

Пустое значение означает «данных нет», а не ноль. Подробнее: [schema/README.md](schema/README.md).

## Как получена оценка населения

Официальное население района на 01.01.2026 распределено по махаллям района. Распределение опирается на растр GHS-POP или на здания OpenStreetMap (колонка `method`). Итог каждого района приведён к официальной цифре; коэффициент хранится в `district.calibration_factor`. Скрипта расчёта в репозитории нет, поэтому оценку нельзя воспроизвести из этих файлов.

## Флаги качества

| Флаг | Строк | Что означает |
|---|---|---|
| `no_data` | 188 | строка-заглушка: махалля есть в списке района, но оценки, метода и точки нет |
| `district_ghs_diverges_2x` | 189 | в районе GHS-POP расходится с официальным итогом примерно вдвое или больше |
| `district_buildings_diverge_50pct` | 64 | в районе здания OSM расходятся с официальным итогом на 50 % и больше |
| `test_record` | 2 | тестовая запись источника (махалля TEST в районах Олмазор и Яшнобод): её контур лежит поверх настоящих махаллей других районов. Население входит в районные суммы, в слой для GIS запись не попадает |
| `small_polygon` | 46 | очень маленький контур махалли в источнике, оценка менее надёжна |

Строки `no_data` нужно отфильтровывать. Без них остаётся 9 473 махаллей, и именно по ним построены точки и карта. Названия флагов даны как в данных; расчётного кода в репозитории нет.

## Быстрый старт

```python
import csv

with open("data/mahallas/1735/1735401.csv", encoding="utf-8", newline="") as f:
    rows = [r for r in csv.DictReader(f) if r["quality_flags"] != "no_data"]

print(len(rows), rows[0]["name"], rows[0]["pop_2026_est"])  # 71 Өрнек МФЙ 3663.0
```

## Ограничения

- Контуры махаллей: 9 473 объекта, по одному на каждую махаллю с оценкой. Строка `no_data` без контура есть только в районе Чуст тумани (1714237, махалля Янгичак). Все центроиды лежат внутри своих контуров, площади контуров совпадают с `area_km2` в пределах 1 %.
- Данные о населении хранятся только в CSV, в контурах их нет. Все файлы контуров занимают около 75 МБ.
- Контуры соседних махаллей местами перекрываются: у 365 махаллей (около 4 %) внутренняя точка лежит внутри контура другой махалли. Геометрия оставлена как в исходном файле.
- Границы регионов взяты из Natural Earth. Граница Тошкент шаҳри там устарела и не охватывает, например, Яшнобод, поэтому часть городских точек на карте лежит вне полигона города.
- Оценки по отдельным махаллям приблизительны. Надёжны только суммы по районам, они равны официальным.

## Слой для QGIS/ArcGIS

Файл [`data/layers/mahallas_2026_simplified.geojson`](data/layers/mahallas_2026_simplified.geojson) (EPSG:4326, около 29 МБ) содержит контуры махаллей и цифры в одной таблице атрибутов: идентификатор, название (кириллицей и латиницей), район, регион, площади, население, плотности, метод и флаги. Контуры упрощены с допуском 2,5 м. Записи `no_data` и `test_record` в слой не входят. Слой с полными контурами (около 80 МБ) собирается командой `python3 tools/build_gis_layer.py --full OUT.geojson`. Латинские названия получены автоматической транслитерацией и могут отличаться от официального написания.

## Карта и проверки

Интерактивная карта: https://pdlpad.github.io/SOATO/ (границы регионов, фильтры по регионам и районам, поиск махалли, инфографика). При приближении к району или городу карта подгружает контуры махаллей и красит их по населению.

```bash
python3 tools/build_web_polygons.py           # облегчённые контуры для карты: docs/polygons/
python3 tools/build_map.py                    # пересобрать docs/index.html
python3 -m unittest discover -s tests -v      # проверки целостности данных
```

## Источники и лицензия

- Данные: [CC BY 4.0](DATA_LICENSE.md). Код: MIT.
- Население районов — официальная статистика. Оценка по махаллям использует здания OpenStreetMap (© OpenStreetMap contributors, ODbL) и GHS-POP (JRC, Европейская комиссия). Границы регионов — Natural Earth (public domain).
- Контуры махаллей: файл `mahallalar_2026.geojson` от владельца репозитория; владелец подтвердил право публикации и сообщил, что границы махаллей — общедоступная информация. Происхождение исходных границ в файле не указано (см. [SOURCES.md](SOURCES.md)).
- Подробнее: [SOURCES.md](SOURCES.md), [DATA_LICENSE.md](DATA_LICENSE.md).

Пока нет DOI, ссылайтесь на репозиторий: https://github.com/pdlpad/SOATO

---

## English

Reference dataset of **9,473 mahallas** (neighbourhoods) of Uzbekistan, linked to **SOATO** district codes (7-digit, district level). For each mahalla: area, populated area, estimated population as of 01.01.2026, gross and populated density, and a centroid point (EPSG:4326). Coverage: 14 regions, 205 districts, 38,236,700 people; district sums equal the official figures (within one person).

> Population by mahalla is a **model estimate** (GHS-POP and OSM buildings), not official statistics. Each district's total is calibrated to its official 2026 population.

- `data/mahallas/<region>/<district>.csv`: mahalla table. Column descriptions are in [`schema/`](schema/README.md).
- `data/points/<region>/<district>.geojson`: centroids. `data/polygons/<region>/<district>.geojson`: mahalla boundary polygons (9,473 features, ~75 MB). `data/districts/` and `data/regions/` hold metadata.
- Rows with `quality_flags = no_data` (188) are placeholders: no estimate, no point. Filter them out. Two rows named TEST (`test_record`, Olmazor and Yashnobod districts) are test records of the source whose polygons overlie real mahallas of other districts.
- `data/layers/mahallas_2026_simplified.geojson`: ready-to-use layer for QGIS/ArcGIS (polygons plus attributes, Cyrillic and Latin names, ~29 MB). A full-detail layer: `python3 tools/build_gis_layer.py --full OUT.geojson`.
- `method` is `здания OSM`, `GHS-POP` or `GHS-POP (дыра в OSM)`. The estimation script is not in this repository.
- Polygons carry only `mahalla_id`, `name` and `district_soato`; population lives in the CSV. Region boundaries (Natural Earth, public domain) are in `data/regions/regions.geojson`; the Tashkent city boundary there is outdated.
- Interactive map (region boundaries, filters by region and district, search): https://pdlpad.github.io/SOATO/. Rebuild with `python3 tools/build_map.py`; run the checks with `python3 -m unittest discover -s tests -v`.
- Licence: data under [CC BY 4.0](DATA_LICENSE.md), code under MIT. The data contains OpenStreetMap-derived values: © OpenStreetMap contributors. Sources: [SOURCES.md](SOURCES.md).

A Python example (reading a district CSV and dropping `no_data` rows) is in the Russian section above. Until a DOI is assigned, cite the repository: https://github.com/pdlpad/SOATO
