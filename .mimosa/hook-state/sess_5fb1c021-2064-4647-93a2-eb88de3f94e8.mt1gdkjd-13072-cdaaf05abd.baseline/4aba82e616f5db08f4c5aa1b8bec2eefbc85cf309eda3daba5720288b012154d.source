"""product.py — Product Card, Inventory Snapshot, and SKU management for Ziman.
Phase 2 · Product & Inventory Intelligence

Implements:
  - product_card.v1 schema validation
  - inventory_snapshot.v1
  - photo_product_map.v1 read-only indexing
  - C1–C4 family rules with hard invariants
  - fail-closed ATP (Available-to-Promise) calculation
  - anti-misread guards (50 products ≠ 50 SKUs ≠ weekly capacity)

Standards: OLP-1, additive, $0 offline, stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────────────
FAMILIES = ("C1", "C2", "C3", "C4")
_ID_RE = re.compile(r"^ZM-C[1-4]-\d{4}$")
_C4_POLICIES = ("local_only", "pickup")
_C4_MAX_LEAD_DAYS = 3  # perishable — short lead time only

# ZIM catalog taxonomy (photo-grounded 35-product catalog). Additive to C1–C4:
# the CLI/template world keeps ZM-Cx-NNNN; the real photographed catalog uses
# ZIM-Fx-NN. Both are valid product_ids and share one ProductCard schema.
FAMILIES_ZIM = ("F1", "F2", "F3", "F4", "OTHER")
ALL_FAMILIES = FAMILIES + FAMILIES_ZIM
_ID_RE_ZIM = re.compile(r"^ZIM-(F[1-4]|OTHER)-\d{2}$")
ZIM_FAMILY_NAMES = {
    "F1": "F1_floral",
    "F2": "F2_framed",
    "F3": "F3_candy_basket",
    "F4": "F4_mixed_hamper",
    "OTHER": "OTHER",
}
# Families that are perishable-capable → local delivery, fail-closed (R0-F1):
# a mixed hamper (F4) can contain edibles, so it is treated as local-only even
# if a single record omits the perishable flag.
_ZIM_PERISHABLE_FAMILIES = ("F4",)

# ── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class CommercialBlock:
    cost_aud: float | None = None
    public_price_aud: float | None = None
    price_status: str = "unknown"  # unknown | draft | owner_approved

    def validate(self) -> list[str]:
        errs: list[str] = []
        if self.public_price_aud is not None and self.price_status != "owner_approved":
            errs.append("public_price without owner_approved price_status")
        return errs


@dataclass
class InventoryBlock:
    quantity_on_hand: int | None = None
    quantity_reserved: int = 0
    available_to_promise: int | None = None
    measured_at: str | None = None   # ISO8601
    evidence_class: str = "UNKNOWN"   # OWNER_INPUT | VERIFIED_FACT | INFERENCE | UNKNOWN

    def compute_atp(self) -> int | None:
        """ATP = max(on_hand - reserved, 0). None if on_hand unmeasured or stale."""
        if self.quantity_on_hand is None or not self.measured_at:
            return None
        if self.quantity_on_hand < 0 or self.quantity_reserved < 0:
            return None
        return max(self.quantity_on_hand - self.quantity_reserved, 0)

    def is_fresh(self, max_hours: int = 168) -> bool:
        """Inventory data older than max_hours (default one week) is stale.

        Fail closed: an invalid, timezone-naive, future, or missing timestamp is
        not fresh.  Product inventory must be recorded in ISO-8601 with an
        explicit timezone (normally UTC).
        """
        if not self.measured_at or not isinstance(max_hours, int) or max_hours < 0:
            return False
        try:
            measured = datetime.fromisoformat(self.measured_at)
            if measured.tzinfo is None:
                return False
            age_seconds = (datetime.now(timezone.utc) - measured).total_seconds()
            return 0 <= age_seconds <= max_hours * 3600
        except (TypeError, ValueError, OverflowError):
            return False


@dataclass
class ProductCard:
    """schema_version: product_card.v1"""
    product_id: str = ""
    family_id: str = ""            # C1 | C2 | C3 | C4
    title: str = ""
    status: str = "draft"          # draft | active | reserved | sold | archived
    classification: dict[str, Any] = field(default_factory=dict)
    inventory: InventoryBlock = field(default_factory=InventoryBlock)
    commercial: CommercialBlock = field(default_factory=CommercialBlock)
    fulfilment: dict[str, Any] = field(default_factory=dict)
    assets: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    governance: dict[str, Any] = field(default_factory=dict)

    # ── validation ────────────────────────────────────────────────────────
    def validate(self) -> list[str]:
        errs: list[str] = []
        # ID format — accept the ZM-Cx-NNNN (CLI) or ZIM-Fx-NN (catalog) scheme.
        id_ok = _ID_RE.match(self.product_id) or _ID_RE_ZIM.match(self.product_id)
        if not id_ok:
            errs.append(f"invalid product_id: {self.product_id!r} (expected ZM-Cx-NNNN or ZIM-Fx-NN)")
        # Family
        if self.family_id not in ALL_FAMILIES:
            errs.append(f"invalid family_id: {self.family_id!r}")
        # ID-family consistency
        if id_ok and self.family_id in ALL_FAMILIES:
            if f"-{self.family_id}-" not in self.product_id:
                errs.append(f"product_id family mismatch: {self.product_id} vs {self.family_id}")
        # C4 invariants
        cls_perishable = self.classification.get("perishable")
        policy = self.fulfilment.get("policy")
        if self.family_id == "C4":
            if cls_perishable is not True:
                errs.append("C4 must have classification.perishable=true")
            if policy not in _C4_POLICIES:
                errs.append(f"C4 policy must be local_only|pickup, got {policy!r}")
            lead = self.fulfilment.get("lead_time_days")
            if lead is not None and lead > _C4_MAX_LEAD_DAYS:
                errs.append(f"C4 lead_time_days must be ≤{_C4_MAX_LEAD_DAYS}")
        # ZIM F-family invariants (additive; mirrors C4 for perishable catalog items)
        if self.family_id in FAMILIES_ZIM:
            zim_perishable = self.family_id in _ZIM_PERISHABLE_FAMILIES or cls_perishable is True
            if zim_perishable:
                if policy not in _C4_POLICIES:
                    errs.append(f"perishable {self.family_id} policy must be local_only|pickup, got {policy!r}")
                lead = self.fulfilment.get("lead_time_days")
                if lead is not None and lead > _C4_MAX_LEAD_DAYS:
                    errs.append(f"perishable {self.family_id} lead_time_days must be ≤{_C4_MAX_LEAD_DAYS}")
        # Price gate
        errs.extend(self.commercial.validate())
        # Delivery promise
        if self.fulfilment.get("delivery_promise_authority"):
            errs.append("delivery_promise_authority must be false (agent cannot promise)")
        # ATP consistency
        computed = self.inventory.compute_atp()
        declared = self.inventory.available_to_promise
        if declared is not None:
            if computed is None or not self.inventory.is_fresh():
                errs.append("ATP set but on_hand unmeasured/stale (fail-closed)")
            elif declared != computed:
                errs.append(f"ATP mismatch: declared={declared}, computed={computed}")
        # Quantity sanity
        for k in ("quantity_on_hand", "quantity_reserved"):
            v = getattr(self.inventory, k)
            if v is not None and (not isinstance(v, int) or v < 0):
                errs.append(f"{k} must be non-negative int or null")
        return errs

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = "product_card.v1"
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ProductCard":
        data = dict(data)
        data.pop("schema_version", None)
        inv = data.pop("inventory", {})
        com = data.pop("commercial", {})
        return cls(
            inventory=InventoryBlock(**inv),
            commercial=CommercialBlock(**com),
            **data,
        )


@dataclass
class InventorySnapshot:
    """schema_version: inventory_snapshot.v1 — one owner counting session."""
    snapshot_id: str = ""
    measured_at: str = ""           # ISO8601
    measured_by: str = "owner"      # owner | operator (never agent)
    method: str = ""                # physical_count | photo_estimate | partial
    totals: dict[str, Any] = field(default_factory=dict)
    families: dict[str, Any] = field(default_factory=dict)
    capacity: dict[str, Any] = field(default_factory=dict)
    conflicts_acknowledged: list[str] = field(default_factory=list)
    governance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = "inventory_snapshot.v1"
        return d


@dataclass
class PhotoProductMap:
    """schema_version: photo_product_map.v1 — read-only metadata."""
    map_id: str = ""
    created_at: str = ""
    entries: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = "photo_product_map.v1"
        return d


# ── Pure Functions ─────────────────────────────────────────────────────────

def valid_product_id(pid: str) -> bool:
    return bool(_ID_RE.match(pid or "") or _ID_RE_ZIM.match(pid or ""))


def next_zim_product_id(family_id: str, existing_ids: list[str]) -> str:
    """Generate next ZIM-Fx-NN id (catalog scheme). Fail-closed on bad family."""
    if family_id not in FAMILIES_ZIM:
        raise ValueError(f"invalid ZIM family: {family_id}")
    pattern = re.compile(rf"^ZIM-{re.escape(family_id)}-(\d{{2}})$")
    nums = [int(m.group(1)) for eid in existing_ids for m in [pattern.match(eid)] if m]
    return f"ZIM-{family_id}-{max(nums, default=0) + 1:02d}"


def next_product_id(family_id: str, existing_ids: list[str]) -> str:
    """Generate next ZM-Cx-NNNN ID. Fail-closed: family must be C1-C4."""
    if family_id not in FAMILIES:
        raise ValueError(f"invalid family: {family_id}")
    nums = []
    pattern = re.compile(rf"^ZM-{family_id}-(\d{{4}})$")
    for eid in existing_ids:
        m = pattern.match(eid)
        if m:
            nums.append(int(m.group(1)))
    next_n = max(nums, default=0) + 1
    return f"ZM-{family_id}-{next_n:04d}"


def anti_misread_guard(claim: str) -> dict[str, Any]:
    """Block claims that misinterpret 50 products as SKUs or capacity."""
    text = (claim or "").lower()
    blocked: list[str] = []
    if re.search(r"50\s*(unique\s*)?sku", text):
        blocked.append("50-products-as-SKUs")
    if re.search(r"50\s*(per|/)\s*week|capacity\s*(of|=)?\s*50", text):
        blocked.append("50-products-as-capacity")
    if re.search(r"30\s*(per|/)\s*week\b.*(verified|measured|confirmed)", text):
        blocked.append("30/week-claimed-verified (CF-01 open)")
    return {"allowed": not blocked, "blocked_patterns": blocked}


def capacity_fail_closed(ceiling: int | None, owner_revalidated: bool = False) -> int:
    """Until owner revalidates, effective proposal ceiling = min(ceiling, 6).
    6 = observed approximate historical rate, used as fail-closed fallback."""
    if ceiling is None or not isinstance(ceiling, (int, float)) or ceiling <= 0:
        return 0
    if not owner_revalidated:
        return min(int(ceiling), 6)
    return int(ceiling)


# ── File I/O (safe, read-only where possible) ───────────────────────────────

def load_product_cards(dir_path: Path) -> list[ProductCard]:
    """Load all product_card.v1 YAML/JSON files from directory."""
    cards: list[ProductCard] = []
    if not dir_path.exists():
        return cards
    paths = sorted(dir_path.glob("*.json")) + sorted(dir_path.glob("product-*.yaml"))
    for p in paths:
        try:
            text = p.read_text("utf-8")
            # JSON is the CLI write format; YAML remains supported for templates.
            data = json.loads(text) if p.suffix == ".json" else _minimal_yaml_parse(text)
            card = ProductCard.from_dict(data)
            if card.validate() == []:
                cards.append(card)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            # A malformed local draft must not crash a status/report command.
            continue
    return cards


def save_product_card(card: ProductCard, dir_path: Path) -> Path:
    """Save product card as JSON. Returns path."""
    dir_path.mkdir(parents=True, exist_ok=True)
    out = dir_path / f"{card.product_id}.json"
    out.write_text(json.dumps(card.to_dict(), ensure_ascii=False, indent=2), "utf-8")
    return out


def _minimal_yaml_parse(text: str) -> dict[str, Any]:
    """Bare-bones YAML parser for simple flat structures (no external deps).
    Falls back to returning empty dict on complex nested YAML."""
    # If PyYAML is available, use it
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except Exception:
        pass
    # Simple key: value line parser
    result: dict[str, Any] = {}
    current_key: str | None = None
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        # Match "key: value"
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            val = m.group(2).strip()
            # Try int/float/bool/null
            if val.lower() in ("null", "~", ""):
                result[current_key] = None
            elif val.lower() == "true":
                result[current_key] = True
            elif val.lower() == "false":
                result[current_key] = False
            elif re.match(r"^-?\d+$", val):
                result[current_key] = int(val)
            elif re.match(r"^-?\d+\.\d+$", val):
                result[current_key] = float(val)
            else:
                result[current_key] = val
    return result


# ── Photo Indexing ─────────────────────────────────────────────────────────

def hash_photo(path: Path) -> str:
    """SHA256 of file bytes — for provenance."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def index_photos(photo_dir: Path, scope: str = "08 - Assets/Photos/WhatsApp-2026") -> PhotoProductMap:
    """Read-only index of direct photo files in an explicitly supplied folder.

    This function neither discovers other image folders nor assigns identities.
    Paths are stored relative to the supplied folder, avoiding an assumption
    about the caller's vault root.
    """
    mp = PhotoProductMap(
        map_id=f"ZM-PHOTO-MAP-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    if not photo_dir.is_dir():
        return mp
    for p in sorted(photo_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic"):
            mp.entries.append({
                "photo_path": str(p.relative_to(photo_dir)),
                "sha256": hash_photo(p),
                "product_id": None,
                "match_evidence": "",
                "match_class": "UNKNOWN",
                "privacy_flag": False,
            })
    return mp
