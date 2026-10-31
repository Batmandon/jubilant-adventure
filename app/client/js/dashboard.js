// ===================== CONFIG =====================
const CONFIG = {
  API_BASE: window.APP_CONFIG.API_BASE_URL, // comes from config.js, which must load before this file
  LOGIN_PAGE: "login.html",
  ACCOUNT_PAGE: "account.html",
  PAGE_SIZE: 20,
  RECENT_ORDERS: 10,   // rows in the "Recent orders" card on the overview
  SEARCH_DELAY: 350,   // ms to wait after typing before searching products
};

const PATHS = {
  profile: "/auth_routes/profile",   // GET   (used to check the user is an admin + show the name)
  logout: "/auth_routes/logout",     // POST
  dashboard: "/admin/dashboard",     // GET   today_orders, pending_orders, revenue, active_products, total_products
  products: "/admin/products",       // GET   ?search=&page=&page_size=
  orders: "/admin/orders",           // GET   ?status=&page=&page_size=   |   PATCH /{id}/status
};

// the order flow, same rules as the backend (it checks again, this only decides which options to show)
const STATUS_STEPS = ["pending", "confirmed", "processing", "shipped", "delivered"];

function nextStatuses(current) {
  const i = STATUS_STEPS.indexOf(current);
  if (i === -1 || current === "delivered") return []; // delivered and cancelled are final
  return [...STATUS_STEPS.slice(i + 1), "cancelled"];
}

// ===================== API LAYER =====================
// Returns the parsed JSON. Throws an Error with a message that is safe to show to the user.
// err.redirecting = true means we are already sending the user to another page.
async function request(method, path, { params, body } = {}) {
  const url = new URL(CONFIG.API_BASE + path);
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== "" && value != null) url.searchParams.set(key, value);
  }

  let res;
  try {
    res = await fetch(url, {
      method,
      credentials: "include", // sends the login cookie
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (_) {
    throw new Error("Cannot reach the server. Check your internet connection and try again.");
  }

  // not logged in -> login page; logged in but not an admin -> account page
  if (res.status === 401 || res.status === 403) {
    window.location.href = res.status === 401 ? CONFIG.LOGIN_PAGE : CONFIG.ACCOUNT_PAGE;
    const err = new Error(res.status === 401 ? "Please log in again." : "You do not have access to this page.");
    err.redirecting = true;
    throw err;
  }

  let data = null;
  try { data = await res.json(); } catch (_) {}

  if (!res.ok) throw new Error(errorMessage(data, res.status));
  if (data === null || typeof data !== "object" || Array.isArray(data)) throw new Error("The server sent an unexpected response.");
  return data;
}

function errorMessage(data, status) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    // validation errors (422): show the readable part of each
    return detail.map((e) => String(e.msg || "").replace(/^Value error, /, "")).filter(Boolean).join(". ");
  }
  if (data && typeof data.message === "string") return data.message;
  if (status === 404) return "Not found.";
  if (status >= 500) return "Server error. Please try again in a moment.";
  return "Something went wrong. Please try again.";
}

// ===================== ELEMENTS =====================
const $ = (id) => document.getElementById(id);

const pageMsg = $("page-message");
const confirmDialog = $("confirm-dialog");

const views = ["overview", "orders", "products"];
const titles = { overview: "Overview", orders: "Orders", products: "Products" };

// ===================== HELPERS =====================
const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const count = new Intl.NumberFormat("en-IN");
const moneyWhole = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }); // for big tiles
const dateFmt = new Intl.DateTimeFormat("en-IN", {
  day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata",
});

const toNumber = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);
const toItems = (data) => (Array.isArray(data.items) ? data.items : []);
const PAYMENT_LABELS = { cod: "Cash on delivery", pickup: "Store pickup" };

function formatDate(value) {
  const d = new Date(value);
  return isNaN(d) ? "" : dateFmt.format(d);
}
const cap = (s) => String(s).charAt(0).toUpperCase() + String(s).slice(1);

function showMessage(text, type = "error") {
  pageMsg.textContent = text;
  pageMsg.className = `form-message ${type}`;
}
function clearMessage() {
  pageMsg.textContent = "";
  pageMsg.className = "form-message";
}

