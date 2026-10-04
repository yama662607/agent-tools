const cards = Array.from(document.querySelectorAll(".card"));
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
  current = Math.max(0, Math.min(index, cards.length - 1));
  detailPreview.replaceChildren(cards[current].querySelector(".slide").cloneNode(true));
  document.getElementById("detail-notes").innerHTML = cards[current].querySelector(".notes").innerHTML;
  document.getElementById("slide-position").textContent = (current + 1) + " / " + cards.length;
  document.getElementById("previous").disabled = current === 0;
  document.getElementById("next").disabled = current === cards.length - 1;
  if (!detail.open) detail.showModal();
  fit(detailPreview);
  detail.scrollTop = 0;
}
document.querySelectorAll(".open-slide").forEach(button => {
  button.addEventListener("click", () => showSlide(Number(button.dataset.index)));
});
document.getElementById("previous").onclick = () => showSlide(current - 1);
document.getElementById("next").onclick = () => showSlide(current + 1);
document.getElementById("close-detail").onclick = () => detail.close();
document.getElementById("toggle-notes").onclick = function () {
  const visible = document.body.classList.toggle("show-notes");
  this.setAttribute("aria-pressed", String(visible));
  this.textContent = visible ? "構成メモを隠す" : "構成メモを表示";
};
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
