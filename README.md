# Grocery prices visualisation prototype

This folder contains eleven linked Vega-Lite visualisations for the FIT3179 Data Visualisation 2 project:

1. Selectable line chart of annual food price change since September 2018.
2. 100% stacked area chart of broad food-category shares of CPI contribution.
3. Heatmap of monthly inflation across 11 everyday food categories.
4. Bump chart ranking broad categories by annual inflation each August.
5. Lollipop chart of the latest annual change for detailed categories.
6. Ranked horizontal bars showing the average size of monthly price changes since September 2023.
7. Graduated-symbol map of annual food inflation across eight capital cities.
8. Range-and-dot comparison of supermarket basket prices by state.
9. Slope graph comparing Aldi and IGA basket prices by state.
10. Point map of supermarket locations and brand groups in Greater Melbourne.
11. SA2 choropleth of supermarkets per 10,000 residents.

From this directory, preview the page with a local HTTP server:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000/`. Opening `index.html` directly may block local CSV and GeoJSON requests.

The page uses Vega 6.4.0, Vega-Lite 6.5.0 and Vega-Embed 7.3.0 from jsDelivr. Data preparation scripts and source notes are in `scripts/` and `DATA_SOURCES.md`.

The human-readable Vega-Lite JSON descriptions are indexed in [`specs/README.md`](specs/README.md). The page loads these JSON files directly through `js/maps.js`, so the repository specifications and the rendered visualisations stay in sync.