let toastTimer;
function showToast(text) {
  const toast = $("toast");
  toast.textContent = text;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

// resolves true if the admin confirms, false on cancel / Esc / click outside
function confirmAction({ title, text, confirmLabel }) {
  $("confirm-title").textContent = title;
  $("confirm-text").textContent = text;
  confirmDialog.querySelector('button[value="confirm"]').textContent = confirmLabel;
  confirmDialog.returnValue = "";
  confirmDialog.showModal();
  return new Promise((resolve) => {
    confirmDialog.addEventListener("close", () => resolve(confirmDialog.returnValue === "confirm"), { once: true });
  });
}

// one full-width row inside a table body: "Loading...", "Could not load..."
function tableMessage(tbody, columns, text) {
  const td = document.createElement("td");
  td.colSpan = columns;
  td.className = "empty";
  td.textContent = text;
  const tr = document.createElement("tr");
  tr.append(td);
  tbody.replaceChildren(tr);
}

// clone a <template> and give back a function to fill its [data-f] cells by name
function cloneRow(templateId) {
  const row = $(templateId).content.firstElementChild.cloneNode(true);
  const cell = (name) => row.querySelector(`[data-f="${name}"]`);
  return { row, cell };
}

function setStatus(node, status) {
  node.textContent = status;
  node.className = `status status-${status}`;
}

function updatePager({ prev, next, info }, page, size, total) {
  const pages = Math.max(1, Math.ceil(total / size));
  prev.disabled = page <= 1;
  next.disabled = page >= pages;
  info.textContent = total ? `Page ${page} of ${pages} · ${count.format(total)} total` : "";
}

// ===================== VIEWS (sidebar) =====================
const loaded = { orders: false, products: false };

function showView(name, { updateHash = true } = {}) {
  if (!views.includes(name)) name = "overview";

  document.querySelectorAll(".nav-item[data-view]").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  views.forEach((v) => { $(`view-${v}`).hidden = v !== name; });
  $("view-title").textContent = titles[name];
  if (updateHash) history.replaceState(null, "", `#${name}`);

  // orders and products load the first time they are opened
  if (name === "orders" && !loaded.orders) { loaded.orders = true; loadOrders(); }
  if (name === "products" && !loaded.products) { loaded.products = true; loadProducts(); }
}

// sidebar buttons
$("nav").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-view]");
  if (btn) showView(btn.dataset.view);
});

// links inside the page, like "View all orders"
document.addEventListener("click", (e) => {
  const link = e.target.closest("[data-view-link]");
  if (link) showView(link.dataset.viewLink);
});

window.addEventListener("hashchange", () => showView(location.hash.slice(1), { updateHash: false }));

// ===================== OVERVIEW: tiles =====================
function renderStats(d) {
  $("stat-today").textContent = count.format(toNumber(d.today_orders));
  $("stat-pending").textContent = count.format(toNumber(d.pending_orders));
  $("stat-revenue").textContent = moneyWhole.format(toNumber(d.revenue));
  $("stat-active-products").textContent = count.format(toNumber(d.active_products));
}

async function loadStats() {
  try {
    renderStats(await request("GET", PATHS.dashboard));
    clearMessage();
  } catch (err) {
    if (!err.redirecting) showMessage(`Could not load the summary. ${err.message}`);
  }
}

// ===================== OVERVIEW: recent orders =====================
async function loadRecent() {
  const body = $("recent-orders-body");
  try {
    const data = await request("GET", PATHS.orders, { params: { page: 1, page_size: CONFIG.RECENT_ORDERS } });
    const items = toItems(data);

    body.replaceChildren(...items.map((o) => {
      const { row, cell } = cloneRow("recent-order-row");
      cell("id").textContent = `#${o.id}`;
      cell("customer").textContent = o.customer || "";
      cell("date").textContent = formatDate(o.created_at);
      cell("total").textContent = money.format(toNumber(o.total));
      setStatus(cell("status"), String(o.status));
      return row;
    }));
    $("recent-orders-empty").hidden = items.length > 0;
  } catch (err) {
    if (!err.redirecting) tableMessage(body, 5, `Could not load orders. ${err.message}`);
  }
}

// ===================== ORDERS =====================
const orderState = { page: 1, status: "", seq: 0 };
const orderPager = { prev: $("order-prev"), next: $("order-next"), info: $("order-page-info") };

function orderRow(o) {
  const { row, cell } = cloneRow("order-row");
  const status = String(o.status);
  row.dataset.id = o.id; // the status dropdown reads the order id from here

  cell("id").textContent = `#${o.id}`;
  cell("customer").textContent = o.customer || "";
  cell("date").textContent = formatDate(o.created_at);
  cell("payment").textContent = PAYMENT_LABELS[o.payment_method] || o.payment_method || "";
  cell("total").textContent = money.format(toNumber(o.total));
  setStatus(cell("status"), status);

  const select = cell("next-status");
  const options = nextStatuses(status);
  select.append(new Option("Change...", ""));
  options.forEach((s) => select.append(new Option(cap(s), s)));
  select.disabled = options.length === 0;
  return row;
}

async function loadOrders() {
  const seq = ++orderState.seq; // ignore answers that arrive late, after a newer request
  const body = $("order-body");
  tableMessage(body, 7, "Loading...");
  $("order-empty").hidden = true;

  try {
    const data = await request("GET", PATHS.orders, {
      params: { page: orderState.page, page_size: CONFIG.PAGE_SIZE, status: orderState.status },
    });
    if (seq !== orderState.seq) return;

    const items = toItems(data);
    body.replaceChildren(...items.map(orderRow));
    $("order-empty").hidden = items.length > 0;
    updatePager(orderPager, orderState.page, CONFIG.PAGE_SIZE, toNumber(data.total));
  } catch (err) {
    if (seq === orderState.seq && !err.redirecting) tableMessage(body, 7, `Could not load orders. ${err.message}`);
  }
}

