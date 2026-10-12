# Grocery Prices - verified data sources

Checked: 11 October 2026

## Recommended scope

Use a national-to-local story:

1. Australian food inflation over time and by food category.
2. Supermarket basket prices by chain and state/territory.
3. Greater Melbourne as a local case study of supermarket access and household resources.

This scope supports a national audience while keeping the detailed map files small enough for GitHub Pages.

## 1. ABS Consumer Price Index - core time-series source

Landing page:
https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release

Current reference period: August 2026, released 30 September 2026.

Recommended downloads:

- Table 3 - group, subgroup and expenditure-class series, weighted average of eight capital cities:
  https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/aug-2026/640103.xlsx
- Table 10 - group, subgroup and expenditure-class index numbers by capital city:
  https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/aug-2026/6401010.xlsx
- Table 11 - annual percentage change by capital city:
  https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/aug-2026/6401011.xlsx

Useful fields/series:

- Food and non-alcoholic beverages
- Bread and cereal products
- Meat and seafoods
- Dairy and related products
- Fruit and vegetables
- Food products n.e.c.
- Non-alcoholic beverages
- Meals out and takeaway foods
- Period, index number, monthly percentage change, annual percentage change, capital city

Best uses: indexed line chart, category heatmap, bump chart, slope chart, treemap/contribution chart, capital-city graduated-symbol map.

Important limitation: CPI measures price change, not the dollar price of a household's actual shopping basket.

## 2. CHOICE supermarket basket survey - supermarket and state comparison

Article and accessible data table:
https://www.choice.com.au/shopping/everyday-shopping/supermarkets/articles/cheapest-groceries-australia

Reference period: June 2026; page updated 24 September 2026.

Coverage:

- 104 supermarkets in 27 locations
- 27 Woolworths, 27 Coles, 23 Aldi and 27 IGA stores
- Full basket: 17 items, including 8 fresh and 9 packaged items
- National basket prices with and without specials
- State/territory basket prices with specials for each available chain
- Base basket prices and change from the March survey

Best uses: chain comparison dot plot, with/without-specials dumbbell plot, state-by-chain heatmap, state basket-price map.

Important limitations:

- The page is an accessible published table, not a downloadable raw research dataset.
- Some state/chain combinations are unavailable because Aldi does not operate in every jurisdiction.
- Recreate charts from the reported values and cite CHOICE; do not copy CHOICE's graphics.

## 3. ABS SA2 income web service - local affordability context

Feature layer:
https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/arcgis/rest/services/SA2_income_DbR_Nov25/FeatureServer/0

Recommended field:

- `equiv_22021`: median equivalised total household income per week, 2021
- `sa2_code_2021`, `sa2_name_2021`, `gccsa_name_2021`

Best use: Greater Melbourne choropleth or bivariate map. Use the SA2 code as the join key.

## 4. ABS regional population 2025 - denominator for access measures

Feature service:
https://geo.abs.gov.au/arcgis/rest/services/Hosted/SA2_Regional_Population_2025/FeatureServer/3

Recommended fields:

- `sa2_code_2021`, `sa2_name_2021`, `gccsa_name_2021`
- `erp_2025`: estimated resident population at 30 June 2025
- `area_km2`
- `pop_density_2025_people_per_km2`

Derived measure:

`supermarkets_per_10000 = supermarket_count / erp_2025 * 10000`

Best use: supermarket-access choropleth and tooltip context.

## 5. ABS SA2 boundaries - lightweight geometry

Generalised SA2 layer (prefer this over the full-resolution layer for a web page):
https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/FeatureServer/1

Filter to `gccsa_code_2021 = '2GMEL'` or `gccsa_name_2021 = 'Greater Melbourne'`, request GeoJSON in WGS84, and retain only SA2 code/name fields. Simplify further if the result remains large.

## 6. OpenStreetMap - supermarket locations

Tag definition:
https://wiki.openstreetmap.org/wiki/Tag%3Ashop%3Dsupermarket

Overpass Turbo:
https://overpass-turbo.eu/

Suggested query:

```overpass
[out:json][timeout:120];
{{geocodeArea:Greater Melbourne, Victoria, Australia}}->.searchArea;
nwr["shop"="supermarket"](area.searchArea);
out center tags;
```

Export the result as GeoJSON. Retain `name`, `brand`, `operator`, longitude and latitude; normalise only the major brand names needed for the story.

Required attribution: `© OpenStreetMap contributors, ODbL` with a link to https://www.openstreetmap.org/copyright

Important limitation: OpenStreetMap is community-maintained, so missing or inconsistent brand/name tags must be acknowledged.

## Recommended three different map idioms

1. Graduated-symbol map: food inflation by the eight capital cities, using ABS CPI Table 11.
2. Point/density map: supermarket locations and brand concentration in Greater Melbourne, using OpenStreetMap.
3. Choropleth map: supermarkets per 10,000 residents by SA2, joining OpenStreetMap counts to ABS 2025 population.

Optional fourth map: bivariate choropleth combining low supermarket access with low equivalised household income.

## Prepared clean outputs

- `data/clean/abs_food_australia_monthly.csv`: 33 food categories from ABS Table 3, in long format. Measures include index number, monthly and annual percentage change, contribution to the All groups CPI index, and change in contribution. Coverage is September 2017 to August 2026 where each series is available.
- `data/clean/abs_food_capital_city_monthly.csv`: the overall Food and non-alcoholic beverages group for all eight capital cities, combining Table 10 index numbers and Table 11 annual percentage changes. Coverage is April 2024 to August 2026 where each series is available.
- `data/clean/choice_state_basket_jun2026.csv`: June 2026 state-level prices for Aldi, Woolworths, Coles and IGA for the 17-item basket with specials. Aldi is explicitly marked unavailable in the Northern Territory and Tasmania.

The reproducible cleaning script is `scripts/prepare_grocery_data.py`. It keeps ABS series IDs and source URLs in every output row.

## Prepared spatial outputs

The two spatial outputs are now prepared:

- `data/clean/supermarkets_greater_melbourne.geojson`: 1,038 supermarket point features inside the official Greater Melbourne SA2 boundary. It includes the original OSM element ID and URL, name, raw brand/operator tags, a normalised brand group, coordinates and assigned SA2 code/name.
- `data/clean/sa2_greater_melbourne.geojson`: 361 simplified SA2 polygons joined to 2025 population, 2021 median equivalised household income, supermarket counts, brand counts and supermarkets per 10,000 residents.

The OSM query first retrieved 1,137 `shop=supermarket` elements from a bounding box around Melbourne. The spatial cleaning retained 1,039 elements inside Greater Melbourne and removed one duplicate node/building representation of the same Woolworths, leaving 1,038 stores. OSM data timestamp: 11 October 2026 05:43 UTC.

To prevent non-residential special-purpose SA2s from dominating the colour scale, `supermarkets_per_10000` is left null when 2025 population is below 1,000. The original population and store count remain available, and `access_rate_status` explains the exclusion. This affects seven SA2s, including airport and racecourse areas.

The reproducible spatial cleaning script is `scripts/prepare_melbourne_spatial_data.py`. It uses the original ABS polygons for point-in-polygon assignment and simplifies geometry only for the final web map.

## Sources to avoid as core evidence

- Kaggle files without a clear original source or licence
- Undocumented Coles/Woolworths APIs or large-scale scraping
- One-off online price snapshots presented as historical trends
- The 2015-16 Household Expenditure Survey as the main current-price source

