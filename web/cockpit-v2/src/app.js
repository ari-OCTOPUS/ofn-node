import { API_PATHS, createApiClient, createPollController } from "./api.js";
import { AuthFailure, authMessage, establishSession, markSessionExpired, prepareTelegramShell } from "./auth.js";
import { renderBanners } from "./components/banners.js";
import { append, clear, element, statePanel } from "./components/dom.js";
import { formatDateTime } from "./formatting.js";
import { createRouter, enableNavKeyboard } from "./router.js";
import { clearBearerSession, createInitialState, createStore, updateResource } from "./state.js";
import { renderAudit } from "./pages/audit.js";
import { renderCommandCenter } from "./pages/command-center.js";
import { renderLegs } from "./pages/legs.js";
import { renderNodes } from "./pages/nodes.js";
import { renderQueue } from "./pages/queue.js";
import { renderSurface } from "./pages/surface.js";

const PAGE_CONFIG = Object.freeze({
  surface: { resource: "surface", render: renderSurface, label: "نمای هفت‌کارته" },
  "command-center": { resource: "status", render: renderCommandCenter, label: "مرکز فرمان" },
  nodes: { resource: "nodes", render: renderNodes, label: "نودها" },
  legs: { resource: "legs", render: renderLegs, label: "چرخه" },
  queue: { resource: "queue", render: renderQueue, label: "صف" },
  audit: { resource: "audit", render: renderAudit, label: "ممیزی" },
});

const store = createStore(createInitialState());
const api = createApiClient();
const controllers = new Map();
const main = document.getElementById("main-content");
const bannerRegion = document.getElementById("banner-region");
const connectionSummary = document.querySelector(".connection-summary");
const connectionText = document.getElementById("connection-text");
const liveStatus = document.getElementById("live-status");
const lastSuccess = document.getElementById("last-success");
const welcome = document.getElementById("welcome");
const nav = document.querySelector(".primary-nav");
let teardownNavKeyboard = () => {};
let lastRenderedRoute = null;
let renderQueued = false;
let shuttingDown = false;

function announce(message) {
  liveStatus.textContent = "";
  globalThis.setTimeout(() => { liveStatus.textContent = message; }, 0);
}

function setConnection(state, text) {
  connectionSummary.dataset.state = state;
  connectionText.textContent = text;
}

function latestSuccess(resources) {
  const values = Object.values(resources)
    .map((entry) => entry?.lastSuccessAt)
    .filter((value) => Number.isFinite(value));
  return values.length ? Math.max(...values) : null;
}

function updateChrome(state) {
  renderBanners(bannerRegion, {
    online: state.online,
    resources: state.resources,
    authStatus: state.auth.status,
  });

  if (state.auth.status === "expired") setConnection("expired", "نشست پایان یافته");
  else if (state.auth.status === "authenticated" && state.online) setConnection("online", "متصل · فقط خواندن");
  else if (!state.online) setConnection("offline", "آفلاین");
  else if (state.auth.status === "authenticating") setConnection("pending", "در حال ورود…");
  else setConnection("offline", "بدون داده");

  for (const link of nav.querySelectorAll("a[data-route]")) {
    const selected = link.dataset.route === state.route;
    if (selected) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }

  const receivedAt = latestSuccess(state.resources);
  lastSuccess.textContent = receivedAt === null
    ? "آخرین دریافت موفق: نامعلوم"
    : `آخرین دریافت موفق: ${formatDateTime(receivedAt)}`;
}

function authFailurePanel(reason) {
  const copy = authMessage(reason);
  const retry = copy.retry
    ? element("button", { text: "دوباره تلاش کن", attrs: { type: "button" } })
    : null;
  if (retry) retry.addEventListener("click", () => void authenticate());
  const panel = statePanel({
    kind: "error",
    title: copy.title,
    message: copy.message,
    action: retry,
  });
  panel.dataset.authError = reason;
  return panel;
}

function renderCurrentPage({ focus = false } = {}) {
  const state = store.getState();
  updateChrome(state);
  main.setAttribute("aria-busy", "false");

  if (state.auth.status === "authenticating") {
    clear(main);
    append(main, statePanel({
      kind: "loading",
      title: "در حال برقراری نشست امن",
      message: "نشست فقط در حافظهٔ این صفحه نگه داشته می‌شود.",
      busy: true,
    }));
    main.setAttribute("aria-busy", "true");
    return;
  }

  if (state.auth.status === "failed" || state.auth.status === "expired") {
    clear(main);
    append(main, authFailurePanel(state.auth.reason));
    return;
  }

  if (state.auth.status !== "authenticated") return;

  const config = PAGE_CONFIG[state.route] ?? PAGE_CONFIG["surface"];
  const resourceState = state.resources[config.resource] ?? {};
  const hasData = resourceState.data !== null && resourceState.data !== undefined;

  clear(main);
  if (!hasData && (resourceState.status === "idle" || resourceState.status === "loading")) {
    append(main, statePanel({
      kind: "loading",
      title: `در حال دریافت ${config.label}`,
      message: "درخواست فقط‌خواندنی در حال اجرا است.",
      busy: true,
    }));
    main.setAttribute("aria-busy", "true");
  } else if (!hasData && resourceState.status === "error") {
    append(main, statePanel({
      kind: "error",
      title: "داده دریافت نشد",
      message: "اتصال دوباره با عقب‌نشینی محدود امتحان می‌شود؛ دادهٔ ساختگی نمایش داده نمی‌شود.",
    }));
  } else if (hasData) {
    append(main, config.render(resourceState.data));
    if (resourceState.status === "loading") main.setAttribute("aria-busy", "true");
  }

  document.title = `${config.label} · OFN`;
  if (focus) main.focus({ preventScroll: true });
}

