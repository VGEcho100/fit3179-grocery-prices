from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_ABS = ROOT / "data" / "raw" / "abs"
CLEAN = ROOT / "data" / "clean"

ABS_BASE_URL = (
    "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/"
    "consumer-price-index-australia/aug-2026/"
)
CHOICE_URL = (
    "https://www.choice.com.au/shopping/everyday-shopping/supermarkets/"
    "articles/cheapest-groceries-australia"
)

MEASURE_NAMES = {
    "Index Numbers": "index_number",
    "Percentage Change from Corresponding Month of Previous Year": "annual_percent_change",
    "Percentage Change from Previous Period": "monthly_percent_change",
    "Contribution to All groups CPI Index Number": "contribution_to_all_groups_index",
    "Change in Contribution to All groups CPI Index Number": "change_in_contribution",
}

CITIES = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Adelaide",
    "Perth",
    "Hobart",
    "Darwin",
    "Canberra",
]


def parse_description(description: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in description.split(";") if part.strip()]
    if len(parts) < 3:
        raise ValueError(f"Unexpected ABS series description: {description!r}")
    return parts[0], parts[1], parts[2]


def read_index(path: Path) -> pd.DataFrame:
    index = pd.read_excel(path, sheet_name="Index", header=9)
    index = index[
        index["Data Item Description"].notna() & index["Series ID"].notna()
    ].copy()
    parsed = index["Data Item Description"].astype(str).map(parse_description)
    index[["metric_label", "category", "geography"]] = pd.DataFrame(
        parsed.tolist(), index=index.index
    )
    index["measure"] = index["metric_label"].map(MEASURE_NAMES)
    return index


def food_categories(table3_index: pd.DataFrame) -> list[str]:
    mask = (
        (table3_index["metric_label"] == "Index Numbers")
        & (table3_index["geography"] == "Australia")
    )
    categories = table3_index.loc[mask, "category"].tolist()
    start = categories.index("Food and non-alcoholic beverages")
    end = categories.index("Alcohol and tobacco")
    return categories[start:end]


def extract_series(
    path: Path,
    selected_index: pd.DataFrame,
    source_table: str,
    source_url: str,
) -> pd.DataFrame:
    metadata = selected_index.set_index("Series ID").to_dict("index")
    selected_ids = set(metadata)
    records: list[pd.DataFrame] = []

    for sheet_name in pd.ExcelFile(path).sheet_names:
        if not sheet_name.startswith("Data"):
            continue
        sheet = pd.read_excel(path, sheet_name=sheet_name, header=None)
        dates = pd.to_datetime(sheet.iloc[10:, 0], errors="coerce")
        for column in range(1, sheet.shape[1]):
            series_id = str(sheet.iat[9, column]).strip()
            if series_id not in selected_ids:
                continue
            values = pd.to_numeric(sheet.iloc[10:, column], errors="coerce")
            meta = metadata[series_id]
            frame = pd.DataFrame(
                {
                    "date": dates,
                    "geography": meta["geography"],
                    "category": meta["category"],
                    "measure": meta["measure"],
                    "value": values,
                    "unit": meta["Unit"],
                    "series_id": series_id,
                    "source_table": source_table,
                    "source_url": source_url,
                }
            )
            records.append(frame.dropna(subset=["date", "value"]))

    if not records:
        raise RuntimeError(f"No selected series found in {path.name}")

    result = pd.concat(records, ignore_index=True)
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    return result.sort_values(
        ["date", "geography", "category", "measure"], ignore_index=True
    )


def build_abs_australia() -> pd.DataFrame:
    path = RAW_ABS / "640103.xlsx"
    index = read_index(path)
    categories = food_categories(index)
    selected = index[
        (index["geography"] == "Australia")
        & (index["category"].isin(categories))
        & (index["measure"].notna())
    ].copy()
    result = extract_series(
        path,
        selected,
        "ABS CPI Table 3",
        ABS_BASE_URL + "640103.xlsx",
    )
    result.insert(2, "category_order", result["category"].map({c: i + 1 for i, c in enumerate(categories)}))
    return result


