(() => {
  const summary = document.getElementById("sum");
  const cartItems = document.getElementById("cart-items");
  const cartMessage = document.getElementById("cart-message");
  const orderButtons = document.querySelectorAll("[data-order]");
  const currency = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  });
  const deliveryCharge = 30;
  let cart = [];

  function setCartMessage(message) {
    cartMessage.textContent = message;
    cartMessage.hidden = false;
  }

  function formatAmount(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount < 0) {
      throw new Error("The cart response contains an invalid amount.");
    }
    return amount;
  }

  function getImageUrl(value) {
    if (typeof value !== "string" || !value.trim()) return "";
    try {
      const url = new URL(value, window.location.href);
      return ["http:", "https:"].includes(url.protocol) ? url.href : "";
    } catch {
      return "";
    }
  }

  function createCartItem(item) {
    const row = document.createElement("div");
    row.className = "item";
    row.dataset.cartItem = "";

    const imageContainer = document.createElement("div");
    imageContainer.className = "pill";
    const imageUrl = getImageUrl(item.img_url);
    if (imageUrl) {
      const image = document.createElement("img");
      image.src = imageUrl;
      image.alt = "";
      image.loading = "lazy";
      image.addEventListener("error", () => {
        image.replaceWith(document.createTextNode("💊"));
      }, { once: true });
      imageContainer.append(image);
    } else {
      imageContainer.textContent = "💊";
    }

    const details = document.createElement("div");
    const name = document.createElement("b");
    name.textContent = item.name;
    const description = document.createElement("small");
    description.textContent = [
      item.strength,
      item.pack_size,
      `${currency.format(formatAmount(item.price))} each`,
      `Qty ${item.quantity}`,
    ].filter(Boolean).join(" · ");
    details.append(name, description);

    const price = document.createElement("span");
    price.className = "price";
    price.textContent = currency.format(formatAmount(item.line_total));

    const removeButton = document.createElement("button");
    removeButton.className = "remove-item";
    removeButton.type = "button";
    removeButton.dataset.removeItem = "";
    removeButton.dataset.productId = String(item.product_id);
    removeButton.setAttribute("aria-label", `Remove ${item.name} from cart`);
    removeButton.title = "Remove item";
    const icon = document.createElement("i");
    icon.className = "fa-solid fa-trash-can";
    icon.setAttribute("aria-hidden", "true");
    removeButton.append(icon);

    row.append(imageContainer, details, price, removeButton);
    return row;
  }

  function renderCart(subtotal) {
    cartItems.replaceChildren(...cart.map(createCartItem));
    const hasItems = cart.length > 0;
    const delivery = hasItems ? deliveryCharge : 0;
    const total = subtotal + delivery;
    const countLabel = `Order summary (${cart.length} ${cart.length === 1 ? "item" : "items"})`;

    document.getElementById("mobile-summary-title").textContent = countLabel;
    document.getElementById("desktop-summary-title").textContent = countLabel;
    summary.querySelector('[data-summary="subtotal"]').textContent = currency.format(subtotal);
    summary.querySelector('[data-summary="delivery"]').textContent = currency.format(delivery);
    summary.querySelector('[data-summary="tax"]').textContent = currency.format(0);
    summary.querySelector('[data-summary="total"]').textContent = currency.format(total);
    document.querySelector('[data-summary="mobile-total"]').textContent = currency.format(total);
    orderButtons.forEach((button) => {
      button.disabled = !hasItems;
    });

    if (hasItems) {
      cartMessage.hidden = true;
    } else {
      setCartMessage("Your cart is empty.");
    }
  }

  async function readResponse(response) {
    const responseText = await response.text();
    let body = {};
    if (responseText) {
      try {
        body = JSON.parse(responseText);
      } catch {
        body = { detail: responseText };
      }
    }
    if (!response.ok) {
      const message = typeof body.detail === "string"
        ? body.detail
        : `Cart request failed (HTTP ${response.status}).`;
      throw new Error(message);
    }
    return body;
  }

  async function loadCart() {
    try {
      const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/orders/items`, {
        credentials: "include",
      });
      const body = await readResponse(response);
      if (!Array.isArray(body.items)) {
        throw new Error("The cart response is missing its items list.");
      }
      cart = body.items;
      renderCart(formatAmount(body.total));
    } catch (error) {
      console.error("Could not load cart:", error);
      cart = [];
      cartItems.replaceChildren();
      renderCart(0);
      setCartMessage(error.message || "Could not load your cart. Please try again.");
    }
  }

  summary.addEventListener("click", async (event) => {
    if (!(event.target instanceof Element)) return;
    const removeButton = event.target.closest("[data-remove-item]");
    if (!removeButton || !summary.contains(removeButton)) return;

    removeButton.disabled = true;
    try {
      const response = await fetch(
        `${window.APP_CONFIG.API_BASE_URL}/orders/items/${encodeURIComponent(removeButton.dataset.productId)}`,
        { method: "DELETE", credentials: "include" },
      );
      await readResponse(response);
      await loadCart();
    } catch (error) {
      console.error("Could not remove cart item:", error);
      removeButton.disabled = false;
      setCartMessage(error.message || "Could not remove this item. Please try again.");
    }
  });

  loadCart();
})();
