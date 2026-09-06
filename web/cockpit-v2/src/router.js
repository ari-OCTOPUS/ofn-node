const ROUTES = Object.freeze([
  "surface",
  "command-center",
  "nodes",
  "legs",
  "queue",
  "audit",
]);

const DEFAULT_ROUTE = "surface";

export function normalizeRoute(hash = "") {
  const raw = String(hash).replace(/^#\/?/, "").split(/[/?]/, 1)[0].trim().toLowerCase();
  return ROUTES.includes(raw) ? raw : DEFAULT_ROUTE;
}

export function createRouter({
  globalObject = globalThis,
  onRoute = () => {},
} = {}) {
  let current = null;
  let started = false;

  const apply = ({ focus = true } = {}) => {
    const next = normalizeRoute(globalObject.location?.hash ?? "");
    if (next === current && started) return next;
    current = next;
    onRoute(next, { focus });
    return next;
  };

  const onHashChange = () => apply({ focus: true });

  return {
  start() {
    if (started) return current;
    started = true;
    globalThis.addEventListener?.("hashchange", onHashChange);
    if (!globalThis.location?.hash || normalizeRoute(globalThis.location.hash) === DEFAULT_ROUTE) {
      if (globalThis.location && globalThis.location.hash !== `#/${DEFAULT_ROUTE}`) {
        globalThis.history?.replaceState?.(null, "", `#/${DEFAULT_ROUTE}`);
      }
    }
    return apply({ focus: false });
  },
  navigate(route) {
    const normalized = ROUTES.includes(route) ? route : DEFAULT_ROUTE;
    if (globalThis.location) globalThis.location.hash = `#/${normalized}`;
    return normalized;
  },
    current() {
      return current ?? normalizeRoute(globalObject.location?.hash ?? "");
    },
    stop() {
      globalObject.removeEventListener?.("hashchange", onHashChange);
      started = false;
    },
  };
}

export function enableNavKeyboard(navElement) {
  if (!navElement) return () => {};
  const handler = (event) => {
    const keys = new Set(["ArrowLeft", "ArrowRight", "Home", "End"]);
    if (!keys.has(event.key)) return;
    const links = [...navElement.querySelectorAll("a[data-route]")];
    const active = links.indexOf(event.target);
    if (active < 0 || links.length === 0) return;
    event.preventDefault();

    let next = active;
    if (event.key === "Home") next = 0;
    else if (event.key === "End") next = links.length - 1;
    else if (event.key === "ArrowLeft") next = (active + 1) % links.length;
    else if (event.key === "ArrowRight") next = (active - 1 + links.length) % links.length;
    links[next].focus();
  };
  navElement.addEventListener("keydown", handler);
  return () => navElement.removeEventListener("keydown", handler);
}

export { ROUTES };
