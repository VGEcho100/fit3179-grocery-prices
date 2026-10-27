(() => {
  const status = document.querySelector("#price-band-chart-status");
  const scrolly = document.querySelector("#price-band-scrolly");

  if (!status || !scrolly) {
    return;
  }

  // Scroll-driven highlighting: each step card sets the Vega-Lite params that
  // decide which pills keep their colour. Everything else is dimmed.
  const steps = Array.from(scrolly.querySelectorAll(".price-band-step"));
  const scrollyQuery = window.matchMedia("(min-width: 901px) and (min-height: 500px)");
  let view = null;
  let activeStep = null;
  let updateRequested = false;

  function applyHighlight(step) {
    steps.forEach((item) => item.classList.toggle("is-active", item === step));

    if (!view) {
      return;
    }

    view
      .signal("focusBands", step ? step.dataset.bands || "" : "all")
      .signal("focusFoods", step ? step.dataset.foods || "" : "")
      .runAsync();
  }

  function updateScrolly() {
    updateRequested = false;

    if (!scrolly.classList.contains("is-scrolly")) {
      return;
    }

    const midline = window.innerHeight * 0.5;
    let nextStep = null;

    steps.forEach((step) => {
      if (step.getBoundingClientRect().top < midline) {
        nextStep = step;
      }
    });

    // Once the last card nears the top of the screen, show every band again.
    if (nextStep === steps[steps.length - 1] && nextStep.getBoundingClientRect().bottom < midline * 0.6) {
      nextStep = null;
    }

    if (nextStep !== activeStep) {
      activeStep = nextStep;
      applyHighlight(activeStep);
    }
  }

  function requestUpdate() {
    if (!updateRequested) {
      updateRequested = true;
      window.requestAnimationFrame(updateScrolly);
    }
  }

  function setScrollyMode() {
    scrolly.classList.toggle("is-scrolly", scrollyQuery.matches);

    if (!scrollyQuery.matches) {
      activeStep = null;
      applyHighlight(null);
    }

    requestUpdate();
  }

  document.fonts.ready
    .then(() =>
      vegaEmbed("#price-band-chart", "specs/05-price-bands.json", {
        actions: false,
        renderer: "svg",
        tooltip: { theme: "light" },
      }),
    )
    .then((result) => {
      view = result.view;
      status.textContent = "";
      applyHighlight(activeStep);
    })
    .catch((error) => {
      console.error(error);
      status.textContent = "The price-band view could not be loaded.";
    });

  if (steps.length > 0) {
    scrollyQuery.addEventListener("change", setScrollyMode);
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate);
    setScrollyMode();
  }
})();
