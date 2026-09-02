// content.js — runs inside buy.nsw pages the user is already viewing.
// Two jobs: (1) scrape a search-results page into records, (2) scrape a detail page.
// Robust to unknown class names: keyed off link-href patterns + label:value text,
// not fragile CSS selectors. Tune LINK_PATTERNS / labels if the DOM dump shows drift.

(() => {
  "use strict";

  // Links that identify a tender/opportunity/CAN, on results pages.
  const LINK_PATTERNS = [
    /\/notices\//i,          // /notices/{CNUUID}  (Contract Award Notices)
    /\/prcOpportunity\//i,   // /prcOpportunity/{UUID}
    /\/opportunity\/[0-9a-f-]{8}/i,
    /RFTUUID=/i,
    /CNUUID=/i,
    /SONUUID=/i,
  ];
  const DETAIL_PATTERNS = [/\/notices\//i, /\/prcOpportunity\//i, /RFTUUID=/i, /CNUUID=/i];

  const DATE_RE = /(\d{1,2}\s+\w{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}\/\d{2,4})/;
  const EMAIL_RE = /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i;
  const PHONE_RE = /(\(?0\d\)?[\s-]?\d{4}[\s-]?\d{4}|\+61[\s-]?\d[\s-]?\d{4}[\s-]?\d{4})/;
  const ABN_RE = /\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b/;
  const MONEY_RE = /\$\s?[\d,]+(?:\.\d{2})?/;

  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();

  function isResultsPage() {
    return /\/opportunity\/search|search-closed|\/opportunity(\/)?$/i.test(location.pathname + location.search)
      || document.querySelectorAll("a[href]").length > 40 && findResultLinks().length >= 3;
  }
  function isDetailPage() {
    return DETAIL_PATTERNS.some((re) => re.test(location.pathname + location.search));
  }

  function findResultLinks() {
    const seen = new Set();
    const out = [];
    for (const a of document.querySelectorAll("a[href]")) {
      const href = a.href;
      if (!LINK_PATTERNS.some((re) => re.test(href))) continue;
      if (seen.has(href)) continue;
      seen.add(href);
      out.push(a);
    }
    return out;
  }

  // Walk up from a link to the "card" container that holds its metadata.
  function cardOf(a) {
    let el = a;
    for (let i = 0; i < 6 && el && el.parentElement; i++) {
      el = el.parentElement;
      const tag = el.tagName.toLowerCase();
      const cls = (el.className || "").toString().toLowerCase();
      if (tag === "li" || tag === "article" ||
          /card|result|tile|listing|opportunity|notice|row/.test(cls)) {
        return el;
      }
    }
    return a.closest("li,article,tr,div") || a.parentElement || a;
  }

  // Find a value near a label word within a container's text lines.
  function fieldNear(container, labels) {
    // 1) definition lists
    for (const dt of container.querySelectorAll("dt,th,strong,b,.label,[class*=label]")) {
      const key = clean(dt.textContent).toLowerCase().replace(/:$/, "");
      if (labels.some((l) => key.includes(l))) {
        const dd = dt.nextElementSibling;
        if (dd) { const v = clean(dd.textContent); if (v) return v; }
      }
    }
    // 2) "Label: value" inside a single text block
    const text = clean(container.textContent);
    for (const l of labels) {
      const re = new RegExp(l + "\\s*[:\\-]\\s*([^\\n|]{2,80})", "i");
      const m = text.match(re);
      if (m) return clean(m[1]);
    }
    return "";
  }

  function scrapeResults() {
    const kindGuess = /can|contract|award|archived|closed/i.test(location.href) ? "award" : "opportunity";
    const records = [];
    for (const a of findResultLinks()) {
      const card = cardOf(a);
      const title = clean(a.textContent) ||
        clean((card.querySelector("h1,h2,h3,h4,[class*=title]") || {}).textContent);
      if (!title) continue;
      const cardText = clean(card.textContent);
      const dateMatches = cardText.match(new RegExp(DATE_RE, "g")) || [];
      records.push(OFN.normalize({
        href: a.href,
        title,
        kind: kindGuess,
        agency: fieldNear(card, ["agency", "buyer", "published by", "organisation", "department"]),
        category: fieldNear(card, ["category", "type", "unspsc", "class"]),
        location: fieldNear(card, ["location", "region", "delivery", "suburb"]),
        closing_at: fieldNear(card, ["clos", "deadline", "due"]) || dateMatches[dateMatches.length - 1] || "",
        published_at: fieldNear(card, ["publish", "released", "issued"]) || dateMatches[0] || "",
        amount_text: (cardText.match(MONEY_RE) || [""])[0],
        description: cardText.slice(0, 400),
      }));
    }
    return records;
  }

  function scrapeDetail() {
    const bodyText = clean(document.body.innerText);
    // Capture every label:value pair on the page for later re-parsing.
    const rawMap = {};
    for (const dt of document.querySelectorAll("dt,th,.label,[class*=label]")) {
      const key = clean(dt.textContent).toLowerCase().replace(/:$/, "");
      const dd = dt.nextElementSibling;
      if (key && dd) rawMap[key] = clean(dd.textContent);
    }
    const kind = /can|contract-award|\/notices\/|CNUUID=/i.test(location.href) ? "award" : "opportunity";
    const rec = OFN.normalize({
      href: location.href,
      kind,
      title: clean((document.querySelector("h1,h2,[class*=title]") || {}).textContent),
      agency: rawMap["agency"] || rawMap["buyer"] || rawMap["published by"] ||
        fieldNearBody(["agency", "buyer", "published by", "organisation"]),
      supplier_name: rawMap["supplier"] || rawMap["contract awarded to"] || rawMap["awarded to"] ||
        fieldNearBody(["supplier", "awarded to", "contractor"]),
      category: rawMap["category"] || rawMap["unspsc"] || "",
      location: rawMap["location"] || rawMap["region"] || rawMap["delivery location"] || "",
      closing_at: rawMap["closing date"] || rawMap["close date"] || "",
      published_at: rawMap["published"] || rawMap["publish date"] || "",
      amount_text: (bodyText.match(MONEY_RE) || [""])[0],
      contact_email: (bodyText.match(EMAIL_RE) || [""])[0],
      contact_phone: (bodyText.match(PHONE_RE) || [""])[0],
      abn: (bodyText.match(ABN_RE) || [""])[0],
      description: bodyText.slice(0, 1200),
    });
    rec.raw.labels = rawMap;
    return [rec];
  }

  function fieldNearBody(labels) {
    const text = clean(document.body.innerText);
    for (const l of labels) {
      const m = text.match(new RegExp(l + "\\s*[:\\-]\\s*([^\\n|]{2,80})", "i"));
      if (m) return clean(m[1]);
    }
    return "";
  }

  function scrape() {
    if (isDetailPage()) return { mode: "detail", records: scrapeDetail() };
    return { mode: "results", records: scrapeResults() };
  }

  // --- pagination: find the "next page" URL on a server-rendered results page ---
  function nextPageUrl() {
    // explicit rel=next / aria-label
    const rel = document.querySelector('a[rel="next"], a[aria-label*="Next" i], a[aria-label*="next" i]');
    if (rel && rel.href) return rel.href;
    // link whose text is "Next" / ">"
    for (const a of document.querySelectorAll("a[href]")) {
      const t = clean(a.textContent).toLowerCase();
      if ((t === "next" || t === "next page" || t === "›" || t === ">") && a.href) return a.href;
    }
    // increment ?page=N in the URL if a numbered pager exists
    const u = new URL(location.href);
    const p = parseInt(u.searchParams.get("page") || "1", 10);
    const hasHigher = [...document.querySelectorAll("a[href]")].some((a) => {
      const m = new URL(a.href, location.href).searchParams.get("page");
      return m && parseInt(m, 10) > p;
    });
    if (hasHigher) { u.searchParams.set("page", String(p + 1)); return u.toString(); }
    return null;
  }

  // --- auto-harvest loop across pages (persisted so it survives navigation) ---
  async function maybeAutoContinue() {
    const { autoHarvest } = await chrome.storage.local.get("autoHarvest");
    if (!autoHarvest || !autoHarvest.active) return;
    if (isDetailPage()) return; // only paginate results pages
    const res = scrape();
    await chrome.runtime.sendMessage({ type: "ADD_RECORDS", records: res.records, mode: res.mode });
    const cap = autoHarvest.maxPages || 40;
    const done = (autoHarvest.pages || 0) + 1;
    const next = nextPageUrl();
    if (next && done < cap) {
      autoHarvest.pages = done;
      await chrome.storage.local.set({ autoHarvest });
      const delay = 1500 + Math.floor(Math.random() * 2500); // human-paced, easy on the WAF
      setTimeout(() => { location.href = next; }, delay);
    } else {
      autoHarvest.active = false;
      await chrome.storage.local.set({ autoHarvest });
      await chrome.runtime.sendMessage({ type: "AUTO_DONE", pages: done });
    }
  }

  // messages from popup
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === "SCRAPE_PAGE") {
      const res = scrape();
      sendResponse(res);
      return true;
    }
    if (msg.type === "START_AUTO") {
      chrome.storage.local.set({
        autoHarvest: { active: true, pages: 0, maxPages: msg.maxPages || 40 },
      }).then(() => { maybeAutoContinue(); sendResponse({ ok: true }); });
      return true;
    }
    if (msg.type === "STOP_AUTO") {
      chrome.storage.local.set({ autoHarvest: { active: false } }).then(() => sendResponse({ ok: true }));
      return true;
    }
    if (msg.type === "DOM_DUMP") {
      // Debug: return the outerHTML of the first few result cards so selectors can be tuned.
      const links = findResultLinks().slice(0, 3);
      sendResponse({
        url: location.href,
        isResults: isResultsPage(),
        isDetail: isDetailPage(),
        linkCount: findResultLinks().length,
        sampleCards: links.map((a) => cardOf(a).outerHTML.slice(0, 2000)),
        nextPage: nextPageUrl(),
      });
      return true;
    }
  });

  // kick off auto-continue on each page load if active
  maybeAutoContinue();
})();
