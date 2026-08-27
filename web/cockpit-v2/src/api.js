import { getBearerSession } from "./state.js";

export const API_PATHS = Object.freeze({
  status: "/api/v2/owner/status",
  nodes: "/api/v2/owner/nodes",
  legs: "/api/v2/owner/legs",
  queue: "/api/v2/owner/queue",
  audit: "/api/v2/owner/audit",
});

export const VISIBLE_INTERVAL_MS = 15_000;
export const HIDDEN_INTERVAL_MS = 60_000;
export const REQUEST_TIMEOUT_MS = 10_000;
export const MAX_BACKOFF_MS = 5 * 60_000;

function makeAbortError(message = "Aborted") {
  try {
    return new DOMException(message, "AbortError");
  } catch {
    const error = new Error(message);
    error.name = "AbortError";
    return error;
  }
}

function responseHeader(response, name) {
  return response?.headers?.get?.(name) ?? null;
}

async function safeErrorBody(response) {
  try {
    const payload = await response.json();
    return payload && typeof payload === "object" ? payload : null;
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  constructor(message, { status = null, code = null, cause = null } = {}) {
    super(message, cause ? { cause } : undefined);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function createApiClient({
  fetchImpl = globalThis.fetch,
  getSession = getBearerSession,
} = {}) {
  if (typeof fetchImpl !== "function") throw new TypeError("fetch is required");

  return {
    async get(path, { signal, etag = null } = {}) {
      if (!Object.values(API_PATHS).includes(path)) {
        throw new TypeError("Only declared same-origin /api/v2 owner reads are allowed");
      }
      const token = getSession();
      if (!token) throw new ApiError("No bearer session", { status: 401, code: "no-session" });

      const headers = {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
      };
      if (etag) headers["If-None-Match"] = etag;

      let response;
      try {
        response = await fetchImpl(path, {
          method: "GET",
          headers,
          cache: "no-store",
          redirect: "error",
          referrerPolicy: "no-referrer",
          signal,
        });
      } catch (error) {
        if (error?.name === "AbortError") throw error;
        throw new ApiError("Network request failed", { code: "network", cause: error });
      }

      const responseEtag = responseHeader(response, "ETag") ?? etag;
      if (response.status === 304) {
        return { notModified: true, data: null, etag: responseEtag };
      }
      if (!response.ok) {
        const payload = await safeErrorBody(response);
        throw new ApiError(`HTTP ${response.status}`, {
          status: response.status,
          code: payload?.code ?? payload?.error ?? "http",
        });
      }

      let data;
      try {
        data = await response.json();
      } catch (error) {
        throw new ApiError("Invalid JSON response", { status: response.status, code: "invalid-json", cause: error });
      }
      return { notModified: false, data, etag: responseEtag };
    },
  };
}

export function computeBackoffDelay(failures, baseMs, maxMs = MAX_BACKOFF_MS) {
  const count = Math.max(0, Math.floor(Number(failures) || 0));
  const base = Math.max(1, Math.floor(Number(baseMs) || VISIBLE_INTERVAL_MS));
  if (count === 0) return base;
  return Math.min(maxMs, base * (2 ** Math.min(count, 20)));
}

export function createPollController({
  request,
  onUpdate = () => {},
  onError = () => {},
  onAuthExpired = () => {},
  isHidden = () => typeof document !== "undefined" && document.visibilityState === "hidden",
  visibleIntervalMs = VISIBLE_INTERVAL_MS,
  hiddenIntervalMs = HIDDEN_INTERVAL_MS,
  timeoutMs = REQUEST_TIMEOUT_MS,
  maxBackoffMs = MAX_BACKOFF_MS,
  now = () => Date.now(),
  setTimeoutImpl = globalThis.setTimeout,
  clearTimeoutImpl = globalThis.clearTimeout,
  AbortControllerImpl = globalThis.AbortController,
} = {}) {
  if (typeof request !== "function") throw new TypeError("request must be a function");
  if (typeof AbortControllerImpl !== "function") throw new TypeError("AbortController is required");

  let active = false;
  let stoppedForAuth = false;
  let generation = 0;
  let failures = 0;
  let etag = null;
  let lastSuccessAt = null;
  let generatedAt = null;
  let timer = null;
  let inFlight = null;

  const clearSchedule = () => {
    if (timer !== null) {
      clearTimeoutImpl(timer);
      timer = null;
    }
  };

  const baseInterval = () => isHidden() ? hiddenIntervalMs : visibleIntervalMs;

  const schedule = (delay) => {
    clearSchedule();
    if (!active || stoppedForAuth) return;
    timer = setTimeoutImpl(() => {
      timer = null;
      void poll("timer");
    }, Math.max(0, delay));
  };

  const emit = (patch) => onUpdate({
    status: "idle",
    data: null,
    notModified: false,
    stale: false,
    error: null,
    etag,
    generatedAt,
    lastSuccessAt,
    failures,
    ...patch,
  });

  async function poll(reason = "manual") {
    if (!active || stoppedForAuth) return { skipped: "stopped" };
    if (inFlight) return { skipped: "inflight" };

    clearSchedule();
    const runGeneration = generation;
    const controller = new AbortControllerImpl();
    let timedOut = false;
    const timeout = setTimeoutImpl(() => {
      timedOut = true;
      controller.abort(makeAbortError("Request timed out"));
    }, timeoutMs);
    inFlight = { controller, runGeneration };
    emit({ status: "loading", reason, stale: lastSuccessAt !== null });

    try {
      const result = await request({ signal: controller.signal, etag });
      if (!active || stoppedForAuth || runGeneration !== generation || inFlight?.controller !== controller) {
        return { ignored: "late" };
      }

      const completedAt = now();
      failures = 0;
      etag = result?.etag ?? etag;
      lastSuccessAt = completedAt;

      if (result?.notModified) {
        emit({ status: "success", notModified: true, stale: false, receivedAt: completedAt });
      } else {
        const envelope = result?.data;
        generatedAt = envelope?.generated_at
          ?? envelope?.generatedAt
          ?? envelope?.meta?.generated_at
          ?? envelope?.meta?.generatedAt
          ?? null;
        emit({
          status: "success",
          data: envelope,
          notModified: false,
          stale: false,
          receivedAt: completedAt,
        });
      }
      schedule(baseInterval());
      return { ok: true, notModified: Boolean(result?.notModified) };
    } catch (error) {
      if (!active || runGeneration !== generation || inFlight?.controller !== controller) {
        return { ignored: "late" };
      }
      if (error?.status === 401) {
        stoppedForAuth = true;
        active = false;
        clearSchedule();
        emit({ status: "expired", stale: lastSuccessAt !== null, error });
        onAuthExpired(error);
        return { stopped: "auth" };
      }
      if (error?.name === "AbortError" && !timedOut) {
        return { aborted: true };
      }

      failures += 1;
      const delay = computeBackoffDelay(failures, baseInterval(), maxBackoffMs);
      emit({ status: "error", stale: lastSuccessAt !== null, error, retryInMs: delay });
      onError(error, { failures, retryInMs: delay, timedOut });
      schedule(delay);
      return { ok: false, error };
    } finally {
      clearTimeoutImpl(timeout);
      if (inFlight?.controller === controller) inFlight = null;
    }
  }

  function start({ immediate = true } = {}) {
    if (stoppedForAuth) return false;
    active = true;
    generation += 1;
    clearSchedule();
    if (immediate) void poll("start");
    else schedule(baseInterval());
    return true;
  }

  function refresh() {
    if (!active || stoppedForAuth) return Promise.resolve({ skipped: "stopped" });
    return poll("refresh");
  }

  function visibilityChanged() {
    if (!active || stoppedForAuth) return;
    generation += 1;
    clearSchedule();
    if (inFlight) {
      inFlight.controller.abort(makeAbortError("Visibility changed"));
      inFlight = null;
    }
    schedule(baseInterval());
  }

  function stop() {
    active = false;
    generation += 1;
    clearSchedule();
    if (inFlight) {
      inFlight.controller.abort(makeAbortError("Polling stopped"));
      inFlight = null;
    }
  }

  function reset() {
    stop();
    stoppedForAuth = false;
    failures = 0;
    etag = null;
    lastSuccessAt = null;
    generatedAt = null;
  }

  return {
    start,
    refresh,
    visibilityChanged,
    stop,
    teardown: stop,
    reset,
    snapshot() {
      return {
        active,
        stoppedForAuth,
        generation,
        failures,
        etag,
        lastSuccessAt,
        generatedAt,
        inFlight: Boolean(inFlight),
        scheduled: timer !== null,
      };
    },
  };
}
