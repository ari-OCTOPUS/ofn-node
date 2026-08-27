import { element, clear } from "./dom.js";

export function renderBanners(container, { online, resources, authStatus }) {
  clear(container);
  const banners = [];

  if (!online) {
    banners.push({
      kind: "offline",
      text: "آفلاین هستید؛ دادهٔ روی صفحه ممکن است تازه نباشد.",
    });
  }
  if (authStatus === "expired") {
    banners.push({
      kind: "error",
      text: "نشست پایان یافته است. پنل را ببندید و از تلگرام دوباره باز کنید.",
    });
  }

  const rows = Object.values(resources || {});
  if (rows.some((row) => row?.status === "error")) {
    banners.push({
      kind: "error",
      text: "دریافت بخشی از داده‌ها ناموفق بود؛ تلاش بعدی با فاصلهٔ بیشتر انجام می‌شود.",
    });
  }
  if (rows.some((row) => row?.stale && row?.lastSuccessAt !== null)) {
    banners.push({
      kind: "stale",
      text: "دادهٔ نمایش‌داده‌شده کهنه است؛ تا دریافت موفق تازه برچسب‌ها را قطعی ندانید.",
    });
  }
  if (rows.length > 0 && rows.every((row) => row?.status === "loading" && row?.data === null)) {
    banners.push({ kind: "info", text: "در حال دریافت دادهٔ زنده…" });
  }

  for (const banner of banners) {
    container.append(element("div", {
      className: "banner",
      text: banner.text,
      attrs: { role: banner.kind === "error" ? "alert" : "status" },
      dataset: { kind: banner.kind },
    }));
  }
}
