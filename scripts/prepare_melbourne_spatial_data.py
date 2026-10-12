from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
RAW_SPATIAL = ROOT / "data" / "raw" / "spatial"
RAW_OSM = ROOT / "data" / "raw" / "osm"
CLEAN = ROOT / "data" / "clean"

BOUNDARY_URL = (
    "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/"
    "FeatureServer/1"
)
POPULATION_URL = (
    "https://geo.abs.gov.au/arcgis/rest/services/Hosted/"
    "SA2_Regional_Population_2025/FeatureServer/3"
)
INCOME_URL = (
    "https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/arcgis/rest/services/"
    "SA2_income_DbR_Nov25/FeatureServer/0"
)
OSM_COPYRIGHT_URL = "https://www.openstreetmap.org/copyright"
RETRIEVED_DATE = "2026-10-11"
MIN_POPULATION_FOR_ACCESS_RATE = 1000


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def polygon_parts(geometry: dict[str, Any]) -> Iterable[list[list[list[float]]]]:
    if geometry["type"] == "Polygon":
        yield geometry["coordinates"]
    elif geometry["type"] == "MultiPolygon":
        yield from geometry["coordinates"]
    else:
        raise ValueError(f"Unsupported geometry type: {geometry['type']}")


def geometry_bbox(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    points = [
        point
        for polygon in polygon_parts(geometry)
        for ring in polygon
        for point in ring
    ]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        crosses = (yi > lat) != (yj > lat)
        if crosses:
            crossing_lon = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < crossing_lon:
                inside = not inside
        j = i
    return inside


def point_in_geometry(lon: float, lat: float, geometry: dict[str, Any]) -> bool:
    for polygon in polygon_parts(geometry):
        if not polygon or not point_in_ring(lon, lat, polygon[0]):
            continue
        if any(point_in_ring(lon, lat, hole) for hole in polygon[1:]):
            continue
        return True
    return False


def perpendicular_distance(
    point: list[float], start: list[float], end: list[float]
) -> float:
    if start == end:
        return math.dist(point, start)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    numerator = abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0])
    return numerator / math.hypot(dx, dy)


def rdp(points: list[list[float]], epsilon: float) -> list[list[float]]:
    if len(points) <= 2:
        return points
    distances = [
        perpendicular_distance(point, points[0], points[-1]) for point in points[1:-1]
    ]
    if not distances:
        return [points[0], points[-1]]
    maximum = max(distances)
    if maximum <= epsilon:
        return [points[0], points[-1]]
    index = distances.index(maximum) + 1
    return rdp(points[: index + 1], epsilon)[:-1] + rdp(points[index:], epsilon)


def simplify_ring(ring: list[list[float]], epsilon: float) -> list[list[float]]:
    if len(ring) <= 5:
        return ring
    open_ring = ring[:-1] if ring[0] == ring[-1] else ring[:]
    simplified = rdp(open_ring, epsilon)
    if len(simplified) < 3:
        return ring
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return simplified


def signed_ring_area(ring: list[list[float]]) -> float:
    return sum(
        ring[index][0] * ring[index + 1][1]
        - ring[index + 1][0] * ring[index][1]
        for index in range(len(ring) - 1)
    ) / 2


def orient_ring_for_vega(ring: list[list[float]], clockwise: bool) -> list[list[float]]:
    is_clockwise = signed_ring_area(ring) < 0
    return list(reversed(ring)) if is_clockwise != clockwise else ring


def simplify_polygon(
    polygon: list[list[list[float]]], epsilon: float
) -> list[list[list[float]]]:
    simplified = [simplify_ring(ring, epsilon) for ring in polygon]
    return [
        orient_ring_for_vega(ring, clockwise=(index == 0))
        for index, ring in enumerate(simplified)
    ]


def simplify_geometry(geometry: dict[str, Any], epsilon: float) -> dict[str, Any]:
    if geometry["type"] == "Polygon":
        coordinates = simplify_polygon(geometry["coordinates"], epsilon)
    else:
        coordinates = [
            simplify_polygon(polygon, epsilon)
            for polygon in geometry["coordinates"]
        ]
    return {"type": geometry["type"], "coordinates": coordinates}


def canonical_brand(tags: dict[str, str]) -> str:
    text = " ".join(
        str(tags.get(field, "")) for field in ["brand", "name", "operator"]
    ).casefold()
    if "woolworth" in text:
        return "Woolworths"
    if re.search(r"\bcoles\b", text):
        return "Coles"
    if re.search(r"\baldi\b", text):
        return "Aldi"
    if re.search(r"\biga\b", text):
        return "IGA"
    if "foodworks" in text:
        return "FoodWorks"
    if "costco" in text:
        return "Costco"
    return "Other"


