import test from "node:test";
import assert from "node:assert/strict";
import {
  CARD_ORDER,
  cardRows,
  renderSurface,
  verdictMeta,
} from "../src/pages/surface.js";

test("surface exposes exactly the seven owner cards in order", () => {
  assert.deepEqual(CARD_ORDER, [
    "command_center",
    "self_model",
    "doctor",
    "economic_learning",
    "owner_queue",
    "telegram_bridge",
    "receipts_sync",
  ]);
});

test("only a consistent verdict is green; incomplete stays neutral", () => {
  assert.equal(verdictMeta("consistent").tone, "ok");
  assert.equal(verdictMeta("incomplete").tone, "warn");
  assert.equal(verdictMeta(undefined).tone, "neutral");
  assert.notEqual(verdictMeta("incomplete").tone, "ok");
  assert.notEqual(verdictMeta(undefined).tone, "ok");
});

test("an inconsistent verdict is loud and bad-toned", () => {
  const meta = verdictMeta("inconsistent");
  assert.equal(meta.tone, "bad");
  assert.match(meta.label, /INCONSISTENT/);
});

test("unknown numbers render as unknown, never as zero or green", () => {
  const rows = cardRows("command_center", {
    numbers: [
      { id: "main_sha", value: null, truth: "UNKNOWN" },
      { id: "verified_payments", value: null, truth: "UNKNOWN" },
      { id: "owner_queue_count", value: null, truth: "UNKNOWN" },
    ],
    disagreements: [],
  });
  assert.equal(rows.length, 3);
  for (const row of rows) {
    assert.match(row.value, /نامعلوم/);
    assert.notEqual(row.value, "۰");
    assert.notEqual(row.value, "0");
  }
});

test("a known zero stays a zero and disagreements are listed as rows", () => {
  const rows = cardRows("command_center", {
    numbers: [
      { id: "main_sha", value: "aa12", truth: "REPO_VERIFIED" },
      { id: "verified_payments", value: 0, truth: "REPO_VERIFIED" },
    ],
    disagreements: [{ left: "main_sha", right: "economic_code_sha" }],
  });
  assert.match(rows[1].value, /^۰$/);
  const disagreement = rows.find((row) => row.label === "ناسازگاری");
  assert.match(disagreement.value, /main_sha/);
  assert.match(disagreement.value, /economic_code_sha/);
});

test("missing card payloads degrade to unknown rows, not fabrications", () => {
  for (const cardId of CARD_ORDER) {
    const rows = cardRows(cardId, undefined);
    assert.ok(rows.length > 0, cardId);
    for (const row of rows) {
      assert.match(String(row.value), /نامعلوم/);
    }
  }
});

test("renderSurface mounts the seven cards into a grid", () => {
  const created = [];
  globalThis.document = {
    createElement(tag) {
      const node = {
        tag,
        className: "",
        children: [],
        dataset: {},
        attributes: {},
        textContent: "",
        append(child) {
          this.children.push(child);
        },
        removeChild(child) {
          this.children = this.children.filter((entry) => entry !== child);
        },
        get firstChild() {
          return this.children[0] ?? null;
        },
        setAttribute(name, value) {
          this.attributes[name] = value;
        },
        focus() {},
      };
      created.push(node);
      return node;
    },
  };
  try {
    const page = renderSurface({
      schema_version: "2.0",
      status: "degraded",
      data: {
        coherence: { verdict: "inconsistent", numbers: [], disagreements: [] },
        card_status: {},
        cards: {},
      },
    });
    assert.ok(page);
    for (const cardId of CARD_ORDER) {
      assert.ok(
        created.some((node) => node.dataset.card === cardId),
        cardId,
      );
    }
    assert.ok(created.some((node) => node.className.includes("card-grid")));
  } finally {
    delete globalThis.document;
  }
});
