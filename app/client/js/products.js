const grid = document.getElementById("product-grid");
const emptyState = document.getElementById("empty-state");
const pagination = document.getElementById("pagination");
const resultCount = document.getElementById("result-count");

const total = grid.querySelectorAll(".card").length;

// update the count text
resultCount.textContent = total === 1 ? "1 product" : `${total} products`;

// no products: show the empty state, hide the grid, count and pagination
if (total === 0) {
  grid.hidden = true;
  pagination.hidden = true;
  emptyState.hidden = false;
  document.getElementById("result-text").textContent = "No results for your search";
}
