const savedTheme = localStorage.getItem("theme") || "light";
document.documentElement.dataset.theme = savedTheme;

document.addEventListener("click", async (event) => {
  const themeButton = event.target.closest("[data-theme-toggle]");
  if (themeButton) {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
    return;
  }

  const applyButton = event.target.closest("[data-apply]");
  if (!applyButton) return;

  event.preventDefault();
  applyButton.disabled = true;
  applyButton.textContent = "Enviando";

  try {
    const response = await fetch(`/postular/${applyButton.dataset.apply}`, {
      method: "POST",
      headers: { "X-Requested-With": "fetch" },
    });
    const data = await response.json();
    applyButton.textContent = data.ok ? "Postulado" : data.message || "No enviado";
    if (data.ok) {
      applyButton.classList.remove("btn-primary");
      applyButton.classList.add("btn-secondary");
    } else {
      applyButton.disabled = false;
    }
  } catch (_error) {
    applyButton.disabled = false;
    applyButton.textContent = "Reintentar";
  }
});

setTimeout(() => {
  document.querySelectorAll(".flash").forEach((el) => el.remove());
}, 4200);
