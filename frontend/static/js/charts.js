function renderBars(el, items) {
  if (!el) return;
  if (!items || !items.length) {
    el.innerHTML = "<p class='muted'>Sin datos para el gráfico.</p>";
    return;
  }
  const max = Math.max(...items.map((i) => Number(i.value) || 0), 1);
  el.innerHTML = items
    .map((item) => {
      const pct = Math.max(4, Math.round((Number(item.value) || 0) * 100 / max));
      const color = item.color || "#1f4454";
      return `<div class="bar-row"><span>${item.label}</span><div class="bar"><i style="width:${pct}%;background:${color}"></i></div><b>${item.value}</b></div>`;
    })
    .join("");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-bars]").forEach((el) => {
    try {
      renderBars(el, JSON.parse(el.getAttribute("data-bars") || "[]"));
    } catch (_err) {
      el.textContent = "No se pudo dibujar el gráfico.";
    }
  });
});
