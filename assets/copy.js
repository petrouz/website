(function () {
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-copy]");
    if (!btn) return;
    var target = document.querySelector(btn.getAttribute("data-copy"));
    if (!target) return;
    var text = target.textContent.trim();
    navigator.clipboard.writeText(text).then(function () {
      var label = btn.querySelector(".copy-label");
      if (!label) return;
      var prev = label.textContent;
      label.textContent = "Copied";
      setTimeout(function () {
        label.textContent = prev || "Copy";
      }, 1600);
    });
  });
})();
