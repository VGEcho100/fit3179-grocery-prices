(() => {
  const chart = document.querySelector("#price-band-chart");
  const status = document.querySelector("#price-band-chart-status");

  if (!chart || !status) {
    return;
  }

  const excludedCategories = new Set([
    "Food and non-alcoholic beverages",
    "Bread and cereal products",
    "Meat and seafoods",
    "Dairy and related products",
    "Fruit and vegetables",
    "Food products n.e.c.",
    "Meals out and take away foods",
    "Non-alcoholic beverages",
  ]);

  const bands = [
    {
      key: "falling",
      title: "Prices fell",
      range: "Below 0%",
      includes: (value) => value < 0,
    },
    {
      key: "steady",
      title: "Small change",
      range: "0–2%",
      includes: (value) => value >= 0 && value < 2,
    },
    {
      key: "rising",
      title: "Moderate rise",
      range: "2–5%",
      includes: (value) => value >= 2 && value < 5,
    },
    {
      key: "fast",
      title: "Fastest rise",
      range: "5% or more",
      includes: (value) => value >= 5,
    },
  ];

  function makePill(row, bandKey) {
    const item = document.createElement("li");
    const direction = row.value < 0 ? "fell" : "rose";
    const value = Math.abs(row.value).toFixed(1);

    item.className = `price-pill price-pill--${bandKey}`;
    item.tabIndex = 0;
    item.textContent = row.category;
    item.dataset.tooltip = `${direction} ${value}%`;
    item.setAttribute("aria-label", `${row.category}: ${direction} ${value}%`);
    return item;
  }

  function render(rows) {
    const grid = document.createElement("div");
    grid.className = "price-band-grid";

    bands.forEach((band) => {
      const group = document.createElement("section");
      const heading = document.createElement("h4");
      const title = document.createElement("strong");
      const range = document.createElement("span");
      const list = document.createElement("ul");
      const matches = rows
        .filter((row) => band.includes(row.value))
        .sort((a, b) => b.value - a.value);

      group.className = "price-bin";
      heading.className = "price-bin-heading";
      title.textContent = band.title;
      range.textContent = `${band.range} · ${matches.length} foods`;
      list.className = "price-pill-list";

      heading.append(title, range);
      matches.forEach((row) => list.append(makePill(row, band.key)));
      group.append(heading, list);
      grid.append(group);
    });

    chart.replaceChildren(grid);
    status.textContent = "";
  }

  fetch("data/clean/abs_food_australia_monthly.csv")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Could not load price data: HTTP ${response.status}`);
      }
      return response.text();
    })
    .then((text) => vega.read(text, { type: "csv", parse: { value: "number" } }))
    .then((rows) =>
      rows.filter(
        (row) =>
          row.measure === "annual_percent_change" &&
          row.date === "2026-08-01" &&
          !excludedCategories.has(row.category),
      ),
    )
    .then(render)
    .catch((error) => {
      console.error(error);
      status.textContent = "The price-band view could not be loaded.";
    });
})();