def build_abs_cities() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for filename, table_name in [
        ("6401010.xlsx", "ABS CPI Table 10"),
        ("6401011.xlsx", "ABS CPI Table 11"),
    ]:
        path = RAW_ABS / filename
        index = read_index(path)
        selected = index[
            (index["geography"].isin(CITIES))
            & (index["category"] == "Food and non-alcoholic beverages")
            & (index["measure"].notna())
        ].copy()
        frames.append(
            extract_series(
                path,
                selected,
                table_name,
                ABS_BASE_URL + filename,
            )
        )
    result = pd.concat(frames, ignore_index=True)
    result.insert(2, "city_order", result["geography"].map({c: i + 1 for i, c in enumerate(CITIES)}))
    return result.sort_values(["date", "city_order", "measure"], ignore_index=True)


def build_choice_states() -> pd.DataFrame:
    prices = {
        "ACT": {"Aldi": 68.76, "Woolworths": 74.30, "Coles": 75.88, "IGA": 96.49},
        "NSW": {"Aldi": 68.76, "Woolworths": 74.28, "Coles": 75.96, "IGA": 88.98},
        "NT": {"Aldi": None, "Woolworths": 77.28, "Coles": 75.90, "IGA": 109.69},
        "QLD": {"Aldi": 67.88, "Woolworths": 72.56, "Coles": 76.08, "IGA": 94.35},
        "SA": {"Aldi": 69.06, "Woolworths": 73.53, "Coles": 76.33, "IGA": 95.91},
        "TAS": {"Aldi": None, "Woolworths": 75.95, "Coles": 77.24, "IGA": 99.53},
        "VIC": {"Aldi": 68.76, "Woolworths": 73.08, "Coles": 77.26, "IGA": 86.11},
        "WA": {"Aldi": 70.14, "Woolworths": 75.46, "Coles": 78.87, "IGA": 92.21},
    }
    records = []
    for state, supermarkets in prices.items():
        for supermarket, price in supermarkets.items():
            records.append(
                {
                    "survey_month": "2026-06-01",
                    "state": state,
                    "supermarket": supermarket,
                    "basket_price_aud": price,
                    "available": price is not None,
                    "basket_definition": "17-item basket with specials",
                    "stores_visited_nationally": 104,
                    "locations_nationally": 27,
                    "source_url": CHOICE_URL,
                }
            )
    return pd.DataFrame.from_records(records)


def validate(
    australia: pd.DataFrame,
    cities: pd.DataFrame,
    choice: pd.DataFrame,
) -> None:
    assert australia["category"].nunique() == 33
    assert set(australia["measure"].unique()) == set(MEASURE_NAMES.values())
    assert australia["date"].max() == "2026-08-01"
    assert cities["geography"].nunique() == 8
    assert set(cities["measure"].unique()) == {
        "index_number",
        "annual_percent_change",
    }
    latest_yoy = cities[
        (cities["date"] == "2026-08-01")
        & (cities["measure"] == "annual_percent_change")
    ]
    assert len(latest_yoy) == 8
    assert choice.shape[0] == 32
    assert choice["basket_price_aud"].isna().sum() == 2


def main() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    australia = build_abs_australia()
    cities = build_abs_cities()
    choice = build_choice_states()
    validate(australia, cities, choice)

    australia.to_csv(CLEAN / "abs_food_australia_monthly.csv", index=False)
    cities.to_csv(CLEAN / "abs_food_capital_city_monthly.csv", index=False)
    choice.to_csv(CLEAN / "choice_state_basket_jun2026.csv", index=False)

    print(
        {
            "abs_food_australia_monthly.csv": len(australia),
            "abs_food_capital_city_monthly.csv": len(cities),
            "choice_state_basket_jun2026.csv": len(choice),
        }
    )


if __name__ == "__main__":
    main()
