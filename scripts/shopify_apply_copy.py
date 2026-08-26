#!/usr/bin/env python3
"""Dry-default Shopify copy applier for Ziman COPY-DRAFTS.json.

NEVER invents copy. Reads drafts from JSON path.
Applies ONLY when:
  - OFN_ZIMAN_COPY_APPLY=1
  - owner SKU list provided (--skus A,B or --skus-file)
Otherwise prints DRY and exits 0.

Read secrets from env / ~/.config/ofn — never print token values.
"""
from __future__ import annotations
import argparse, json, os, sys, pathlib, urllib.request

def load_env_files():
    for p in (
        pathlib.Path.home() / ".config/ofn/secrets.env",
        pathlib.Path.home() / ".config/ofn/node.env",
    ):
        if not p.exists():
            continue
        for line in p.read_text(errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)

def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Ziman copy drafts to Shopify (dry-default)")
    ap.add_argument("drafts_json", help="Path to COPY-DRAFTS.json")
    ap.add_argument("--skus", default="", help="Comma-separated owner-approved SKUs")
    ap.add_argument("--skus-file", default="", help="File with one SKU per line")
    ap.add_argument("--title-field", choices=["title_en", "title_fa"], default="title_fa",
                    help="Which draft title to push as Shopify title")
    ap.add_argument("--body-field", choices=["body_en", "body_fa", "both_html"], default="both_html",
                    help="Body source; both_html wraps FA+EN")
    args = ap.parse_args()

    path = pathlib.Path(args.drafts_json)
    if not path.exists():
        print(f"ERROR missing drafts file: {path}", file=sys.stderr)
        return 2
    doc = json.loads(path.read_text(encoding="utf-8"))
    drafts = {d["sku"]: d for d in doc.get("drafts", [])}

    approved = set()
    if args.skus.strip():
        approved |= {s.strip() for s in args.skus.split(",") if s.strip()}
    if args.skus_file:
        fp = pathlib.Path(args.skus_file)
        if not fp.exists():
            print(f"ERROR missing skus file: {fp}", file=sys.stderr)
            return 2
        approved |= {ln.strip() for ln in fp.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}

    apply_flag = os.environ.get("OFN_ZIMAN_COPY_APPLY", "").strip() == "1"
    targets = [s for s in approved if s in drafts]
    missing = sorted(approved - set(drafts))

    print("shopify_apply_copy.py")
    print(f"  drafts: {path}")
    print(f"  draft_count: {len(drafts)}")
    print(f"  OFN_ZIMAN_COPY_APPLY: {os.environ.get('OFN_ZIMAN_COPY_APPLY', '')!r}")
    print(f"  approved_skus: {sorted(approved)}")
    print(f"  applyable: {targets}")
    if missing:
        print(f"  skus_not_in_drafts: {missing}")

    if not apply_flag or not approved:
        print("DRY: no Shopify writes. Set OFN_ZIMAN_COPY_APPLY=1 AND provide --skus/--skus-file to apply.")
        for sku in (targets or list(drafts)[:3]):
            d = drafts[sku]["draft"]
            print(f"  would_update {sku}: title[{args.title_field}]={d[args.title_field][:60]!r}...")
        return 0

    load_env_files()
    token = os.environ.get("OFN_SHOPIFY_ADMIN_TOKEN", "")
    domain = os.environ.get("OFN_SHOPIFY_SHOP_DOMAIN", "")
    if not token or not domain:
        print("ERROR missing OFN_SHOPIFY_ADMIN_TOKEN or OFN_SHOPIFY_SHOP_DOMAIN", file=sys.stderr)
        return 3

    ok_n = fail_n = 0
    for sku in targets:
        entry = drafts[sku]
        d = entry["draft"]
        gid = entry.get("shopify_gid")
        if not gid:
            print(f"FAIL {sku}: no shopify_gid in draft")
            fail_n += 1
            continue
        title = d[args.title_field]
        if args.body_field == "both_html":
            body_html = (
                f"<p dir=\"rtl\">{html_escape(d['body_fa'])}</p>"
                f"<p>{html_escape(d['body_en'])}</p>"
            )
        else:
            body_html = f"<p>{html_escape(d[args.body_field])}</p>"
        tags = d.get("tags") or []
        mutation = {
            "query": (
                "mutation productUpdate($input: ProductInput!) {"
                "  productUpdate(input: $input) {"
                "    product { id title }"
                "    userErrors { field message }"
                "  }"
                "}"
            ),
            "variables": {
                "input": {
                    "id": gid,
                    "title": title,
                    "descriptionHtml": body_html,
                    "tags": tags,
                }
            },
        }
        req = urllib.request.Request(
            f"https://{domain}/admin/api/2024-10/graphql.json",
            data=json.dumps(mutation).encode(),
            headers={
                "X-Shopify-Access-Token": token,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            errs = (data.get("data") or {}).get("productUpdate", {}).get("userErrors") or []
            if errs or data.get("errors"):
                print(f"FAIL {sku}: {errs or data.get('errors')}")
                fail_n += 1
            else:
                print(f"OK {sku}")
                ok_n += 1
        except Exception as e:
            print(f"FAIL {sku}: {type(e).__name__}")
            fail_n += 1
    print(f"done ok={ok_n} fail={fail_n}")
    return 0 if fail_n == 0 else 4

def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )

if __name__ == "__main__":
    raise SystemExit(main())
