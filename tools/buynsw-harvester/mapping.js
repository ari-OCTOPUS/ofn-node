// mapping.js — shared normalization + painting filter (mirrors ofn/agents/h1_buysw.py)
// Loaded in both content script and (imported) by popup for consistent output shape.

const OFN = (() => {
  const ACCEPT_KEYWORDS = [
    "painting", "repaint", "repainting", "external painting",
    "internal painting", "coating", "facade repaint", "paint work", "paintwork",
  ];
  const REJECT_KEYWORDS = [
    "paint supply", "paint product", "art gallery", "exhibition",
    "artwork", "art collection", "painting exhibition", "paints and primers", "bulk paint",
  ];
  // Sydney + ~100km service area (from OCDS xNSWRegions scheme)
  const ACCEPT_REGIONS = [
    "sydney", "cumberland/prospect", "cumberland", "prospect", "nepean",
    "northern sydney", "inner west", "south east sydney", "south west sydney",
    "central coast", "illawarra", "hunter", "newcastle", "wollongong",
  ];

  const GUID = /[0-9A-Fa-f]{8}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{12}/;

  function stripHtml(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.innerHTML = s;
    return (d.textContent || d.innerText || "").replace(/\s+/g, " ").trim();
  }

  function extractUuid(hrefOrText) {
    if (!hrefOrText) return "";
    const m = String(hrefOrText).match(GUID);
    return m ? m[0].replace(/-/g, "").toUpperCase() : "";
  }

  function isPainting(text) {
    const t = (text || "").toLowerCase();
    if (REJECT_KEYWORDS.some((k) => t.includes(k))) return false;
    return ACCEPT_KEYWORDS.some((k) => t.includes(k));
  }

  function inServiceArea(text) {
    const t = (text || "").toLowerCase();
    if (!t) return null; // unknown
    return ACCEPT_REGIONS.some((r) => t.includes(r));
  }

  // Normalize a raw scraped record into the OFN lead/tender shape.
  function normalize(raw) {
    const uuid = raw.uuid || extractUuid(raw.href) || extractUuid(raw.title);
    const blob = [raw.title, raw.description, raw.category, raw.agency]
      .filter(Boolean).join(" ");
    const painting = isPainting(blob);
    const geo = inServiceArea([raw.location, raw.agency, raw.title].filter(Boolean).join(" "));
    return {
      tender_id: uuid ? `lead:tender:buysw:${uuid}` : `lead:tender:buysw:href:${raw.href || ""}`,
      channel: "buysw_web",
      kind: raw.kind || "opportunity",        // opportunity | award(CAN)
      title: raw.title || "",
      buyer_name: raw.agency || "",
      description: raw.description || "",
      location: raw.location || "",
      category: raw.category || "",
      closing_at: raw.closing_at || "",
      published_at: raw.published_at || "",
      amount_text: raw.amount_text || "",
      supplier_name: raw.supplier_name || "",   // set on CAN detail pages
      contact_email: raw.contact_email || "",
      contact_phone: raw.contact_phone || "",
      abn: raw.abn || "",
      uuid,
      source: "buy.nsw.gov.au",
      source_url: raw.href || location.href,
      access_mode: "browser_session",           // NOT official_api — WAF bypassed via real session
      evidence_status: "unverified",
      status: "received",
      // classification hints for downstream Python filter/scoring
      _painting_hint: painting,
      _in_service_area: geo,                     // true / false / null(unknown)
      _scraped_at: new Date().toISOString(),
      raw,                                       // full captured label:value map, for later re-parsing
    };
  }

  return { normalize, isPainting, inServiceArea, extractUuid, stripHtml, GUID };
})();

// Make available to service worker via importScripts and to content script global.
if (typeof self !== "undefined") self.OFN = OFN;
