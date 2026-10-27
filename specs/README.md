# Vega-Lite specifications

Each visualisation used on the public page has a separate, human-readable Vega-Lite JSON specification in this directory.

1. [`01-trend.json`](01-trend.json) - selectable national food-price trend line.
2. [`02-waffle.json`](02-waffle.json) - August 2026 food-category shares of CPI contribution as a waffle chart, split into eating out and groceries.
3. [`03-heatmap.json`](03-heatmap.json) - detailed category inflation heatmap.
4. [`04-bump-chart.json`](04-bump-chart.json) - annual inflation ranking changes.
5. [`05-price-bands.json`](05-price-bands.json) - August 2026 detailed foods grouped into annual price-change bands, with scroll-driven highlighting.
6. [`06-monthly-movement.json`](06-monthly-movement.json) - average absolute monthly price movement by category.
7. [`07-capital-map.json`](07-capital-map.json) - capital-city food inflation map.
8. [`08-basket-comparison.json`](08-basket-comparison.json) - state supermarket basket ranges.
9. [`09-slope-chart.json`](09-slope-chart.json) - Aldi and IGA basket comparison.
10. [`10-store-map.json`](10-store-map.json) - Greater Melbourne supermarket locations.
11. [`11-access-map.json`](11-access-map.json) - SA2 supermarkets per 10,000 residents.

The page loader in `../js/maps.js` fetches these files directly, so the specifications in this directory are the source of truth for the rendered charts.
