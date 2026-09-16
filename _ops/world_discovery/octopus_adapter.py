"""octopus_adapter.py — public API اندام کشف دنیای واقعی.

قرارداد عمومی (بند ۱۴):
  observe(direction) -> dict          جمع‌آوری کاندیداهای خام؛ بدون اثر بیرونی
  triangulate(candidate) -> dict       تأیید چندمنبعی، تناقض و تازگی
  discover(direction) -> dict          یک discovery receipt یا no-valid-discovery
  design_experiment(discovery) -> dict کوچک‌ترین آزمایش ابطال‌پذیر
  export_bundle(result, output_dir) -> dict   artifact اتمیک

ویژگی‌ها:
- pure-data (JSON serializable).
- side-effect بیرونی ندارد.
- result را به success تحمیل نمی‌کند.
- no-valid-discovery پشتیبانی می‌شود.
- owner gate پیش‌فرض NoOp → BLOCKED_BY_OWNER.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import (
    action_boundary,
    candidate_miner,
    competitor_intel,
    contradiction as contra_mod,
    experiment_designer,
    freshness as fresh_mod,
    novelty as novelty_mod,
    opportunity as opp_mod,
    public_web,
    report,
    scorer,
    source_policy,
)
from .contracts import (
    Discovery,
    Metrics,
    Opportunity,
    Source,
    STATUS_ACTIONABLE,
    STATUS_BLOCKED,
    STATUS_CANDIDATE,
    STATUS_CONTESTED,
    STATUS_TRIANGULATED,
    make_discovery_id,
)
from .direction_reader import load_direction

_DEFAULT_RETRIEVER: Optional[public_web.Retriever] = None


def set_retriever(retriever: Optional[public_web.Retriever]) -> None:
    """تزریق retriever (برای تست یا اتصال به cortex.web_research)."""
    global _DEFAULT_RETRIEVER
    _DEFAULT_RETRIEVER = retriever


def _get_retriever() -> public_web.Retriever:
    """به‌دست آوردن retriever فعال: تزریق‌شده → cortex fallback → stdlib fallback."""
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is not None:
        return _DEFAULT_RETRIEVER
    # تلاش برای reuse از cortex.web_research
    cr = public_web.try_cortex_retriever()
    if cr is not None:
        _DEFAULT_RETRIEVER = cr
        return cr
    _DEFAULT_RETRIEVER = public_web.StdlibRetriever()
    return _DEFAULT_RETRIEVER


# ──────────────────────────────────────────────────────
# observe — جمع‌آوری کاندیداهای خام
# ──────────────────────────────────────────────────────
def observe(direction: dict, *, now: Optional[datetime] = None,
            retriever: Optional[public_web.Retriever] = None,
            max_queries: int = 5) -> dict:
    """جمع‌آوری کاندیداهای خام از وب عمومی. بدون اثر بیرونی.

    خروجی: {observations, metrics_partial}
    """
    now = now or datetime.now(timezone.utc)
    ret = retriever or _get_retriever()
    competitors = direction.get("competitors", [])
    domain = direction.get("domain", "")

    queries = _build_queries(competitors, domain, max_queries)
    all_obs = []
    seen_urls = set()
    for q in queries:
        try:
            hits = ret.search(q, k=8) or []
        except Exception:
            hits = []
        for hit in hits:
            url = public_web.normalize_url(str(hit.get("url", "")))
            if not url or url in seen_urls:
                continue
            if not public_web.is_fetch_allowed(url):
                continue  # egress policy
            seen_urls.add(url)
            comp = _guess_competitor(hit, competitors)
            obs = public_web.hit_to_observation(hit, competitor=comp)
            all_obs.append(obs)

    # dedup
    all_obs = candidate_miner.dedupe_observations(all_obs)
    return {
        "schema": "world-discovery.observe.v1",
        "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "queries": queries,
        "observations": [o.as_dict() for o in all_obs],
        "observation_count": len(all_obs),
    }


def _build_queries(competitors: list[str], domain: str, max_q: int) -> list[str]:
    """ساخت queryهای تحقیق برای هر رقیب + تحلیل مقایسه‌ای."""
    queries = []
    # تحلیل مقایسه‌ای رقبا
    if len(competitors) >= 2:
        queries.append(f"{competitors[0]} vs {competitors[1]} AI agent 2026")
    for c in competitors:
        queries.append(f"{c} AI agent limitations weaknesses 2026")
        queries.append(f"{c} new release pricing 2026")
    # موضوع دامنه
    queries.append(f"{domain} AI agent architecture gap opportunity 2026")
    # محدود به max_q
    return queries[:max_q]


def _guess_competitor(hit: dict, competitors: list[str]) -> str:
    text = (str(hit.get("title", "")) + " " + str(hit.get("snippet", ""))).lower()
    for c in competitors:
        if c.lower() in text:
            return c
    return ""


# ──────────────────────────────────────────────────────
# triangulate — تأیید چندمنبعی + novelty + contradiction
# ──────────────────────────────────────────────────────
def triangulate(candidate: dict, *, now: Optional[datetime] = None,
                retriever: Optional[public_web.Retriever] = None,
                min_sources: int = 2) -> dict:
    """تأیید چندمنبعی، تناقض و تازگی یک کاندیدا.

    خروجی: {novelty, contradiction, evidence_receipt, status}
    """
    now = now or datetime.now(timezone.utc)
    ret = retriever or _get_retriever()

    claim = candidate.get("claim", "")
    sources = candidate.get("sources", []) or [
        o.get("source") for o in candidate.get("observations", [])
    ]

    # 1. novelty check
    novelty_receipt = novelty_mod.assess_novelty(claim)

    # 2. evidence sufficiency
    evidence = source_policy.evidence_sufficient(sources, min_independent=min_sources)

    # 3. contradiction search (active)
    contra = contra_mod.search_contradictions(
        claim,
        retriever=lambda q: ret.search(q, k=6),
        competitor=candidate.get("competitors", [""])[0] if candidate.get("competitors") else "",
        max_queries=2,
    )

    # 4. freshness
    fresh = fresh_mod.compute_freshness(sources, observed_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"))

    # 5. status
    status = contra_mod.reconcile_status(
        contradiction_result=contra,
        evidence_sufficient=evidence.get("sufficient", False),
    )
    if status == "triangulated" and novelty_receipt.decision == "known":
        status = "candidate"  # کشف تکراری actionable نیست

    return {
        "schema": "world-discovery.triangulate.v1",
        "triangulated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "novelty": novelty_receipt.as_dict(),
        "contradiction": contra.as_dict(),
        "evidence_receipt": evidence,
        "freshness": fresh.as_dict(),
        "status": status,
    }


# ──────────────────────────────────────────────────────
# discover — یک discovery receipt یا no-valid-discovery
# ──────────────────────────────────────────────────────
def discover(direction: dict, *, now: Optional[datetime] = None,
             retriever: Optional[public_web.Retriever] = None,
             max_candidates: int = 10) -> dict:
    """اجرای کل حلقهٔ کشف. برمی‌گرداند:
    {schema, status, discovery|null, metrics, candidates, competitor_matrix, ...}

    status در {DISCOVERY_VALIDATED, NO_VALID_DISCOVERY, CONTESTED, BLOCKED_BY_OWNER,
               IMPLEMENTED_NOT_INTEGRATED}
    """
    now = now or datetime.now(timezone.utc)
    direction = direction if isinstance(direction, dict) else direction.as_dict()
    min_sources = direction.get("min_sources", 2)

    # 1. observe
    obs_result = observe(direction, now=now, retriever=retriever)
    observations = obs_result["observations"]

    metrics = Metrics(
        candidates_found=len(observations),
    )

    if not observations:
        metrics.candidates_found = 0
        return _no_valid_discovery(
            direction, metrics, reason="no-observations",
            observe_summary=obs_result, now=now,
        )

    # 2. mine candidates
    obs_objs = [_dict_to_observation(o) for o in observations]
    cands = candidate_miner.mine_candidates(obs_objs)
    metrics.candidates_deduplicated = max(0, len(observations) - len(cands))

    if not cands:
        return _no_valid_discovery(
            direction, metrics, reason="no-candidates-after-mining",
            observe_summary=obs_result, now=now,
        )

    # 3. triangulate top candidates
    tri_results = []
    for cand in cands[:max_candidates]:
        tri = triangulate(
            cand.as_dict_with_sources(),
            now=now, retriever=retriever, min_sources=min_sources,
        )
        tri_results.append((cand, tri))
        metrics.contradiction_search_rate += 1
        if tri["status"] == "triangulated":
            metrics.triangulated_discovery_count += 1
        elif tri["status"] == "contested":
            metrics.contested_discovery_count += 1

    metrics.contradiction_search_rate = (
        round(metrics.contradiction_search_rate / max(len(cands), 1), 3)
    )

    # 4. انتخاب discovery برتر: اول triangulated، بعد partially-novel، بعد contested
    best = _pick_best(tri_results)
    if best is None:
        return _no_valid_discovery(
            direction, metrics, reason="no-triangulated-candidate",
            observe_summary=obs_result, candidates=[c.as_dict() for c, _ in tri_results],
            now=now,
        )

    cand, tri = best

    # 5. ساخت Discovery object
    disc = _build_discovery(direction, cand, tri, now)

    # 6. competitor matrix + asymmetry
    comp_rows = _build_competitor_rows(cand, direction)
    comp_matrix = competitor_intel.competitor_matrix_summary(comp_rows)
    asymmetries = competitor_intel.propose_asymmetry(comp_rows)
    metrics.competitor_coverage = comp_matrix["coverage"]
    metrics.asymmetry_hypotheses = len(asymmetries)
    metrics.novel_candidate_rate = round(
        sum(1 for _, t in tri_results
            if t["novelty"]["decision"] in ("novel", "partially-novel"))
        / max(len(tri_results), 1), 3
    )

    # 7. opportunity + scoring
    opp_seed = opp_mod.OpportunitySeed(
        claim=disc.claim,
        opp_type=opp_mod.classify_opportunity_type(disc.claim, asymmetries[0] if asymmetries else None),
        discovery_id=disc.discovery_id,
        asymmetry=asymmetries[0] if asymmetries else None,
        time_to_test_days=direction.get("horizon_days", 7),
        reversibility="high",
    )
    opp = opp_mod.build_opportunity(opp_seed)
    opp, breakdown = scorer.score_opportunity(
        opp,
        sources=disc.evidence,
        novelty_decision=disc.novelty.get("decision", "unknown"),
        direction_keywords=direction.get("competition_dims", []),
        horizon_days=direction.get("horizon_days", 7),
        action_level=direction.get("action_level", "L3"),
        freshness_dict=disc.freshness,
        injection_flags=sum(1 for o in cand.observations if o.injection_risk),
        asymmetry_confidence=(asymmetries[0].confidence if asymmetries else 0.0),
        contested=(disc.status == "contested"),
    )
    disc.opportunity = opp.as_dict()
    disc.competitors = [r.as_dict() for r in comp_rows]

    # 8. experiment design
    exp = experiment_designer.design_experiment(
        disc.as_dict(), opp,
        action_level=direction.get("action_level", "L3"),
        horizon_days=direction.get("horizon_days", 7),
        now=now,
    )
    metrics.experiments_designed = 1
    metrics.experiments_with_falsifier = 1 if exp.falsifier else 0
    disc.next_experiment = exp.as_dict()["hypothesis"]

    # 9. final status
    disc.owner_gate = (
        "L3: نتیجه به‌صورت report تحویل می‌شود؛ ارسال تلگرام فقط با رأی تازه."
    )
    missing = disc.validate_required()
    if not missing and disc.is_valid():
        # همهٔ فیلدهای اجباری حضور دارند → معتبر
        disc.status = STATUS_TRIANGULATED
        final_status = "DISCOVERY_VALIDATED"
    else:
        # فاقد موارد اجباری است → NO_VALID (صادقانه)
        final_status = "NO_VALID_DISCOVERY"
        disc.status = STATUS_CANDIDATE

    # 10. owner action card (تلگرام — BLOCKED_BY_OWNER)
    brief = action_boundary.compose_telegram_brief(
        discovery=disc.as_dict(),
        opportunity=opp.as_dict(),
        experiment=exp.as_dict(),
        metrics=metrics.as_dict(),
    )
    card = action_boundary.make_owner_action_card(
        discovery_id=disc.discovery_id,
        exact_action="send-telegram: discovery brief to owner",
        why_needed="مالک برای تصمیم نیاز به کشف دارد.",
        risk="low",
        channel="telegram",
        draft_message=brief,
        ttl_hours=48,
        now=now,
    )
    metrics.blocked_by_owner_count = 1

    # 11. check hard invariants
    violations = metrics.check_hard_invariants()
    if violations:
        final_status = "BLOCKED_BY_OWNER"

    return {
        "schema": "world-discovery.discover.v1",
        "discovered_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": final_status,
        "discovery": disc.as_dict(),
        "experiment": exp.as_dict(),
        "opportunity": opp.as_dict(),
        "competitor_matrix": comp_matrix,
        "asymmetry_hypotheses": [h.as_dict() for h in asymmetries],
        "owner_action_cards": [card.as_dict()],
        "metrics": metrics.as_dict(),
        "candidates": [c.as_dict() for c, _ in tri_results[:10]],
        "observe_summary": {
            "queries": obs_result["queries"],
            "observation_count": obs_result["observation_count"],
        },
        "telegram_draft_brief": brief,
        "hard_invariant_violations": violations,
    }


def _no_valid_discovery(direction, metrics, *, reason, now,
                        observe_summary=None, candidates=None) -> dict:
    """ساخت receipt صادقانهٔ NO_VALID_DISCOVERY."""
    return {
        "schema": "world-discovery.discover.v1",
        "discovered_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "NO_VALID_DISCOVERY",
        "discovery": None,
        "reason": reason,
        "metrics": metrics.as_dict(),
        "candidates": candidates or [],
        "observe_summary": observe_summary or {},
        "competitor_matrix": {},
        "asymmetry_hypotheses": [],
        "owner_action_cards": [],
        "telegram_draft_brief": "",
        "hard_invariant_violations": [],
        "note": (
            "هیچ کشف معتبری پیدا نشد. این نتیجه معتبر است. "
            "ساختن کشف برای سبزشدن آزمون ممنوع است."
        ),
    }


# ──────────────────────────────────────────────────────
# design_experiment — public wrapper
# ──────────────────────────────────────────────────────
def design_experiment(discovery: dict, *, now: Optional[datetime] = None,
                      action_level: str = "L3", horizon_days: int = 7) -> dict:
    now = now or datetime.now(timezone.utc)
    opp = Opportunity(claim=discovery.get("claim", ""),
                      type=discovery.get("opportunity", {}).get("type", "ai-architecture-insight"),
                      discovery_id=discovery.get("discovery_id", ""))
    exp = experiment_designer.design_experiment(
        discovery, opp, action_level=action_level,
        horizon_days=horizon_days, now=now,
    )
    return exp.as_dict()


# ──────────────────────────────────────────────────────
# export_bundle — public wrapper
# ──────────────────────────────────────────────────────
def export_bundle(result: dict, output_dir, *, now: Optional[datetime] = None) -> dict:
    return report.export_bundle(result, Path(output_dir), now=now)


def write_report(result: dict, output_dir, *, now: Optional[datetime] = None) -> dict:
    """نوشتن گزارش انسان‌خوان از result. برمی‌گرداند {report_path, bundle_path}."""
    now = now or datetime.now(timezone.utc)
    output_dir = Path(output_dir)
    bundle_info = export_bundle(result, output_dir / "artifacts", now=now)

    direction = _extract_direction_from_result(result)
    report_path = report.write_human_report(
        direction=direction,
        metrics=result.get("metrics", {}),
        candidates=result.get("candidates", []),
        top_discovery=result.get("discovery"),
        competitor_matrix=result.get("competitor_matrix", {}),
        asymmetry_hypotheses=result.get("asymmetry_hypotheses", []),
        experiment=result.get("experiment"),
        owner_action_cards=result.get("owner_action_cards", []),
        final_status=result.get("status", "UNKNOWN"),
        output_dir=output_dir / "reports",
        now=now,
    )
    return {"report_path": report_path, "bundle_path": bundle_info["path"],
            "bundle_sha256": bundle_info["sha256"]}


def _extract_direction_from_result(result: dict) -> dict:
    disc = result.get("discovery") or {}
    return {
        "domain": disc.get("domain", "ai-competition"),
        "geography": disc.get("geography", "global"),
        "horizon_days": disc.get("horizon_days", 7),
        "competitors": [r.get("company") for r in result.get("competitor_matrix", {}).get("rows", [])],
        "action_level": "L3",
        "min_sources": 2,
    }


# ──────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────
def _dict_to_observation(d: dict):
    from .contracts import Observation, Source
    src_d = d.get("source", {})
    src = Source(
        url=src_d.get("url", ""),
        title=src_d.get("title", ""),
        tier=src_d.get("tier", "D"),
        source_date=src_d.get("source_date"),
        retrieved_at=src_d.get("retrieved_at", ""),
        snippet=src_d.get("snippet", ""),
        publisher=src_d.get("publisher", ""),
        is_primary=src_d.get("is_primary", False),
        notes=src_d.get("notes", ""),
    )
    return Observation(
        observation_id=d.get("observation_id", ""),
        claim=d.get("claim", ""),
        source=src,
        competitor=d.get("competitor", ""),
        raw_kind=d.get("raw_kind", ""),
        retrieved_at=d.get("retrieved_at", ""),
        injection_risk=d.get("injection_risk", False),
    )


def _pick_best(tri_results):
    """انتخاب discovery برتر: اول triangulated + novel/partially-novel."""
    # اول triangulated
    triangulated = [(c, t) for c, t in tri_results if t["status"] == "triangulated"]
    if triangulated:
        # ترجیح novelty بالاتر
        triangulated.sort(
            key=lambda ct: (ct[1]["novelty"]["decision"] != "novel",
                            ct[1]["novelty"]["overlap_score"]),
        )
        return triangulated[0]
    # اگر contested بود ولی novelty خوب، آن را برای حل تناقض برمی‌داریم
    contested = [(c, t) for c, t in tri_results if t["status"] == "contested"]
    if contested:
        return contested[0]
    return None


def _build_discovery(direction, cand, tri, now) -> Discovery:
    sources = [o.source.as_dict() for o in cand.observations]
    claim = cand.claim
    disc = Discovery(
        discovery_id=make_discovery_id(claim, direction.get("mission_id", "wd")),
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        mission_id=direction.get("mission_id", ""),
        domain=direction.get("domain", ""),
        geography=direction.get("geography", ""),
        claim=claim,
        why_it_matters=_derive_why(cand, direction),
        direction_link=f"mission={direction.get('mission_id')} domain={direction.get('domain')}",
        novelty=tri["novelty"],
        evidence=sources,
        contradictions=tri["contradiction"]["contradictions"],
        unknowns=[],
        freshness=tri["freshness"],
        competitors=[],
        opportunity={},
        falsifier=_derive_falsifier(claim),
        next_experiment="",
        owner_gate="",
        status=tri["status"],
    )
    return disc


def _derive_why(cand, direction) -> str:
    comps = ", ".join(cand.competitors[:3]) if cand.competitors else "رقبا"
    return (
        f"این ادعا دربارهٔ {comps} در حوزهٔ {direction.get('domain')} است "
        f"و ممکن است شکاف قابلیت یا فرصت رقابتی را نشان دهد. "
        f"کاندیدا با {cand.independent_sources} منبع مستقل پشتیبانی می‌شود."
    )


def _derive_falsifier(claim) -> str:
    return (
        f"اگر دادهٔ عمومی نشان دهد که «{claim[:120]}» برعکس است "
        f"(یا رقیب آن را پر کرده، یا ادعا از سوی منبع رسمی رد شده)، کشف باطل می‌شود."
    )


def _build_competitor_rows(cand, direction):
    """ساخت ردیف‌های رقابت از observations کاندیدا."""
    rows = []
    seen = set()
    for o in cand.observations:
        comp = o.competitor
        if not comp or comp in seen:
            continue
        seen.add(comp)
        strengths, weaknesses = _infer_strength_weakness(o)
        rows.append(competitor_intel.build_competitor_row(
            comp,
            strengths=strengths,
            weaknesses=weaknesses,
            evidence=[o.source],
        ))
    return rows


def _infer_strength_weakness(obs):
    """حدس سادهٔ نقاط قوت/ضعف از observation."""
    text = (obs.claim + " " + obs.source.snippet).lower()
    strengths = []
    weaknesses = []
    if any(k in text for k in ("launch", "release", "new", "agent", "capabilit")):
        strengths.append("product velocity / new releases")
    if any(k in text for k in ("context", "long", "memory")):
        strengths.append("long context / memory")
    if any(k in text for k in ("search", "grounded", "citation")):
        strengths.append("search grounding")
    if any(k in text for k in ("safe", "alignment", "constitutional")):
        strengths.append("safety/alignment focus")
    if any(k in text for k in ("limit", "weak", "fail", "lack", "cannot")):
        weaknesses.append("documented limitation")
    if any(k in text for k in ("expensive", "cost", "price")):
        weaknesses.append("pricing pressure")
    if any(k in text for k in ("slow", "rigid", "enterprise")):
        weaknesses.append("operational rigidity")
    if not strengths:
        strengths.append("brand/recognition (unverified)")
    if not weaknesses:
        weaknesses.append("unknown — needs targeted research")
    return strengths[:3], weaknesses[:3]
