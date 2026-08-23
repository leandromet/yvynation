/**
 * Yvynation – HydrateFallback loading overlay.
 *
 * Creates a full-screen spinner that is visible during the JS-module-load /
 * hydration phase and fades out once React has mounted.  This directly
 * addresses the React Router 7 "💿 Hey developer" HydrateFallback hint.
 *
 * Served from /assets/yvy-loading.js and injected via <script src="…"> so
 * React never HTML-escapes the contents (unlike an inline text child).
 */
(function () {
  var CSS = [
    "#yvy-loading{position:fixed;inset:0;display:flex;flex-direction:column;",
    "align-items:center;justify-content:center;",
    "background:linear-gradient(135deg,#f0fdf4 0%,#eff6ff 100%);",
    "z-index:99999;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;",
    "transition:opacity .4s ease}",
    "#yvy-loading.out{opacity:0;pointer-events:none}",
    ".yvy-ring{width:52px;height:52px;border:5px solid #bbf7d0;",
    "border-top-color:#16a34a;border-radius:50%;",
    "animation:yvy-spin .9s linear infinite;margin-bottom:1rem}",
    "@keyframes yvy-spin{to{transform:rotate(360deg)}}",
    ".yvy-h{font-size:1.4rem;font-weight:700;color:#166534;margin:0}",
    ".yvy-s{font-size:.85rem;color:#6b7280;margin-top:.4rem}"
  ].join("");

  var style = document.createElement("style");
  style.textContent = CSS;
  document.head.appendChild(style);

  function createOverlay() {
    var el = document.createElement("div");
    el.id = "yvy-loading";
    el.innerHTML = (
      '<div class="yvy-ring"></div>' +
      '<p class="yvy-h">Yvynation</p>' +
      '<p class="yvy-s">Loading indigenous land monitor…</p>'
    );
    document.body.appendChild(el);
    return el;
  }

  function waitForReact(el) {
    // Reflex mounts into a div with id "app" or "__next"
    function check() {
      var root = (
        document.getElementById("app") ||
        document.getElementById("__next") ||
        document.querySelector("[data-reactroot]")
      );
      if (root && root.childElementCount > 0) {
        el.classList.add("out");
        setTimeout(function () {
          if (el.parentNode) el.parentNode.removeChild(el);
        }, 450);
      } else {
        requestAnimationFrame(check);
      }
    }
    requestAnimationFrame(check);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      waitForReact(createOverlay());
    });
  } else {
    waitForReact(createOverlay());
  }
})();
