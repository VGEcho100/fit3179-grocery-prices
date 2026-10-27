(() => {
  const nav = document.querySelector(".site-nav");
  const links = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'));
  const sections = Array.from(document.querySelectorAll("main > section[id]"));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!nav || links.length === 0 || sections.length === 0) {
    return;
  }

  const sectionGroups = new Map([
    ["trend", "trend"],
    ["composition", "composition"],
    ["categories", "categories"],
    ["rankings", "categories"],
    ["detail", "categories"],
    ["inflation", "categories"],
    ["basket", "basket"],
    ["retailer-gap", "basket"],
    ["stores", "stores"],
    ["access", "access"],
  ]);

  let updateRequested = false;
  let currentActive = null;

  function setActiveLink(sectionId) {
    if (sectionId === currentActive) {
      return;
    }

    currentActive = sectionId;
    links.forEach((link) => {
      const isActive = link.getAttribute("href") === `#${sectionId}`;
      link.classList.toggle("is-active", isActive);

      if (isActive) {
        link.setAttribute("aria-current", "location");
        link.scrollIntoView({
          behavior: reduceMotion ? "auto" : "smooth",
          block: "nearest",
          inline: "center",
        });
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function updateNavigation() {
    const marker = window.scrollY + nav.offsetHeight + Math.min(window.innerHeight * 0.3, 260);
    let activeGroup = null;

    sections.forEach((section) => {
      if (section.offsetTop <= marker) {
        activeGroup = sectionGroups.get(section.id) || activeGroup;
      }
    });

    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) {
      activeGroup = "access";
    }

    nav.classList.toggle("is-scrolled", window.scrollY > 8);
    setActiveLink(activeGroup);
    updateRequested = false;
  }

  function requestUpdate() {
    if (!updateRequested) {
      updateRequested = true;
      window.requestAnimationFrame(updateNavigation);
    }
  }

  links.forEach((link) => {
    link.addEventListener("click", () => {
      setActiveLink(link.getAttribute("href").slice(1));
    });
  });

  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", requestUpdate);
  window.addEventListener("pageshow", requestUpdate);
  requestUpdate();
})();
