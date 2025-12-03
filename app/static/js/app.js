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

  // Dropdown tags avec checkboxes
  const tagsToggle = document.getElementById("tags-toggle");
  const tagsMenu = document.getElementById("tags-menu");
  
  if (tagsToggle && tagsMenu) {
    // Toggle du menu
    tagsToggle.addEventListener("click", (e) => {
      e.preventDefault();
      tagsToggle.classList.toggle("open");
      tagsMenu.classList.toggle("open");
    });

    // Fermer le menu si on clique ailleurs
    document.addEventListener("click", (e) => {
      if (!tagsToggle.contains(e.target) && !tagsMenu.contains(e.target)) {
        tagsToggle.classList.remove("open");
        tagsMenu.classList.remove("open");
      }
    });

    // Mettre à jour le texte du bouton quand on coche/décoche
    const updateToggleText = () => {
      const checked = tagsMenu.querySelectorAll('input[type="checkbox"]:checked');
      const textSpan = tagsToggle.querySelector(".dropdown-text");
      if (checked.length > 0) {
        textSpan.textContent = `${checked.length} tag(s) sélectionné(s)`;
      } else {
        textSpan.textContent = "Sélectionner des tags";
      }
    };

    tagsMenu.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
      checkbox.addEventListener("change", updateToggleText);
    });

    // Boutons tout sélectionner / désélectionner
    const selectAllBtn = document.getElementById("select-all-tags");
    const deselectAllBtn = document.getElementById("deselect-all-tags");

    if (selectAllBtn) {
      selectAllBtn.addEventListener("click", () => {
        tagsMenu.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
          cb.checked = true;
        });
        updateToggleText();
        // Déclencher la recherche
        filtersForm?.dispatchEvent(new Event("change"));
      });
    }

    if (deselectAllBtn) {
      deselectAllBtn.addEventListener("click", () => {
        tagsMenu.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
          cb.checked = false;
        });
        updateToggleText();
        // Déclencher la recherche
        filtersForm?.dispatchEvent(new Event("change"));
      });
    }
  }
});

