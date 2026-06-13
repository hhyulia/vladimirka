(function () {
  function enhancePasswordField(input) {
    if (!input || input.dataset.toggleReady === "1") return;
    input.dataset.toggleReady = "1";

    var wrapper = document.createElement("div");
    wrapper.style.display = "inline-flex";
    wrapper.style.alignItems = "center";
    wrapper.style.gap = "6px";

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "👁";
    btn.title = "Показать/скрыть пароль";
    btn.style.border = "1px solid #ccc";
    btn.style.background = "#fff";
    btn.style.cursor = "pointer";
    btn.style.padding = "4px 8px";
    btn.style.lineHeight = "1";
    btn.style.borderRadius = "4px";

    btn.addEventListener("click", function () {
      input.type = input.type === "password" ? "text" : "password";
    });

    wrapper.appendChild(btn);
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("input.js-password-field, input[type='password']").forEach(enhancePasswordField);
  });
})();
