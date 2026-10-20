const pages = Array.from(document.querySelectorAll(".page"));
const detail = document.getElementById("detail");
const detailPreview = document.getElementById("detail-preview");
let current = 0;
function fit(preview) {
  const slide = preview.querySelector(".slide");
  if (slide) slide.style.transform = "scale(" + preview.clientWidth / slide.offsetWidth + ")";
}
const observer = new ResizeObserver(entries => entries.forEach(entry => fit(entry.target)));
document.querySelectorAll(".preview").forEach(preview => observer.observe(preview));
function showSlide(index) {
  current = Math.max(0, Math.min(index, pages.length - 1));
  detailPreview.replaceChildren(pages[current].querySelector(".slide").cloneNode(true));
  document.getElementById("previous").disabled = current === 0;
  document.getElementById("next").disabled = current === pages.length - 1;
  if (!detail.open) detail.showModal();
  fit(detailPreview);
}
pages.forEach((page, index) => page.addEventListener("click", () => showSlide(index)));
document.getElementById("previous").onclick = () => showSlide(current - 1);
document.getElementById("next").onclick = () => showSlide(current + 1);
document.getElementById("close-detail").onclick = () => detail.close();
// A click anywhere except the slide and the buttons returns to the grid.
detail.addEventListener("click", event => {
  if (!event.target.closest(".preview, button")) detail.close();
});
document.addEventListener("keydown", event => {
  if (!detail.open) return;
  if (event.key === "ArrowRight") showSlide(current + 1);
  if (event.key === "ArrowLeft") showSlide(current - 1);
});
window.mockReady = (async () => {
  await document.fonts.ready;
  await Promise.all(Array.from(document.images).map(img => img.decode().catch(() => {})));
  document.querySelectorAll(".preview").forEach(fit);
  return true;
})();
