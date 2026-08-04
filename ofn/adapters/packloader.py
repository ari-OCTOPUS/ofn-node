"""Load business packs from disk into kernel `PackSpec` objects.

Two formats are accepted: JSON, and the small subset of YAML this project
actually uses. The subset parser exists because the surrounding vault is
YAML throughout, and a pack the owner cannot read in a text editor is a pack
that drifts out of date. It is ~120 lines of stdlib rather than a dependency,
and it is deliberately strict: anything outside the subset raises rather than
being silently mis-parsed. A config parser that guesses is worse than one
that refuses.

Supported YAML subset:
    key: scalar                 int, float, true/false, null, bare or quoted string
    key:                        nested mapping, two-space indent
      sub: value
    key:                        block sequence
      - item
    key: [a, b, c]              inline sequence
    # comment                   whole-line or trailing

Not supported (raises `PackError`): anchors, aliases, multi-document files,
block scalars, flow mappings, tabs for indentation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from ..kernel.domain import (UNRESOLVED, Confidence, Currency, Locale,
                             PackSpec, RiskTier, TenantId)
from ..kernel.errors import PackError

# Exactly one market is implemented end to end. The registry is the single
# place that says so, and `spec_from_mapping` refuses anything absent from it
# rather than falling back — a silent fallback to AUD would put an Australian
# price in front of a partner selling somewhere else, which is the precise
# failure this whole object exists to prevent.
SUPPORTED_LOCALES: Mapping[str, Mapping[str, Any]] = {
    "en-AU": {
        "currency": {"code": "AUD", "symbol": "$", "decimals": 2},
        # 10% is a fact about the country. Whether this business charges it is
        # a fact about the business, so `tax_status` stays unresolved until
        # the owner answers.
        "tax_rate": 0.10,
        "tax_pricing": "inclusive",
        "legal": ("australian_consumer_law",),
    },
}

_TAX_STATUS = {"registered", "not_registered", UNRESOLVED}
_TAX_PRICING = {"inclusive", "exclusive"}

_TRUE = {"true", "yes", "on"}
_FALSE = {"false", "no", "off"}
_NULL = {"null", "~", ""}


def _scalar(raw: str) -> Any:
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    low = s.lower()
    if low in _NULL:
        return None
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _strip_comment(line: str) -> str:
    """Remove a trailing comment, respecting quotes."""
    out, quote = [], None
    for ch in line:
        if quote:
            if ch == quote:
                quote = None
            out.append(ch)
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def parse_yaml_subset(text: str) -> Mapping[str, Any]:
    """Parse the documented subset. Raises `PackError` on anything else."""
    rows: list[tuple[int, str]] = []
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw.split("#", 1)[0]:
            raise PackError(f"line {n}: tabs are not valid indentation")
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise PackError(f"line {n}: indentation must be a multiple of two spaces")
        rows.append((indent, line.strip()))

    pos = 0

    def block(indent: int) -> Any:
        nonlocal pos
        # sequence?
        if pos < len(rows) and rows[pos][0] == indent and rows[pos][1].startswith("- "):
            items: list[Any] = []
            while pos < len(rows) and rows[pos][0] == indent and rows[pos][1].startswith("- "):
                items.append(_scalar(rows[pos][1][2:]))
                pos += 1
            return items
        # mapping
        out: dict[str, Any] = {}
        while pos < len(rows) and rows[pos][0] == indent:
            ind, content = rows[pos]
            if ":" not in content:
                raise PackError(f"expected 'key: value', got {content!r}")
            key, _, rest = content.partition(":")
            key, rest = key.strip(), rest.strip()
            pos += 1
            if rest.startswith("[") and rest.endswith("]"):
                inner = rest[1:-1].strip()
                out[key] = [_scalar(p) for p in inner.split(",")] if inner else []
            elif rest:
                out[key] = _scalar(rest)
            else:
                if pos < len(rows) and rows[pos][0] > ind:
                    out[key] = block(rows[pos][0])
                else:
                    out[key] = None
        return out

    if not rows:
        return {}
    result = block(rows[0][0])
    if pos != len(rows):
        raise PackError(f"could not parse line {pos + 1}: {rows[pos][1]!r}")
    if not isinstance(result, dict):
        raise PackError("a pack must be a mapping at the top level")
    return result


def spec_from_mapping(data: Mapping[str, Any]) -> PackSpec:
    """Validate a parsed mapping into a `PackSpec`.

    Every field is checked here rather than at use-time, so a malformed pack
    fails at boot with a precise message instead of at 3am with a stack trace.
    """
    if not isinstance(data, Mapping):
        raise PackError("pack must be a mapping")

    try:
        tenant = TenantId(str(data["tenant"]))
    except KeyError:
        raise PackError("pack is missing required field 'tenant'") from None
    except ValueError as exc:
        raise PackError(f"invalid tenant id: {exc}") from None

    cap = data.get("capacity_units_per_week", 0)
    if not isinstance(cap, int) or isinstance(cap, bool):
        raise PackError(f"{tenant}: capacity_units_per_week must be an integer")

    facts_raw = data.get("required_facts") or {}
    if not isinstance(facts_raw, Mapping):
        raise PackError(f"{tenant}: required_facts must be a mapping of fact -> confidence")
    facts: dict[str, Confidence] = {}
    for k, v in facts_raw.items():
        try:
            facts[str(k)] = Confidence(str(v))
        except ValueError:
            raise PackError(
                f"{tenant}: fact {k!r} has unknown confidence {v!r}; "
                f"expected one of {[c.value for c in Confidence]}"
            ) from None

    gates_raw = data.get("gates") or []
    if not isinstance(gates_raw, list):
        raise PackError(f"{tenant}: gates must be a list")
    gates = tuple(str(g) for g in gates_raw)

    ov_raw = data.get("risk_overrides") or {}
    if not isinstance(ov_raw, Mapping):
        raise PackError(f"{tenant}: risk_overrides must be a mapping of action -> tier")
    overrides: dict[str, RiskTier] = {}
    for k, v in ov_raw.items():
        try:
            overrides[str(k)] = RiskTier(str(v).lower())
        except ValueError:
            raise PackError(
                f"{tenant}: action {k!r} has unknown tier {v!r}; "
                f"expected one of {[t.value for t in RiskTier]}"
            ) from None

    share = data.get("quota_share", 0.0)
    if isinstance(share, bool) or not isinstance(share, (int, float)):
        raise PackError(f"{tenant}: quota_share must be a number")

    meta = _question_meta(tenant, data.get("questions") or {}, facts)
    locale = _locale(tenant, data.get("locale"))

    try:
        return PackSpec(
            tenant=tenant,
            capacity_units_per_week=cap,
            required_facts=facts,
            gates=gates,
            risk_overrides=overrides,
            quota_share=float(share),
            question_meta=meta,
            locale=locale,
        )
    except ValueError as exc:
        raise PackError(f"{tenant}: {exc}") from None


def _locale(tenant: TenantId, raw: Any) -> Locale:
    """Build the locale, refusing any market that is not fully implemented.

    A pack with no `locale:` block gets the default one — but the default is
    still a real, named locale that had to be in `SUPPORTED_LOCALES`, not an
    implicit set of assumptions scattered through the code.
    """
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise PackError(f"{tenant}: locale must be a mapping")

    loc_id = str(raw.get("id", "en-AU"))
    base = SUPPORTED_LOCALES.get(loc_id)
    if base is None:
        raise PackError(
            f"{tenant}: unsupported_locale {loc_id!r}; implemented locales are "
            f"{sorted(SUPPORTED_LOCALES)}. Add one deliberately — currency, "
            f"tax, timezone, rails and law all have to be answered together.")

    cur = dict(base["currency"])
    cur_raw = raw.get("currency") or {}
    if not isinstance(cur_raw, Mapping):
        raise PackError(f"{tenant}: locale.currency must be a mapping")
    if cur_raw.get("code") and str(cur_raw["code"]) != cur["code"]:
        # The currency is a property of the locale, not a free choice beside
        # it. Letting a pack say en-AU with EUR would rebuild the exact
        # inconsistency the locale object removes.
        raise PackError(
            f"{tenant}: locale {loc_id} is {cur['code']}, pack says "
            f"{cur_raw['code']!r}; currency follows the locale")

    tax_raw = raw.get("tax") or {}
    if not isinstance(tax_raw, Mapping):
        raise PackError(f"{tenant}: locale.tax must be a mapping")
    status = str(tax_raw.get("status", UNRESOLVED))
    if status not in _TAX_STATUS:
        raise PackError(
            f"{tenant}: locale.tax.status must be one of {sorted(_TAX_STATUS)}, "
            f"got {status!r}")
    pricing = str(tax_raw.get("pricing", base["tax_pricing"]))
    if pricing not in _TAX_PRICING:
        raise PackError(
            f"{tenant}: locale.tax.pricing must be one of {sorted(_TAX_PRICING)}, "
            f"got {pricing!r}")

    def _seq(key: str) -> tuple[str, ...]:
        v = raw.get(key) or ()
        if isinstance(v, str) or not isinstance(v, (list, tuple)):
            raise PackError(f"{tenant}: locale.{key} must be a list")
        return tuple(str(x) for x in v)

    try:
        return Locale(
            id=loc_id,
            currency=Currency(cur["code"], cur["symbol"], int(cur["decimals"])),
            timezone=str(raw.get("timezone", UNRESOLVED)),
            tax_status=status,
            tax_rate=float(base["tax_rate"]),
            tax_pricing=pricing,
            payment_rails=_seq("payment_rails"),
            platforms=_seq("platforms"),
            legal=tuple(base["legal"]),
        )
    except ValueError as exc:
        raise PackError(f"{tenant}: locale: {exc}") from None


_META_FIELDS = {"label", "hint", "unit", "options", "min", "max", "default",
                "placeholder"}


def _question_meta(
    tenant: TenantId,
    raw: Any,
    facts: Mapping[str, Confidence],
) -> dict[str, dict[str, Any]]:
    """Validate the optional per-fact question wording.

    Checked here rather than trusted at render time because the failure this
    prevents is silent: a mistyped fact key produces wording that never
    appears, and the partner is shown a raw key like `offer.cogs_per_family`
    with no clue that a sentence for it exists three lines away in the pack.
    """
    if not isinstance(raw, Mapping):
        raise PackError(f"{tenant}: questions must be a mapping of fact -> wording")

    out: dict[str, dict[str, Any]] = {}
    for key, spec in raw.items():
        key = str(key)
        if key not in facts:
            raise PackError(
                f"{tenant}: questions has wording for {key!r}, which is not in "
                f"required_facts; known facts are {sorted(facts)}")
        if not isinstance(spec, Mapping):
            raise PackError(f"{tenant}: questions.{key} must be a mapping")

        unknown = set(map(str, spec)) - _META_FIELDS
        if unknown:
            raise PackError(
                f"{tenant}: questions.{key} has unknown field(s) "
                f"{sorted(unknown)}; allowed are {sorted(_META_FIELDS)}")

        entry: dict[str, Any] = {}
        for field_name in ("label", "hint", "unit", "placeholder"):
            if spec.get(field_name) is not None:
                entry[field_name] = str(spec[field_name])
        for field_name in ("min", "max", "default"):
            value = spec.get(field_name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise PackError(
                    f"{tenant}: questions.{key}.{field_name} must be a number")
            entry[field_name] = value
        if spec.get("options") is not None:
            options = spec["options"]
            if not isinstance(options, list) or not options:
                raise PackError(
                    f"{tenant}: questions.{key}.options must be a non-empty list")
            entry["options"] = [str(o) for o in options]

        if "min" in entry and "max" in entry and entry["min"] > entry["max"]:
            raise PackError(f"{tenant}: questions.{key} has min above max")
        out[key] = entry
    return out


def load_pack(path: str) -> PackSpec:
    """Read one pack file. `.json` is parsed as JSON, anything else as the subset."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if path.endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise PackError(f"{path}: invalid JSON — {exc}") from None
    else:
        data = parse_yaml_subset(text)
    return spec_from_mapping(data)


def load_dir(directory: str) -> dict[str, PackSpec]:
    """Load every pack in a directory, keyed by tenant id.

    Two packs claiming the same tenant is a hard error: it means one of them
    is silently dead, and which one depends on filesystem ordering.
    """
    packs: dict[str, PackSpec] = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith((".yaml", ".yml", ".json", ".pack")):
            continue
        spec = load_pack(os.path.join(directory, name))
        if spec.tenant.value in packs:
            raise PackError(f"duplicate tenant {spec.tenant.value!r} in {name}")
        packs[spec.tenant.value] = spec
    if not packs:
        raise PackError(f"no packs found in {directory!r}")
    return packs
