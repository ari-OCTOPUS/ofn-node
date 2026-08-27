let bearerSession = null;

export function setBearerSession(token) {
  if (typeof token !== "string" || token.trim() === "") {
    throw new TypeError("A non-empty session token is required");
  }
  bearerSession = token;
}

export function getBearerSession() {
  return bearerSession;
}

export function clearBearerSession() {
  bearerSession = null;
}

export function hasBearerSession() {
  return bearerSession !== null;
}

export function createInitialState() {
  return {
    auth: {
      status: "idle",
      reason: null,
      firstName: "",
    },
    route: "command-center",
    online: typeof navigator === "undefined" ? true : navigator.onLine !== false,
    resources: Object.create(null),
  };
}

export function createStore(initialState = createInitialState()) {
  let state = initialState;
  const listeners = new Set();

  return {
    getState() {
      return state;
    },
    setState(updater) {
      const next = typeof updater === "function" ? updater(state) : updater;
      if (!next || next === state) return state;
      state = next;
      for (const listener of [...listeners]) listener(state);
      return state;
    },
    patch(patch) {
      return this.setState((current) => ({ ...current, ...patch }));
    },
    subscribe(listener) {
      if (typeof listener !== "function") throw new TypeError("listener must be a function");
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export function updateResource(state, name, patch) {
  return {
    ...state,
    resources: {
      ...state.resources,
      [name]: {
        status: "idle",
        data: null,
        error: null,
        generatedAt: null,
        lastSuccessAt: null,
        stale: false,
        ...(state.resources[name] || {}),
        ...patch,
      },
    },
  };
}
