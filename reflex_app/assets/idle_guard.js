(function () {
  "use strict";

  // Cloud Run bills for as long as this tab keeps the Reflex WebSocket alive
  // and reconnecting (it force-reconnects every ~5min on the server's request
  // timeout). An idle tab left open all day pins a billed instance with nobody
  // there. After IDLE_MS with no input, navigate away entirely — that's what
  // actually closes the socket and lets the instance scale down — to a static
  // page with no Reflex/socket of its own. See assets/paused.html.
  //
  // Yvynation runs real multi-minute background jobs (batch territory runs,
  // map/timeline builds — AppState.idle_guard_busy in state/__init__.py) that
  // must NOT be interrupted just because the user stepped away to watch them
  // finish. #idle-guard-marker's data-busy attribute (rendered reactively in
  // pages/index.py) is checked before ever pausing; while busy we just defer
  // and re-check on the next timeout instead of disconnecting.
  var IDLE_MS = 10 * 60 * 1000;
  var timer = null;

  function isBusy() {
    var marker = document.getElementById("idle-guard-marker");
    return !!marker && marker.getAttribute("data-busy") === "true";
  }

  function pause() {
    if (isBusy()) {
      reset();
      return;
    }
    try {
      sessionStorage.setItem("idle_guard_resume_url", window.location.href);
    } catch (e) {
      /* sessionStorage unavailable (private mode etc.) — resume falls back to "/" */
    }
    window.location.href = "/assets/paused.html";
  }

  function reset() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(pause, IDLE_MS);
  }

  [
    "mousemove",
    "mousedown",
    "keydown",
    "touchstart",
    "wheel",
    "scroll",
  ].forEach(function (evt) {
    document.addEventListener(evt, reset, { passive: true, capture: true });
  });

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") reset();
  });

  reset();
})();