$("order-status-filter").addEventListener("change", (e) => {
  orderState.status = e.target.value;
  orderState.page = 1;
  loadOrders();
});
$("order-prev").addEventListener("click", () => { orderState.page -= 1; loadOrders(); });
$("order-next").addEventListener("click", () => { orderState.page += 1; loadOrders(); });

// the "Change status" dropdown in every row (one listener on the table body)
$("order-body").addEventListener("change", async (e) => {
  const select = e.target.closest('select[data-f="next-status"]');
  if (!select || !select.value) return;

  const orderId = select.closest("tr").dataset.id;
  const next = select.value;

  if (next === "cancelled" || next === "delivered") {
    const ok = await confirmAction({
      title: next === "cancelled" ? `Cancel order #${orderId}?` : `Mark order #${orderId} as delivered?`,
      text: next === "cancelled"
        ? "The items go back into stock. This cannot be undone."
        : "A delivered order cannot be changed again.",
      confirmLabel: next === "cancelled" ? "Cancel order" : "Mark delivered",
    });
    if (!ok) { select.value = ""; return; }
  }

  select.disabled = true;
  try {
    await request("PATCH", `${PATHS.orders}/${orderId}/status`, { body: { status: next } });
    showToast(`Order #${orderId} is now ${next}`);
  } catch (err) {
    if (err.redirecting) return;
    showToast(err.message);
  }
  // success or failure, reload so the screen matches the database
  // (the tiles change too: pending count, revenue)
  await Promise.allSettled([loadOrders(), loadRecent(), loadStats()]);
});

// ===================== PRODUCTS =====================
const productState = { page: 1, search: "", seq: 0 };
const productPager = { prev: $("page-prev"), next: $("page-next"), info: $("page-info") };

function productRow(p) {
  const { row, cell } = cloneRow("product-row");
  row.dataset.id = p.id;

  cell("name").textContent = p.name;
  cell("sub").textContent = [p.form, p.strength, p.pack_size].filter(Boolean).join(" · ");
  cell("category").textContent = p.category || "";
  cell("stock").textContent = count.format(toNumber(p.total_stock));
  setStatus(cell("status"), p.is_active ? "active" : "inactive");
  return row;
}

async function loadProducts() {
  const seq = ++productState.seq;
  const body = $("product-body");
  tableMessage(body, 5, "Loading...");
  $("product-empty").hidden = true;

  try {
    const data = await request("GET", PATHS.products, {
      params: { search: productState.search, page: productState.page, page_size: CONFIG.PAGE_SIZE },
    });
    if (seq !== productState.seq) return;

    const items = toItems(data);
    body.replaceChildren(...items.map(productRow));
    $("product-empty").hidden = items.length > 0;
    updatePager(productPager, productState.page, CONFIG.PAGE_SIZE, toNumber(data.total));
  } catch (err) {
    if (seq === productState.seq && !err.redirecting) tableMessage(body, 5, `Could not load products. ${err.message}`);
  }
}

// search: wait until the admin stops typing, then go back to page 1
let searchTimer;
$("product-search").addEventListener("input", (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    productState.search = e.target.value.trim();
    productState.page = 1;
    loadProducts();
  }, CONFIG.SEARCH_DELAY);
});
$("page-prev").addEventListener("click", () => { productState.page -= 1; loadProducts(); });
$("page-next").addEventListener("click", () => { productState.page += 1; loadProducts(); });

// Add / edit / delete come in the next step (they need the product dialog + the write endpoints)
const NEXT_STEP = "Adding and editing products is the next step.";
$("add-product-btn").addEventListener("click", () => showToast(NEXT_STEP));
$("product-body").addEventListener("click", (e) => {
  if (e.target.closest("[data-action]")) showToast(NEXT_STEP);
});

// ===================== DIALOG CLOSING =====================
document.addEventListener("click", (e) => {
  const closer = e.target.closest("[data-close]");
  if (closer) { closer.closest("dialog").close(); return; }
  if (e.target instanceof HTMLDialogElement) e.target.close(); // click on the dark backdrop
});

// ===================== LOGOUT =====================
$("logout-btn").addEventListener("click", async () => {
  const ok = await confirmAction({
    title: "Log out?",
    text: "You will need to log in again to open the dashboard.",
    confirmLabel: "Logout",
  });
  if (!ok) return;

  try {
    await request("POST", PATHS.logout);
    window.location.href = CONFIG.LOGIN_PAGE;
  } catch (err) {
    if (!err.redirecting) showToast(err.message);
  }
});

// ===================== INITIAL LOAD =====================
async function init() {
  // 1) who is this? Only admins stay on this page.
  let profile;
  try {
    profile = await request("GET", PATHS.profile);
  } catch (err) {
    if (!err.redirecting) showMessage(`Could not load the dashboard. ${err.message}`);
    return;
  }
  if (profile.role !== "admin") { window.location.replace(CONFIG.ACCOUNT_PAGE); return; }
  $("admin-name").textContent = [profile.first_name, profile.last_name].filter(Boolean).join(" ");

  // 2) the overview always loads; orders / products load when their view opens
  showView(location.hash.slice(1) || "overview", { updateHash: false });
  loadStats();
  loadRecent();
}

init();