def osm_coordinates(element: dict[str, Any]) -> tuple[float, float] | None:
    if element["type"] == "node" and "lon" in element and "lat" in element:
        return float(element["lon"]), float(element["lat"])
    center = element.get("center")
    if center and "lon" in center and "lat" in center:
        return float(center["lon"]), float(center["lat"])
    return None


def approximate_distance_metres(
    first: list[float], second: list[float]
) -> float:
    mean_latitude = math.radians((first[1] + second[1]) / 2)
    dx = (first[0] - second[0]) * 111320 * math.cos(mean_latitude)
    dy = (first[1] - second[1]) * 110540
    return math.hypot(dx, dy)


def deduplicate_same_store(features: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    deduplicated: list[dict[str, Any]] = []
    removed = 0
    for feature in features:
        name = (feature["properties"]["name"] or "").strip().casefold()
        duplicate_index = None
        if name:
            for index, existing in enumerate(deduplicated):
                existing_name = (existing["properties"]["name"] or "").strip().casefold()
                if name != existing_name:
                    continue
                distance = approximate_distance_metres(
                    feature["geometry"]["coordinates"],
                    existing["geometry"]["coordinates"],
                )
                if distance < 25:
                    duplicate_index = index
                    break
        if duplicate_index is None:
            deduplicated.append(feature)
            continue

        existing = deduplicated[duplicate_index]
        if feature["properties"]["osm_type"] == "way" and existing["properties"]["osm_type"] == "node":
            winner, other = feature, existing
        else:
            winner, other = existing, feature
        for field in ["brand", "operator", "street", "suburb", "postcode"]:
            if winner["properties"].get(field) is None:
                winner["properties"][field] = other["properties"].get(field)
        deduplicated[duplicate_index] = winner
        removed += 1
    return deduplicated, removed


def arcgis_attribute_lookup(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path)
    if "error" in data:
        raise RuntimeError(f"ArcGIS error in {path.name}: {data['error']}")
    return {
        str(feature["attributes"]["sa2_code_2021"]): feature["attributes"]
        for feature in data["features"]
    }


def main() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    boundaries = load_json(
        RAW_SPATIAL / "sa2_greater_melbourne_boundaries_raw.geojson"
    )
    population = arcgis_attribute_lookup(
        RAW_SPATIAL / "sa2_greater_melbourne_population_raw.json"
    )
    income = arcgis_attribute_lookup(
        RAW_SPATIAL / "sa2_greater_melbourne_income_raw.json"
    )
    osm = load_json(RAW_OSM / "greater_melbourne_supermarkets_bbox_raw.json")

    boundary_codes = {
        str(feature["properties"]["sa2_code_2021"])
        for feature in boundaries["features"]
    }
    if boundary_codes != set(population) or boundary_codes != set(income):
        raise RuntimeError("ABS boundary, population and income SA2 codes do not match")

    indexed_boundaries = []
    for feature in boundaries["features"]:
        code = str(feature["properties"]["sa2_code_2021"])
        indexed_boundaries.append(
            (code, geometry_bbox(feature["geometry"]), feature["geometry"])
        )

    stores = []
    outside_count = 0
    for element in osm["elements"]:
        coordinates = osm_coordinates(element)
        if not coordinates:
            continue
        lon, lat = coordinates
        matched_code = None
        for code, bbox, geometry in indexed_boundaries:
            if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                continue
            if point_in_geometry(lon, lat, geometry):
                matched_code = code
                break
        if matched_code is None:
            outside_count += 1
            continue

        tags = element.get("tags", {})
        properties = {
            "store_id": f"{element['type']}/{element['id']}",
            "osm_type": element["type"],
            "osm_id": element["id"],
            "name": tags.get("name"),
            "brand": tags.get("brand"),
            "operator": tags.get("operator"),
            "brand_group": canonical_brand(tags),
            "street": tags.get("addr:street"),
            "suburb": tags.get("addr:suburb"),
            "postcode": tags.get("addr:postcode"),
            "sa2_code_2021": matched_code,
            "sa2_name_2021": population[matched_code]["sa2_name_2021"],
            "longitude": lon,
            "latitude": lat,
            "osm_url": f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
            "source": "OpenStreetMap contributors",
            "source_url": OSM_COPYRIGHT_URL,
            "retrieved_date": RETRIEVED_DATE,
        }
        stores.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
        )

    stores, duplicates_removed = deduplicate_same_store(stores)
    store_ids = [feature["properties"]["store_id"] for feature in stores]
    if len(store_ids) != len(set(store_ids)):
        raise RuntimeError("Duplicate OSM element IDs found")

    stores.sort(
        key=lambda feature: (
            feature["properties"]["sa2_code_2021"],
            feature["properties"]["brand_group"],
            feature["properties"]["name"] or "",
            feature["properties"]["store_id"],
        )
    )
    store_collection = {
        "type": "FeatureCollection",
        "name": "Greater Melbourne supermarkets",
        "attribution": "© OpenStreetMap contributors, ODbL",
        "source_url": OSM_COPYRIGHT_URL,
        "osm_data_timestamp": osm.get("osm3s", {}).get("timestamp_osm_base"),
        "query_bbox": [-38.6, 144.2, -37.3, 146.2],
        "retrieved_date": RETRIEVED_DATE,
        "features": stores,
    }

    counts_by_sa2: dict[str, Counter[str]] = {
        code: Counter() for code in boundary_codes
    }
    for feature in stores:
        props = feature["properties"]
        counts_by_sa2[props["sa2_code_2021"]][props["brand_group"]] += 1

    clean_sa2_features = []
    for feature in boundaries["features"]:
        code = str(feature["properties"]["sa2_code_2021"])
        pop = population[code]
        inc = income[code]
        brand_counts = counts_by_sa2[code]
        total = sum(brand_counts.values())
        erp = pop["erp_2025"]
        eligible_for_access_rate = bool(
            erp is not None and erp >= MIN_POPULATION_FOR_ACCESS_RATE
        )
        access_rate = (
            round(total / erp * 10000, 2) if eligible_for_access_rate else None
        )
        properties = {
            "sa2_code_2021": code,
            "sa2_name_2021": feature["properties"]["sa2_name_2021"],
            "gccsa_code_2021": "2GMEL",
            "gccsa_name_2021": "Greater Melbourne",
            "area_km2": pop["area_km2"],
            "erp_2025": erp,
            "population_density_2025": pop["pop_density_2025_people_per_km2"],
            "median_equivalised_household_income_weekly_2021": inc.get("equiv_22021"),
            "supermarket_count": total,
            "supermarkets_per_10000": access_rate,
            "access_rate_eligible": eligible_for_access_rate,
            "access_rate_status": (
                "available"
                if eligible_for_access_rate
                else f"population_below_{MIN_POPULATION_FOR_ACCESS_RATE}"
            ),
            "aldi_count": brand_counts["Aldi"],
            "coles_count": brand_counts["Coles"],
            "woolworths_count": brand_counts["Woolworths"],
            "iga_count": brand_counts["IGA"],
            "foodworks_count": brand_counts["FoodWorks"],
            "costco_count": brand_counts["Costco"],
            "other_count": brand_counts["Other"],
            "boundary_source_url": BOUNDARY_URL,
            "population_source_url": POPULATION_URL,
            "income_source_url": INCOME_URL,
            "supermarket_source_url": OSM_COPYRIGHT_URL,
            "retrieved_date": RETRIEVED_DATE,
        }
        clean_sa2_features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": simplify_geometry(feature["geometry"], epsilon=0.0002),
            }
        )

    clean_sa2_features.sort(
        key=lambda feature: feature["properties"]["sa2_code_2021"]
    )
    sa2_collection = {
        "type": "FeatureCollection",
        "name": "Greater Melbourne SA2 supermarket access",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "attribution": (
            "Australian Bureau of Statistics; © OpenStreetMap contributors, ODbL"
        ),
        "osm_data_timestamp": osm.get("osm3s", {}).get("timestamp_osm_base"),
        "access_rate_minimum_population": MIN_POPULATION_FOR_ACCESS_RATE,
        "retrieved_date": RETRIEVED_DATE,
        "features": clean_sa2_features,
    }

    store_path = CLEAN / "supermarkets_greater_melbourne.geojson"
    sa2_path = CLEAN / "sa2_greater_melbourne.geojson"
    store_path.write_text(
        json.dumps(store_collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    sa2_path.write_text(
        json.dumps(sa2_collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    total_from_sa2 = sum(
        feature["properties"]["supermarket_count"] for feature in clean_sa2_features
    )
    if total_from_sa2 != len(stores):
        raise RuntimeError("SA2 supermarket totals do not reconcile to point features")

    print(
        json.dumps(
            {
                "raw_osm_elements": len(osm["elements"]),
                "stores_in_greater_melbourne": len(stores),
                "bbox_elements_outside_greater_melbourne": outside_count,
                "duplicate_osm_store_features_removed": duplicates_removed,
                "sa2_features": len(clean_sa2_features),
                "brand_counts": Counter(
                    feature["properties"]["brand_group"] for feature in stores
                ),
                "store_geojson_bytes": store_path.stat().st_size,
                "sa2_geojson_bytes": sa2_path.stat().st_size,
            },
            ensure_ascii=False,
            indent=2,
            default=dict,
        )
    )


if __name__ == "__main__":
    main()