function queueRender(options = {}) {
  if (options.focus) {
    renderCurrentPage({ focus: true });
    return;
  }
  if (renderQueued) return;
  renderQueued = true;
  queueMicrotask(() => {
    renderQueued = false;
    renderCurrentPage();
  });
}

function stopAllPolling() {
  for (const controller of controllers.values()) controller.teardown();
}

function expireSession() {
  if (store.getState().auth.status === "expired") return;
  markSessionExpired();
  stopAllPolling();
  store.setState((state) => ({
    ...state,
    auth: { ...state.auth, status: "expired", reason: "expired" },
  }));
  announce("نشست پایان یافت؛ برنامه را از تلگرام دوباره باز کنید.");
}

function installPollers() {
  if (controllers.size > 0) return;
  for (const [name, path] of Object.entries(API_PATHS)) {
    const controller = createPollController({
      request: ({ signal, etag }) => api.get(path, { signal, etag }),
      onUpdate: (update) => {
        store.setState((state) => {
          const previous = state.resources[name] || {};
          const patch = {
            status: update.status,
            error: update.error,
            stale: update.stale,
            etag: update.etag,
            generatedAt: update.generatedAt,
            lastSuccessAt: update.lastSuccessAt,
            failures: update.failures,
            retryInMs: update.retryInMs ?? null,
          };
          if (update.status === "success" && !update.notModified && update.data !== null) {
            patch.data = update.data;
          } else if (!("data" in previous)) {
            patch.data = null;
          }
          return updateResource(state, name, patch);
        });
        const current = store.getState();
        if (current.route === Object.keys(PAGE_CONFIG).find((route) => PAGE_CONFIG[route].resource === name)) {
          if (update.status === "success") announce(`${PAGE_CONFIG[current.route].label} به‌روز شد.`);
          queueRender();
        } else {
          updateChrome(current);
        }
      },
      onAuthExpired: expireSession,
    });
    controllers.set(name, controller);
  }
}

function startAllPolling() {
  installPollers();
  for (const controller of controllers.values()) controller.start({ immediate: true });
}

async function authenticate() {
  if (shuttingDown) return;
  stopAllPolling();
  clearBearerSession();
  store.setState((state) => ({
    ...state,
    auth: { ...state.auth, status: "authenticating", reason: null },
  }));
  renderCurrentPage();

  try {
    const identity = await establishSession();
    store.setState((state) => ({
      ...state,
      auth: {
        status: "authenticated",
        reason: null,
        firstName: identity.firstName,
      },
    }));
    welcome.textContent = identity.firstName
      ? `خوش آمدی ${identity.firstName} · سطح مالک، فقط‌خواندنی`
      : "سطح مالک، فقط‌خواندنی";
    setConnection("online", "متصل · فقط خواندن");
    announce("ورود مالک تأیید شد؛ داده‌های فقط‌خواندنی در حال دریافت‌اند.");
    startAllPolling();
    queueRender();
  } catch (error) {
    if (error?.name === "AbortError") return;
    const reason = error instanceof AuthFailure ? error.reason : "error";
    clearBearerSession();
    store.setState((state) => ({
      ...state,
      auth: { ...state.auth, status: "failed", reason },
    }));
    announce(authMessage(reason).title);
    renderCurrentPage();
  }
}

const router = createRouter({
  onRoute: (route, { focus }) => {
    const changed = route !== lastRenderedRoute;
    lastRenderedRoute = route;
    store.setState((state) => ({ ...state, route }));
    queueRender({ focus: focus && changed });
  },
});

function onVisibilityChange() {
  for (const controller of controllers.values()) controller.visibilityChanged();
}

function onOnline() {
  store.patch({ online: true });
  updateChrome(store.getState());
  for (const controller of controllers.values()) void controller.refresh();
  announce("اتصال شبکه برقرار شد؛ داده‌ها دوباره بررسی می‌شوند.");
}

function onOffline() {
  store.patch({ online: false });
  updateChrome(store.getState());
  announce("اتصال شبکه قطع شد؛ داده‌های موجود ممکن است کهنه باشند.");
}

function teardown() {
  shuttingDown = true;
  stopAllPolling();
  clearBearerSession();
  router.stop();
  teardownNavKeyboard();
  document.removeEventListener("visibilitychange", onVisibilityChange);
  globalThis.removeEventListener("online", onOnline);
  globalThis.removeEventListener("offline", onOffline);
}

function boot() {
  prepareTelegramShell();
  teardownNavKeyboard = enableNavKeyboard(nav);
  router.start();
  document.addEventListener("visibilitychange", onVisibilityChange);
  globalThis.addEventListener("online", onOnline);
  globalThis.addEventListener("offline", onOffline);
  globalThis.addEventListener("pagehide", teardown, { once: true });
  void authenticate();
}

boot();
