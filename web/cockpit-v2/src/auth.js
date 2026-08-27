import { clearBearerSession, setBearerSession } from "./state.js";

export const AUTH_SESSION_PATH = "/api/v1/auth/session";

const AUTH_COPY = Object.freeze({
  "no-shell": {
    title: "این صفحه باید از تلگرام باز شود",
    message: "اطلاعات امضاشدهٔ راه‌اندازی در دسترس نیست. برنامهٔ مالک را مستقیماً از تلگرام باز کنید.",
    retry: false,
  },
  rejected: {
    title: "ورود پذیرفته نشد",
    message: "تلگرام تأیید شد اما نود دادهٔ راه‌اندازی را نپذیرفت. برنامه را ببندید و از تلگرام دوباره باز کنید.",
    retry: true,
  },
  "not-owner": {
    title: "این حساب مالک نیست",
    message: "حساب معتبر است اما مجوز سطح مالک ندارد.",
    retry: false,
  },
  expired: {
    title: "نشست پایان یافته است",
    message: "برای ساخت نشست تازه، این صفحه را ببندید و از تلگرام دوباره باز کنید.",
    retry: false,
  },
  reopen: {
    title: "برنامه را دوباره باز کنید",
    message: "دادهٔ راه‌اندازی قبلاً استفاده شده یا دیگر تازه نیست. برنامه را ببندید و مستقیماً از تلگرام باز کنید.",
    retry: false,
  },
  unreachable: {
    title: "نود پاسخ نمی‌دهد",
    message: "اتصال امن برقرار نشد. شبکه و سرویس OFN را بررسی و سپس دوباره تلاش کنید.",
    retry: true,
  },
  error: {
    title: "ورود با خطا روبه‌رو شد",
    message: "هیچ داده‌ای نمایش داده نشد. دوباره تلاش کنید یا برنامه را از تلگرام باز کنید.",
    retry: true,
  },
});

function telegramWebApp(globalObject = globalThis) {
  return globalObject?.Telegram?.WebApp ?? null;
}

export function prepareTelegramShell(globalObject = globalThis) {
  const webApp = telegramWebApp(globalObject);
  if (!webApp) return false;
  try {
    webApp.ready?.();
    webApp.expand?.();
  } catch {
    // Shell presentation is optional; authentication still uses signed initData.
  }
  return true;
}

function classifyAuthFailure(status, body) {
  const code = String(body?.code ?? body?.reason ?? body?.error ?? "").toLowerCase();
  if (status === 403) return "not-owner";
  if (code.includes("expired") || code.includes("replay") || code.includes("used")) return "reopen";
  if (status === 401) return "rejected";
  return "error";
}

export class AuthFailure extends Error {
  constructor(reason, status = null) {
    super(reason);
    this.name = "AuthFailure";
    this.reason = reason;
    this.status = status;
  }
}

export async function establishSession({
  fetchImpl = globalThis.fetch,
  globalObject = globalThis,
  signal,
} = {}) {
  if (typeof fetchImpl !== "function") throw new TypeError("fetch is required");
  clearBearerSession();

  const webApp = telegramWebApp(globalObject);
  const initData = typeof webApp?.initData === "string" ? webApp.initData.trim() : "";
  if (!initData) throw new AuthFailure("no-shell");

  let response;
  try {
    response = await fetchImpl(AUTH_SESSION_PATH, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ init_data: initData }),
      cache: "no-store",
      redirect: "error",
      referrerPolicy: "no-referrer",
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new AuthFailure("unreachable");
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new AuthFailure(classifyAuthFailure(response.status, payload), response.status);
  }
  if (typeof payload?.session !== "string" || payload.session.trim() === "") {
    throw new AuthFailure("error", response.status);
  }

  setBearerSession(payload.session);
  return {
    firstName: typeof payload.first_name === "string" ? payload.first_name : "",
  };
}

export function authMessage(reason) {
  return AUTH_COPY[reason] ?? AUTH_COPY.error;
}

export function markSessionExpired() {
  clearBearerSession();
  return new AuthFailure("expired", 401);
}
