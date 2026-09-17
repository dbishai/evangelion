(function () {
  "use strict";

  const PAGE_COUNT = 148;
  const PAGE_PREFIX = "pages/page-";
  const PAGE_SUFFIX = ".svg";

  // Same 24x34cm trim as the book itself (src/evangelion/layout.py).
  const ASPECT = 34 / 24;
  const BASE_WIDTH = 520;
  const BASE_HEIGHT = Math.round(BASE_WIDTH * ASPECT);

  function pad(n) {
    return String(n).padStart(3, "0");
  }

  function pageUrls() {
    const urls = [];
    for (let i = 1; i <= PAGE_COUNT; i++) {
      urls.push(PAGE_PREFIX + pad(i) + PAGE_SUFFIX);
    }
    return urls;
  }

  const bookEl = document.getElementById("book");
  const stageEl = document.querySelector(".book-stage");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const pageInput = document.getElementById("pageInput");
  const pageCountEl = document.getElementById("pageCount");
  const pageSlider = document.getElementById("pageSlider");
  const loadingEl = document.getElementById("loading");

  pageInput.max = String(PAGE_COUNT);
  pageSlider.max = String(PAGE_COUNT);
  pageCountEl.textContent = String(PAGE_COUNT);

  // StPageFlip's "stretch" size mode only fits the book to the container's
  // *width* -- it happily produces a page taller than the container, which
  // then gets clipped top and bottom by the page's own overflow:hidden.
  // Derive a tight max page width from the container's actual height (not
  // just an arbitrary large constant) so the computed page can never
  // exceed the space actually available, in either dimension.
  const stageRect = stageEl.getBoundingClientRect();
  const fitMaxWidth = Math.max(240, Math.min(1300, Math.floor(stageRect.height / ASPECT)));
  const fitMinWidth = Math.min(240, fitMaxWidth);

  const pageFlip = new St.PageFlip(bookEl, {
    width: BASE_WIDTH,
    height: BASE_HEIGHT,
    size: "stretch",
    minWidth: fitMinWidth,
    maxWidth: fitMaxWidth,
    minHeight: Math.round(fitMinWidth * ASPECT),
    maxHeight: Math.round(fitMaxWidth * ASPECT),
    maxShadowOpacity: 0.55,
    showCover: true,
    usePortrait: true,
    mobileScrollSupport: false,
    drawShadow: true,
    flippingTime: 700,
  });

  pageFlip.loadFromImages(pageUrls());

  // StPageFlip renders pages onto a <canvas>, sized to plain CSS pixels
  // with no regard for devicePixelRatio -- on any HiDPI display the
  // backing store is under-resolved and the browser upscales it, blurring
  // the fine serif text. Patch its internal canvas-sizing routine to
  // allocate a DPI-scaled backing store and scale the drawing context to
  // match, the standard fix for crisp canvas rendering on Retina displays.
  (function fixCanvasForHiDPI() {
    const ui = pageFlip.ui;
    if (!ui || typeof ui.resizeCanvas !== "function") return;
    ui.resizeCanvas = function () {
      const canvas = ui.getCanvas();
      const style = getComputedStyle(canvas);
      const cssWidth = parseInt(style.width, 10) || canvas.clientWidth || 1;
      const cssHeight = parseInt(style.height, 10) || canvas.clientHeight || 1;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.round(cssWidth * dpr));
      canvas.height = Math.max(1, Math.round(cssHeight * dpr));
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.scale(dpr, dpr);
    };
    ui.resizeCanvas();
  })();

  function syncControls(pageIndex) {
    const oneBased = pageIndex + 1;
    pageInput.value = String(oneBased);
    pageSlider.value = String(oneBased);
    prevBtn.disabled = oneBased <= 1;
    nextBtn.disabled = oneBased >= PAGE_COUNT;
  }

  pageFlip.on("init", (e) => {
    loadingEl.hidden = true;
    syncControls(e.data.page || 0);
  });

  pageFlip.on("flip", (e) => {
    syncControls(e.data);
  });

  prevBtn.addEventListener("click", () => pageFlip.flipPrev());
  nextBtn.addEventListener("click", () => pageFlip.flipNext());

  function goToPage(oneBased) {
    const clamped = Math.min(PAGE_COUNT, Math.max(1, Math.round(oneBased) || 1));
    pageFlip.flip(clamped - 1);
  }

  pageInput.addEventListener("change", () => goToPage(Number(pageInput.value)));
  pageSlider.addEventListener("input", () => goToPage(Number(pageSlider.value)));

  document.addEventListener("keydown", (e) => {
    if (e.target === pageInput) return;
    if (e.key === "ArrowRight") pageFlip.flipNext();
    if (e.key === "ArrowLeft") pageFlip.flipPrev();
  });
})();
