// Renders ```mermaid fences (pymdownx.superfences emits <div class="mermaid">).
// Waits for the theme's web fonts: Mermaid sizes its boxes from the font, and measuring
// with a fallback font clips the labels once the real one has loaded.
mermaid.initialize({ startOnLoad: false });
document.fonts.ready
  .then(() => mermaid.run())
  .catch((error) => console.error("Mermaid rendering failed:", error));
