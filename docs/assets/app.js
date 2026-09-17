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

  // StPageFlip's loadFromImages() is not lazy -- it does `new Image(); img.src
  // = url` for every page in the array immediately, so passing all 148 real
  // SVGs up front fetches and decodes the entire ~28MB book at once. Instead,
  // only give it real URLs for a window of pages around the one currently
  // shown; every other slot gets a tiny blank placeholder. As the reader
  // flips, updateFromImages() swaps in a re-centered window, so only a
  // bounded number of pages are ever resident in memory at a time.
  const WINDOW_RADIUS = 8;
  const RECENTER_THRESHOLD = 4;

  const PLACEHOLDER_SVG =
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 240 340'%3E%3Crect width='240' height='340' fill='%23fdfbf7'/%3E%3C/svg%3E";

  function pageUrl(oneBasedIndex) {
    return PAGE_PREFIX + pad(oneBasedIndex) + PAGE_SUFFIX;
  }

  function urlsForWindow(centerIndex) {
    const urls = [];
    for (let i = 0; i < PAGE_COUNT; i++) {
      urls.push(Math.abs(i - centerIndex) <= WINDOW_RADIUS ? pageUrl(i + 1) : PLACEHOLDER_SVG);
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

  let loadedCenter = 0;
  pageFlip.loadFromImages(urlsForWindow(loadedCenter));

  let recenterTimer = null;
  function ensureWindowLoaded(centerIndex) {
    if (Math.abs(centerIndex - loadedCenter) < RECENTER_THRESHOLD) return;
    loadedCenter = centerIndex;
    clearTimeout(recenterTimer);
    recenterTimer = setTimeout(() => {
      pageFlip.updateFromImages(urlsForWindow(loadedCenter));
    }, 150);
  }

  // StPageFlip renders pages onto a <canvas>, sized to plain CSS pixels
  // with no regard for devicePixelRatio -- on any HiDPI display the
  // backing store is under-resolved and the browser upscales it, blurring
  // the fine serif text. Patch its internal canvas-sizing routine to
  // allocate a DPI-scaled backing store and scale the drawing context to
  // match, the standard fix for crisp canvas rendering on Retina displays.
  (function fixCanvasForHiDPI() {
    const ui = pageFlip.ui;
    if (!ui || typeof ui.resizeCanvas !== "function") return;
    // Cap at 2x: iPhones report a devicePixelRatio of 3, and a naive 3x
    // backing store (9x the pixel count of a 1x canvas) on a 150-plus page
    // book was enough to exhaust Mobile Safari's per-tab memory budget and
    // crash the page ("A problem repeatedly occurred") once flipping
    // started re-triggering resizes. 2x is still fully sharp at this page
    // size and keeps memory in check.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    ui.resizeCanvas = function () {
      const canvas = ui.getCanvas();
      const style = getComputedStyle(canvas);
      const cssWidth = parseInt(style.width, 10) || canvas.clientWidth || 1;
      const cssHeight = parseInt(style.height, 10) || canvas.clientHeight || 1;
      const targetWidth = Math.max(1, Math.round(cssWidth * dpr));
      const targetHeight = Math.max(1, Math.round(cssHeight * dpr));
      // Setting canvas.width/height -- even to its current value -- clears
      // and reallocates the whole backing store. StPageFlip's own resize
      // listener can fire repeatedly in quick succession (e.g. Mobile
      // Safari's chrome bar resizing the viewport while a page is being
      // dragged), so skip the reallocation entirely when nothing changed.
      if (canvas.width === targetWidth && canvas.height === targetHeight) return;
      canvas.width = targetWidth;
      canvas.height = targetHeight;
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
    ensureWindowLoaded(e.data);
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
