const categorySection = document.querySelector(".category-nav-section");

categorySection?.addEventListener("click", (event) => {
  if (!(event.target instanceof Element)) {
    return;
  }

  const categoryCard = event.target.closest(".category-card");
  if (!categoryCard || !categorySection.contains(categoryCard)) {
    return;
  }

  const categoryName = categoryCard.querySelector(".category-name")?.textContent.trim();
  if (!categoryName) {
    return;
  }

  event.preventDefault();
  const searchParams = new URLSearchParams({ name: categoryName });
  window.location.assign(`products.html?${searchParams.toString()}`);
});
