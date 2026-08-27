const ROUTES = Object.freeze([
  "command-center",
  "nodes",
  "legs",
  "queue",
  "audit",
]);

export function normalizeRoute(hash = "") {
  const raw = String(hash).replace(/^#\/?/, "").split(/[/?]/, 1)[0].trim().toLowerCase();
  return ROUTES.includes(raw) ? raw : "command-center";
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
      globalObject.addEventListener?.("hashchange", onHashChange);
      if (!globalObject.location?.hash || normalizeRoute(globalObject.location.hash) === "command-center") {
        if (globalObject.location && globalObject.location.hash !== "#/command-center") {
          globalObject.history?.replaceState?.(null, "", "#/command-center");
        }
      }
      return apply({ focus: false });
    },
    navigate(route) {
      const normalized = ROUTES.includes(route) ? route : "command-center";
      if (globalObject.location) globalObject.location.hash = `#/${normalized}`;
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
