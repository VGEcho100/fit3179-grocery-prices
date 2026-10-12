# Vega-Lite specifications

Each visualisation used on the public page has a separate, human-readable Vega-Lite JSON specification in this directory.

1. [`01-trend.json`](01-trend.json) - selectable national food-price trend line.
2. [`02-streamgraph.json`](02-streamgraph.json) - food-category CPI contribution stream graph.
3. [`03-heatmap.json`](03-heatmap.json) - detailed category inflation heatmap.
4. [`04-bump-chart.json`](04-bump-chart.json) - annual inflation ranking changes.
5. [`05-lollipop.json`](05-lollipop.json) - latest detailed category changes.
6. [`06-boxplot.json`](06-boxplot.json) - monthly price-change distributions.
7. [`07-capital-map.json`](07-capital-map.json) - capital-city food inflation map.
8. [`08-basket-comparison.json`](08-basket-comparison.json) - state supermarket basket ranges.
9. [`09-slope-chart.json`](09-slope-chart.json) - Aldi and IGA basket comparison.
10. [`10-store-map.json`](10-store-map.json) - Greater Melbourne supermarket locations.
11. [`11-access-map.json`](11-access-map.json) - SA2 supermarkets per 10,000 residents.

The page loader in `../js/maps.js` fetches these files directly, so the specifications in this directory are the source of truth for the rendered charts.
