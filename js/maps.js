const visualisations = [
  ["#trend-chart", "#trend-chart-status", "specs/01-trend.json"],
  ["#stream-chart", "#stream-chart-status", "specs/02-stacked-area.json"],
  ["#category-heatmap", "#category-heatmap-status", "specs/03-heatmap.json"],
  ["#bump-chart", "#bump-chart-status", "specs/04-bump-chart.json?v=17"],
  ["#volatility-chart", "#volatility-chart-status", "specs/06-monthly-movement.json"],
  ["#capital-map", "#capital-map-status", "specs/07-capital-map.json"],
  ["#basket-chart", "#basket-chart-status", "specs/08-basket-comparison.json"],
  ["#slope-chart", "#slope-chart-status", "specs/09-slope-chart.json"],
  ["#store-map", "#store-map-status", "specs/10-store-map.json"],
  ["#access-map", "#access-map-status", "specs/11-access-map.json"],
];

async function loadSpec(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not load ${url}: HTTP ${response.status}`);
  }
  return response.json();
}

async function embedChart(selector, statusSelector, specUrl) {
  const status = document.querySelector(statusSelector);

  try {
    const spec = await loadSpec(specUrl);
    await vegaEmbed(selector, spec, {
      actions: false,
      renderer: "svg",
      tooltip: { theme: "light" },
    });
    status.textContent = "";
  } catch (error) {
    console.error(error);
    status.textContent =
      "The visualisation could not be loaded. Run this page through a local web server and check the data and specification paths.";
  }
}

Promise.all(
  visualisations.map(([selector, statusSelector, specUrl]) =>
    embedChart(selector, statusSelector, specUrl),
  ),
);
