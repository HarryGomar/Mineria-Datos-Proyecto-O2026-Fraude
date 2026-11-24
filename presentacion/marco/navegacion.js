(() => {
  const stage = document.querySelector(".stage");
  const slides = [...stage.children];
  const notes = JSON.parse(document.getElementById("datos-notas").textContent);
  const notesPanel = document.getElementById("texto-notas");
  const notesButton = document.getElementById("notas");
  const previous = document.getElementById("anterior");
  const next = document.getElementById("siguiente");
  const modal = document.querySelector(".overview");
  const grid = modal.querySelector(".overview-grid");
  const status = document.getElementById("estado");
  let active = 0;
  let touchStart = null;
  let controlsTimer;
  const talkLength = slides.filter(slide => !slide.classList.contains("appendix")).length;

  function resize() {
    stage.style.setProperty("--zoom", Math.min(innerWidth / stage.offsetWidth, innerHeight / stage.offsetHeight));
    for (const thumbnail of grid.querySelectorAll(".thumbnail")) {
      thumbnail.style.setProperty("--thumb-scale", thumbnail.clientWidth / stage.offsetWidth);
    }
  }

  function showControls() {
    document.body.classList.add("show-controls");
    clearTimeout(controlsTimer);
    controlsTimer = setTimeout(() => document.body.classList.remove("show-controls"), 2600);
  }

  function fromHash() {
    const index = Number(location.hash.slice(1));
    return Number.isInteger(index) ? index - 1 : 0;
  }

  function go(index) {
    active = Math.min(slides.length - 1, Math.max(0, index));
    slides.forEach((slide, position) => {
      slide.classList.toggle("active", position === active);
      slide.setAttribute("aria-hidden", String(position !== active));
    });
    const hash = "#" + (active + 1);
    if (location.hash !== hash) history.replaceState(null, "", hash);
    previous.disabled = active === 0;
    next.disabled = active === slides.length - 1;
    status.textContent = slides[active].dataset.title;
    const note = notes[active];
    const title = document.createElement("b");
    title.textContent = note.heading;
    const paragraph = document.createElement("p");
    paragraph.textContent = note.text;
    notesPanel.replaceChildren(title, paragraph);
  }

  function overview() {
    if (modal.open) {
      modal.close();
      return;
    }
    if (!grid.childElementCount) {
      slides.forEach((slide, index) => {
        const button = document.createElement("button");
        const thumbnail = document.createElement("span");
        thumbnail.className = "thumbnail";
        const preview = slide.cloneNode(true);
        preview.classList.remove("active");
        preview.classList.add("miniature");
        preview.setAttribute("aria-hidden", "true");
        thumbnail.appendChild(preview);
        const label = document.createElement("span");
        label.className = "thumbnail-label";
        label.textContent = (index + 1) + " · " + slide.dataset.title;
        button.append(thumbnail, label);
        button.addEventListener("click", () => {
          modal.close();
          go(index);
        });
        grid.appendChild(button);
      });
    }
    [...grid.children].forEach((button, index) => button.setAttribute("aria-current", String(index === active)));
    modal.showModal();
    resize();
    grid.children[active].focus();
  }

  function toggleNotes() {
    notesPanel.hidden = !notesPanel.hidden;
    notesButton.setAttribute("aria-pressed", String(!notesPanel.hidden));
  }

  async function fullscreen() {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  }

  slides.forEach((slide, index) => {
    if (!index) return;
    const page = document.createElement("p");
    page.className = "page";
    page.textContent = index < talkLength ? (index + 1) + " / " + talkLength : "Apéndice " + (index - talkLength + 1);
    slide.appendChild(page);
  });

  previous.addEventListener("click", () => go(active - 1));
  next.addEventListener("click", () => go(active + 1));
  document.getElementById("vista").addEventListener("click", overview);
  document.getElementById("cerrar-vista").addEventListener("click", () => modal.close());
  document.getElementById("completa").addEventListener("click", fullscreen);
  notesButton.addEventListener("click", toggleNotes);
  addEventListener("resize", resize);
  addEventListener("hashchange", () => go(fromHash()));
  addEventListener("mousemove", event => {
    if (event.clientY > innerHeight - 80) showControls();
  });
  addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const key = event.key.toLowerCase();
    if (modal.open) {
      if (key === "o") overview();
      return;
    }
    if (["arrowright", "arrowdown", "pagedown"].includes(key) || (key === " " && event.target.tagName !== "BUTTON")) go(active + 1);
    else if (["arrowleft", "arrowup", "pageup"].includes(key)) go(active - 1);
    else if (key === "home") go(0);
    else if (key === "end") go(slides.length - 1);
    else if (key === "n") toggleNotes();
    else if (key === "o" || key === "escape") overview();
    else if (key === "f") fullscreen();
    else return;
    event.preventDefault();
  });
  stage.addEventListener("click", event => {
    if (event.target.closest("a") || getSelection().toString()) return;
    go(active + (event.clientX < innerWidth / 3 ? -1 : 1));
  });
  stage.addEventListener("touchstart", event => {
    touchStart = event.changedTouches[0].clientX;
  }, {passive: true});
  stage.addEventListener("touchend", event => {
    if (touchStart === null) return;
    const delta = event.changedTouches[0].clientX - touchStart;
    touchStart = null;
    if (Math.abs(delta) > 45) go(active + (delta > 0 ? -1 : 1));
  }, {passive: true});

  go(fromHash());
  resize();
  if (!new URLSearchParams(location.search).has("print")) showControls();
})();
