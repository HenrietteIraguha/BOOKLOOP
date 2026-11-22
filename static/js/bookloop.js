(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Numbers count up when the page loads
  document.querySelectorAll("[data-count]").forEach(function (el) {
    var target = parseInt(el.dataset.count, 10) || 0;
    if (reduce || target === 0) return;
    var start = null;
    function step(t) {
      if (!start) start = t;
      var p = Math.min((t - start) / 1200, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    }
    el.textContent = "0";
    requestAnimationFrame(step);
  });

  // "Donate in 2 minutes" panel: choices fill the link to the form
  var go = document.getElementById("quick-go");
  if (go) {
    var chosen = { n: "5", lang: "en" };
    var update = function () {
      go.href = go.dataset.base + "?n=" + chosen.n + "&lang=" + chosen.lang;
      var n = parseInt(chosen.n, 10);
      document.getElementById("impact").textContent = n >= 40 ? "more than 30 children" : "about " + n + " children";
    };
    document.querySelectorAll(".choices").forEach(function (group) {
      group.addEventListener("click", function (e) {
        var btn = e.target.closest(".choice");

        if (!btn) return;
        group.querySelectorAll(".choice").forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        chosen[group.dataset.group] = btn.dataset.value;
        update();
      });
    });
    update();
  }

  // Slideshow of donated books
  var track = document.getElementById("track");
  if (!track || !track.children.length) return;
  var viewport = document.getElementById("viewport");
  var dotsBox = document.getElementById("dots");
  var arrows = document.getElementById("arrows");
  var books = track.children;
  var index = 0, timer = null;

  function perView() { var w = window.innerWidth; return w <= 560 ? 1 : w <= 920 ? 2 : 4; }
  function pages() { return Math.max(1, books.length - perView() + 1); }
  function render() {
    var card = books[0].getBoundingClientRect().width + 20;
    track.style.transform = "translateX(" + (-index * card) + "px)";
    dotsBox.querySelectorAll("button").forEach(function (d, i) {
      d.setAttribute("aria-current", i === index ? "true" : "false");
    });
  }
  function goTo(i) { index = (i + pages()) % pages(); render(); }
  function build() {
    dotsBox.innerHTML = "";

    var many = pages() > 1;
    arrows.hidden = !many;
    dotsBox.hidden = !many;
    for (var i = 0; i < pages(); i++) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", "Show from book " + (i + 1));
      b.addEventListener("click", goTo.bind(null, i));
      dotsBox.appendChild(b);
    }
    if (index > pages() - 1) index = pages() - 1;
    render();
  }
  function play() { pause(); if (!reduce && pages() > 1) timer = setInterval(function () { goTo(index + 1); }, 4500); }
  function pause() { clearInterval(timer); }

  document.getElementById("prev").addEventListener("click", function () { goTo(index - 1); });
  document.getElementById("next").addEventListener("click", function () { goTo(index + 1); });
  viewport.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") goTo(index - 1);
    if (e.key === "ArrowRight") goTo(index + 1);
  });
  var sx = null;
  viewport.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; pause(); }, { passive: true });
  viewport.addEventListener("touchend", function (e) {
    if (sx === null) return;
    var dx = e.changedTouches[0].clientX - sx;
    if (Math.abs(dx) > 40) goTo(index + (dx < 0 ? 1 : -1));
    sx = null;
    play();
  });
  [viewport, arrows].forEach(function (el) {

    el.addEventListener("mouseenter", pause);
    el.addEventListener("mouseleave", play);
    el.addEventListener("focusin", pause);
  });
  window.addEventListener("resize", build);
  build();
  play();
})();
