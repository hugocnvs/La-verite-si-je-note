const debounce = (fn, delay = 250) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((flash, index) => {
    flash.style.animationDelay = `${index * 100}ms`;
    setTimeout(() => flash.classList.add("hide"), 5000);
  });

  const filtersForm = document.getElementById("filters-form");
  const filmsGrid = document.getElementById("films-grid");
  if (filtersForm && filmsGrid) {
    const runSearch = debounce(() => {
      const formData = new FormData(filtersForm);
      const params = new URLSearchParams(formData);
      fetch(`/films/partial?${params.toString()}`, {
        headers: { "X-Requested-With": "fetch" },
      })
        .then((response) => response.text())
        .then((html) => {
          filmsGrid.innerHTML = html;
        })
        .catch(() => {
          // Échec silencieux pour éviter de bloquer l'expérience utilisateur
        });
    }, 250);

    filtersForm.addEventListener("input", runSearch);
    filtersForm.addEventListener("change", runSearch);
  }
});

