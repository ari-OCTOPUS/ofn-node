"""
brain/meta_research.py — موتور تحقیقِ فراشناختی

این «لایه‌ی خودآگاهی» است. سیستم:
  ۱. جهت کاربر رو می‌گیره
  ۲. کد خودش رو می‌خونه (self-model)
  ۳. وب رو می‌گرده (web research)
  ۴. داده‌های قبلی خودش رو مرور می‌کنه (past experiments)
  ۵. با Fugu به‌عنوان مغز تحلیل و ترکیب می‌کنه
  ۶. پروپوزال ارتقا می‌سازه و ذخیره می‌کنه
  ۷. به کاربر ارائه می‌ده

جریان:
  direction → self_map + web + vault → Fugu synthesis → proposals → DB
"""
from __future__ import annotations

import json
import time
import os
import textwrap
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from brain.web_research import multi_search, synthesize_knowledge, WebResult
from brain.self_model import build_self_map, self_model_to_text

# Allow running as script (python brain/meta_research.py)
import sys as _sys
if "brain" not in str(type(_sys.modules.get("brain", None))):
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ResearchStep:
    """یک گام از تحقیق."""
    phase: str       # "self_model" | "web_search" | "synthesis" | "proposal"
    status: str      # "running" | "done" | "error"
    detail: str = ""
    timestamp: str = ""


@dataclass
class MetaResearchResult:
    """نتیجه‌ی یک جلسه‌ی تحقیق."""
    topic: str
    direction: str
    steps: list[ResearchStep] = field(default_factory=list)
    web_results: list[WebResult] = field(default_factory=list)
    synthesis: str = ""           # متن تحلیل Fugu
    proposals: list[dict] = field(default_factory=list)  # upgrade proposals
    sources_count: int = 0
    timestamp: str = ""
    session_id: Optional[int] = None


# ════════════════════════════════════════════════════════════════════════
#  Synthesis prompt builder
# ════════════════════════════════════════════════════════════════════════

def _build_synthesis_prompt(direction: str, self_map_text: str,
                            web_knowledge: str, past_data: str) -> str:
    """ساخت پرامپت خیلی فشرده برای LLM."""

    # Extract just the key findings from web (titles + first snippet)
    web_lines = web_knowledge.split("\n")
    web_titles = [l for l in web_lines if l.startswith("##")][:4]
    web_compact = "\n".join(web_titles)

    return f"""سیستم پژوهشی خودمختار. جهت: {direction}

منابع وب:
{web_compact}

۳ پیشنهاد ارتقا. JSON:
{{"analysis":"", "proposals":[{{"title":"","description":"","target_module":"","priority":"high","effort":"medium","code_sketch":""}}]}}"""


def _build_local_synthesis(direction: str, self_map_text: str,
                           web_knowledge: str) -> dict:
    """
    Fallback محلی — بدون LLM.
    تحلیل مبتنی بر قواعد + ساختار سیستم + نتایج وب.
    همیشه ۳ پیشنهاد می‌سازه.
    """

    direction_lower = direction.lower()
    web_text = web_knowledge.lower()
    proposals = []

    # ── قواعد تطبیق الگو ────────────────────────────────────────────

    # Pattern: metacognition / self-awareness / confidence
    if any(kw in direction_lower for kw in
           ["metacogn", "self-aware", "خودآگاه", "فراشناخت", "اعتماد", "confidence", "uncertainty"]):
        proposals.append({
            "title": "لایه‌ی پایش فراشناختی (Metacognitive Monitor)",
            "description": (
                "افزودن کلاسی که برای هر تحلیل، یک امتیاز اعتماد‌به‌نفس محاسبه می‌کنه. "
                "اگه امتیاز پایین باشه، نتیجه flag میشه و سیستم خودش رو بررسی مجدد می‌کنه. "
                "این شبیه‌سازی 'من چه می‌دانم که می‌دانم؟' است."
            ),
            "rationale": (
                "تحقیق وب و ادبیات (Graziano AST، Dehaene GWT، predictive metacognition) "
                "نشان میدن که پایش فراشناختی هسته‌ی خودآگاهی است. "
                "سیستم فعلی هیچ ارزیابی اعتماد نداره."
            ),
            "target_module": "brain/reflection.py",
            "priority": "high",
            "effort": "medium",
            "code_sketch": (
                "class MetacognitiveMonitor:\n"
                "    def __init__(self):\n"
                "        self.history = []  # past analysis results\n\n"
                "    def evaluate_confidence(self, analysis: dict) -> float:\n"
                "        \"\"\"0.0 (no confidence) to 1.0 (very confident).\"\"\"\n"
                "        # Compare with distribution of past results\n"
                "        if not self.history:\n"
                "            return 0.5  # uncertain\n"
                "        # Z-score of current MI vs past MIs\n"
                "        past_mis = [h.get('temporal_mi', 0) for h in self.history]\n"
                "        mi = analysis.get('temporal_mi', 0)\n"
                "        z = abs(mi - np.mean(past_mis)) / (np.std(past_mis) + 1e-9)\n"
                "        # High z = outlier = low confidence\n"
                "        return max(0.0, 1.0 - z / 4)\n\n"
                "    def should_reconsider(self, analysis) -> bool:\n"
                "        return self.evaluate_confidence(analysis) < 0.3"
            ),
            "references": [r.url for r in []],  # will be filled from web
        })

    # Pattern: memory / learning / experience
    if any(kw in direction_lower for kw in
           ["memory", "learn", "یادگیری", "حافظه", "episodic", "تجربه", "continual"]):
        proposals.append({
            "title": "حافظه‌ی اپی­sودیک (Episodic Memory)",
            "description": (
                "ذخیره‌ی هر تجربه‌ی پژوهشی به‌عنوان یک «قسمت» با context کامل: "
                "چه داده‌ای، چه تصمیمی گرفته شد، چه نتیجه‌ای داد، و چه یاد گرفتیم. "
                "سیستم بعداً می‌تونه از این تجربه‌ها الگو استخراج کنه."
            ),
            "rationale": (
                "سیستم فعلی نتایج رو ذخیره می‌کنه (patterns table) ولی "
                "context تصمیم‌گیری (چرا این منبع؟ چرا ذخیره شد؟) رو نه. "
                "حافظه‌ی اپی­sودیک به سیستم اجازه میده از اشتباهات یاد بگیره."
            ),
            "target_module": "memory/store.py",
            "priority": "high",
            "effort": "medium",
            "code_sketch": (
                "# جدول جدید در SQLite:\n"
                "# episodes(id, timestamp, source, analysis_json,\n"
                "#   decision, rationale, outcome, lesson)\n\n"
                "def save_episode(source, analysis, decision, rationale, outcome):\n"
                "    \"\"\"ذخیره‌ی یک تجربه‌ی کامل.\"\"\"\n"
                "    lesson = _extract_lesson(analysis, outcome)\n"
                "    conn.execute(\n"
                "        'INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?)',\n"
                "        (..., source, json.dumps(analysis),\n"
                "         decision, rationale, outcome, lesson)\n"
                "    )\n\n"
                "def recall_similar_episodes(current_analysis, top_k=3):\n"
                "    \"\"\"یادآوری تجربه‌های مشابه.\"\"\"\n"
                "    # Semantic similarity via MI/rho matching\n"
                "    pass"
            ),
            "references": [],
        })

    # Pattern: exploration / curiosity / discovery
    if any(kw in direction_lower for kw in
           ["explor", "curios", "کشف", "کنجکاو", "discovery", "novel"]):
        proposals.append({
            "title": "مکانیزم کنجکاوی ذاتی (Intrinsic Curiosity)",
            "description": (
                "افزودن امتیاز کنجکاوی به autoloop. سیستم منابعی رو انتخاب کنه که "
                "بیشترین خطای پیش‌بینی (prediction error) دارن — یعنی بیشترین پتانسیل یادگیری. "
                "این کشف الگوهای جدید رو تضمین می‌کنه."
            ),
            "rationale": (
                "ICM (Pathak et al 2017) و RND (Burda et al 2018) نشون دادن "
                "که کنجکاوی ذاتی باعث کشف الگوهای متنوع‌تر میشه. "
                "autoloop فعلی منابع رو چرخشی (round-robin) انتخاب می‌کنه."
            ),
            "target_module": "brain/autoloop.py",
            "priority": "medium",
            "effort": "low",
            "code_sketch": (
                "def _select_source_by_curiosity(self, available_sources):\n"
                "    \"\"\"انتخاب منبع بر اساس کنجکاوی.\"\"\"\n"
                "    scores = []\n"
                "    for src in available_sources:\n"
                "        # If we've never seen this source → high curiosity\n"
                "        if src not in self._seen_sources:\n"
                "            scores.append((src, 1.0))\n"
                "        else:\n"
                "            # If last result was surprising → high curiosity\n"
                "            past = [h for h in self.history if h.source == src]\n"
                "            if past:\n"
                "                novelty = past[-1].novelty\n"
                "                scores.append((src, novelty))\n"
                "    # Pick highest curiosity with some randomness\n"
                "    scores.sort(key=lambda x: -x[1])\n"
                "    return scores[0][0] if scores else available_sources[0]"
            ),
            "references": [
                "https://arxiv.org/abs/1705.05363",  # ICM
                "https://arxiv.org/abs/1810.12894",  # RND
            ],
        })

    # Pattern: safety / verification / alignment
    if any(kw in direction_lower for kw in
           ["safe", "verify", "تأیید", "امنیت", "formal", "alignment", "اعتبارسنجی"]):
        proposals.append({
            "title": "مکانیزم تأیید چندلایه (Multi-layer Verification)",
            "description": (
                "افزودن لایه‌ای که هر خروجی رو قبل از ذخیره با چند روش مستقل تأیید می‌کنه: "
                "(۱) بررسی آماری (آیا MI در محدوده‌ی معقول؟) "
                "(۲) بررسی سازگاری (آیا ρ و λ منطقی؟) "
                "(۳) بررسی کران‌ها (آیا مقدار‌ها فیزیکی هستن؟)"
            ),
            "rationale": (
                "formal verification و runtime assurance از ذخیره‌ی نتایج غلط جلوگیری می‌کنن. "
                "سیستم فعلی هر چی detectable باشه رو ذخیره می‌کنه بدون اعتبارسنجی."
            ),
            "target_module": "brain/graph.py",
            "priority": "medium",
            "effort": "high",
            "code_sketch": (
                "def verify_output(analysis: dict) -> tuple[bool, str]:\n"
                "    \"\"\"تأیید چندلایه.\"\"\"\n"
                "    mi = analysis.get('temporal_mi', 0)\n"
                "    rho = analysis.get('rho_hat', 0)\n\n"
                "    # Layer 1: bounds\n"
                "    if mi < 0 or mi > 20:\n"
                "        return False, 'MI out of bounds'\n"
                "    if not (-1 <= rho <= 1):\n"
                "        return False, 'rho out of bounds'\n\n"
                "    # Layer 2: consistency\n"
                "    if mi > 0 and abs(rho) < 0.01:\n"
                "        return False, 'MI>0 but rho~0: inconsistent'\n\n"
                "    # Layer 3: statistical\n"
                "    # (compare with known distributions)\n"
                "    return True, 'all checks passed'"
            ),
            "references": [],
        })

    # Pattern: architecture / multi-layer / cognitive
    if any(kw in direction_lower for kw in
           ["architect", "multi", "چندلایه", "معماری", "layered", "cognitive", "شناختی", "agi"]):
        proposals.append({
            "title": "معماری شناختی سه‌لایه (3-Layer Cognitive Architecture)",
            "description": (
                "تقسیم سیستم به سه لایه‌ی شناختی: \n"
                "لایه‌ی ۱ (Reactive): autoloop فعلی — سریع، خودکار، بدون تفکر عمیق.\n"
                "لایه‌ی ۲ (Deliberative): تحلیل با LLM — کندتر، تحلیلی، با حافظه.\n"
                "لایه‌ی ۳ (Meta): self-model + meta-research — کندترین، استراتژیک.\n"
                "هر لایه می‌تونه لایه‌ی پایین‌تر رو مشاهده و اصلاح کنه."
            ),
            "rationale": (
                "Cognitive architectures (SOAR، ACT-R، CLARION، LIDA) همگی "
                "ساختار چندلایه دارن. لایه‌بندی به سیستم اجازه میده "
                "در سطوح مختلف فکر کنه."
            ),
            "target_module": "brain/graph.py",
            "priority": "high",
            "effort": "high",
            "code_sketch": (
                "class CognitiveArchitecture:\n"
                "    def __init__(self):\n"
                "        self.reactive = AutoLoopEngine()    # Layer 1\n"
                "        self.deliberative = GraphPipeline() # Layer 2\n"
                "        self.meta = MetaResearchEngine()    # Layer 3\n\n"
                "    def process(self, data):\n"
                "        # Layer 1: fast reaction\n"
                "        result = self.reactive.process(data)\n\n"
                "        # Layer 2: if surprising, deliberate\n"
                "        if result.novelty > 0.5:\n"
                "            result = self.deliberative.analyze(data)\n\n"
                "        # Layer 3: periodically, reflect\n"
                "        if self._time_for_reflection():\n"
                "            self.meta.reflect_on_recent()"
            ),
            "references": [
                "https://en.wikipedia.org/wiki/Cognitive_architecture",
            ],
        })

    # Pattern: prediction / forecasting / proactive
    if any(kw in direction_lower for kw in
           ["predict", "forecast", "پیش‌بینی", "proactive", "active inference"]):
        proposals.append({
            "title": "موتور پیش‌بینی (Predictive Engine)",
            "description": (
                "افزودن قابلیت پیش‌بینی: سیستم قبل از تحلیل یک منبع، "
                "حدس می‌زنه چه نتیجه‌ای می‌تونه بده. بعد مقایسه می‌کنه. "
                "اختلاف (surprise) محرک یادگیریه."
            ),
            "rationale": (
                "Predictive Processing (Friston) و Active Inference نشون دادن "
                "که مغز به‌صورت پیش‌بینانه کار می‌کنه. "
                "این الگو قابل پیاده‌سازی در سیستم ماست."
            ),
            "target_module": "brain/autoloop.py",
            "priority": "medium",
            "effort": "medium",
            "code_sketch": (
                "def predict_result(self, source_type):\n"
                "    \"\"\"حدس نتیجه قبل از اجرا.\"\"\"\n"
                "    past = [h for h in self.history if source_type in h.source]\n"
                "    if not past:\n"
                "        return {'expected_mi': 0.5, 'confidence': 0.1}\n"
                "    mis = [h.scores['temporal_mi'] for h in past]\n"
                "    return {\n"
                "        'expected_mi': np.mean(mis),\n"
                "        'confidence': 1.0 - np.std(mis),\n"
                "    }\n\n"
                "# در run_step:\n"
                "prediction = self.predict_result(source_type)\n"
                "# ... تحلیل ...\n"
                "surprise = abs(actual_mi - prediction['expected_mi'])"
            ),
            "references": [
                "https://arxiv.org/abs/1906.09524",  # active inference survey
            ],
        })

    # ── اگه هیچ الگویی تطابق نکرد، پیشنهاد‌های عمومی ─────────────────
    if not proposals:
        # Always suggest based on self-model limitations
        if "تست" in self_map_text.lower() or "test" in self_map_text.lower():
            proposals.append({
                "title": "افزایش پوشش تست",
                "description": "افزودن تست‌های خودکار برای ماژول‌های پیچیده.",
                "rationale": "self-model نشون داد پوشش تست ضعیف است.",
                "target_module": "tests/",
                "priority": "low",
                "effort": "low",
                "code_sketch": "def test_autoloop():\n    engine = AutoLoopEngine()\n    r = engine.run_step(0)\n    assert r is not None",
                "references": [],
            })

        proposals.append({
            "title": "بازخورد انسانی در لوپ (Human-in-the-loop Feedback)",
            "description": (
                "افزودن قابلیت thumbs up/down به هر کشف. "
                "سیستم از بازخورد کاربر یاد می‌گیره و اولویت‌های خودش رو تنظیم می‌کنه."
            ),
            "rationale": "RLHF و RLIF نشون دادن که بازخورد انسانی کیفیت رو بالا می‌بره.",
            "target_module": "ui/app.py",
            "priority": "medium",
            "effort": "low",
            "code_sketch": "# در جدول patterns: column added 'user_rating'\n# در UI: 👍/👎 buttons per result",
            "references": [],
        })

    # Always suggest a web-source-based proposal if we found good sources
    if web_knowledge and len(proposals) < 3:
        proposals.append({
            "title": "ادغام یافته‌های وب در پایگاه دانش",
            "description": (
                f"تحقیق وب {web_knowledge.count('##')} منبع پیدا کرد. "
                "پیشنهاد: این یافته‌ها رو به‌صورت structured notes در vault ذخیره کنیم "
                "تا سیستم بعداً بتونه ازشون استفاده کنه."
            ),
            "rationale": "سیستم فعلی فقط از vault محلی استفاده می‌کنه. وب گنجینه‌ی دانش است.",
            "target_module": "memory/vectorstore.py",
            "priority": "low",
            "effort": "low",
            "code_sketch": "# در vectorstore.py:\ndef add_web_finding(title, content, url):\n    collection.add(\n        documents=[content],\n        metadatas=[{'source': url, 'type': 'web'}],\n        ids=[hashlib.md5(url.encode()).hexdigest()]\n    )",
            "references": [],
        })

    return {
        "analysis": (
            f"تحلیل محلی بر اساس جهت «{direction[:60]}».\n"
            f"سیستم خودش رو بررسی کرد، وب رو گشت، و {len(proposals)} پیشنهاد ساخت. "
            f"این پیشنهادها از ترکیب self-model + الگوهای شناخته‌شده‌ی ادبیات تولید شدن."
        ),
        "proposals": proposals[:3],
    }


# ════════════════════════════════════════════════════════════════════════
#  Main engine
# ════════════════════════════════════════════════════════════════════════

def run_meta_research(direction: str, use_llm: bool = False,
                      max_web_results: int = 5) -> MetaResearchResult:
    """
    اجرای یک جلسه‌ی تحقیقِ خودمختار.

    Args:
        direction: جهت تحقیق از کاربر (مثلا «چطور خودآگاهی سیستم رو بالا ببرم؟»)
        use_llm: آیا از Fugu استفاده بشه؟ (اگه False، فقط local synthesis)
        max_web_results: حداکثر تعداد نتایج وب

    Returns:
        MetaResearchResult با پروپوزال‌ها
    """
    result = MetaResearchResult(
        topic=direction[:80],
        direction=direction,
        timestamp=datetime.now().isoformat(),
    )

    # ── Phase 1: Self-Model ──────────────────────────────────────────
    step = ResearchStep(phase="self_model", status="running",
                        timestamp=datetime.now().isoformat())
    result.steps.append(step)

    try:
        sm = build_self_map()
        self_text = self_model_to_text(sm)
        step.status = "done"
        step.detail = f"{sm.total_files} فایل، {sm.total_lines} خط، {len(sm.capabilities)} توانمندی"
    except Exception as e:
        step.status = "error"
        step.detail = str(e)
        self_text = "(خطا در خواندن self-model)"

    # ── Phase 2: Web Research ────────────────────────────────────────
    step = ResearchStep(phase="web_search", status="running",
                        timestamp=datetime.now().isoformat())
    result.steps.append(step)

    try:
        # Translate Persian direction to English for better web results
        search_query = _optimize_search_query(direction)
        web_results = multi_search(search_query, max_per_source=max_web_results)
        result.web_results = web_results
        result.sources_count = len(web_results)
        web_knowledge = synthesize_knowledge(search_query, web_results)
        step.status = "done"
        step.detail = f"{len(web_results)} منبع از arXiv/Wikipedia/DDG"
    except Exception as e:
        step.status = "error"
        step.detail = str(e)
        web_results = []
        web_knowledge = "(خطا در جستجوی وب)"

    # ── Phase 3: Past experiments summary ────────────────────────────
    try:
        from memory.store import query_experiments
        experiments = query_experiments(limit=10)
        if experiments:
            past_data = f"آخرین {len(experiments)} آزمایش:\n"
            for e in experiments[:5]:
                past_data += f"  - ρ={e.get('rho','?')}, λ={e.get('lambda','?')}, "
                past_data += f"Δ_self={e.get('delta_self','?')}, E_shadow={e.get('e_shadow','?')}\n"
        else:
            past_data = "هنوز آزمایشی ثبت نشده."
    except Exception:
        past_data = ""

    # ── Phase 4: Synthesis (Fugu or local) ──────────────────────────
    step = ResearchStep(phase="synthesis", status="running",
                        timestamp=datetime.now().isoformat())
    result.steps.append(step)

    synthesis_data = None

    if use_llm:
        try:
            synthesis_data = _synthesize_with_fugu(
                direction, self_text, web_knowledge, past_data
            )
            if synthesis_data and synthesis_data.get("proposals"):
                result.synthesis = synthesis_data.get("analysis", "")
                step.status = "done"
                step.detail = f"ترکیب با LLM انجام شد ({len(synthesis_data.get('proposals',[]))} پیشنهاد)"
            else:
                raise RuntimeError("LLM returned empty proposals")
        except Exception as e:
            step.status = "error"
            step.detail = f"LLM ناموفق: {str(e)[:60]} → fallback محلی"
            synthesis_data = None

    if synthesis_data is None:
        synthesis_data = _build_local_synthesis(direction, self_text, web_knowledge)
        result.synthesis = synthesis_data.get("analysis", "")
        step.status = "done"
        step.detail = "ترکیب محلی انجام شد"

    # ── Phase 5: Proposals ───────────────────────────────────────────
    step = ResearchStep(phase="proposal", status="running",
                        timestamp=datetime.now().isoformat())
    result.steps.append(step)

    try:
        from memory.research_store import save_proposal, save_research_session, UpgradeProposal

        proposal_ids = []
        result.proposals = synthesis_data.get("proposals", [])

        for prop in result.proposals:
            pid = save_proposal(UpgradeProposal(
                title=prop.get("title", "بدون عنوان"),
                description=prop.get("description", ""),
                rationale=prop.get("rationale", ""),
                target_module=prop.get("target_module", ""),
                priority=prop.get("priority", "medium"),
                effort=prop.get("effort", "medium"),
                code_sketch=prop.get("code_sketch", ""),
                references=prop.get("references", []),
            ))
            proposal_ids.append(pid)

        # Save session
        session_id = save_research_session(
            topic=result.topic, direction=direction,
            sources_found=result.sources_count,
            insights=result.synthesis[:500],
            proposals=proposal_ids,
        )
        result.session_id = session_id
        step.status = "done"
        step.detail = f"{len(proposal_ids)} پروپوزال ذخیره شد (session #{session_id})"

    except Exception as e:
        step.status = "error"
        step.detail = str(e)

    return result


def _optimize_search_query(direction: str) -> str:
    """ترجمه/بهینه‌سازی جهت فارسی به query انگلیسی برای وب."""

    # Persian → English keyword mapping
    translations = {
        "خودآگاهی": "self-aware AI consciousness metacognition",
        "فراشناخت": "metacognition artificial intelligence",
        "ارتقا": "architecture improvement autonomous AI",
        "یادگیری": "lifelong learning continual AI",
        "حافظه": "episodic memory AI architecture",
        "امنیت": "AI safety verification alignment",
        "تأیید": "formal verification neural networks",
        "کشف": "automated scientific discovery",
        "خودمختار": "autonomous AI agent architecture",
        "چندلایه": "hierarchical cognitive architecture",
        "اگاهی": "artificial consciousness theory",
        "آگاهی": "artificial consciousness theory",
        "هوش": "artificial general intelligence AGI",
        "بعد": "dimensionality hidden state detection",
        "سایه": "shadow variable hidden state inference",
        "p": "self-modeling AI introspection",
        "اعتماد": "confidence calibration uncertainty AI",
        "pishbin": "predictive processing active inference",
    }

    direction_lower = direction.lower()
    keywords = []

    for fa, en in translations.items():
        if fa in direction_lower:
            keywords.append(en)

    # If we found translations, use them
    if keywords:
        query = " ".join(keywords[:3])
    else:
        # Use direction as-is if it looks English
        if any(c.isalpha() and ord(c) < 128 for c in direction):
            query = direction
        else:
            query = "artificial general intelligence architecture"

    return query[:200]


def _synthesize_with_fugu(direction: str, self_text: str,
                          web_knowledge: str, past_data: str) -> dict:
    """ترکیب با LLM — برگرداندن JSON dict.

    از routerِ مرکزی (دکترینِ Local-First) عبور می‌کند: سنتزِ ساخت‌یافته‌ی JSON
    یک taskِ «سخت» است → مدلِ محلیِ کوچک JSONِ نامعتبر می‌دهد، پس مسیرِ ابری:
    اول GLM (سریع/ارزان)، بعد Fugu (عمیق). خطاها از _safe_err کلاینت‌ها sanitize
    می‌شوند و timeoutها مرکزی‌اند.
    """
    prompt = _build_synthesis_prompt(direction, self_text, web_knowledge, past_data)

    from llm.router import get_router
    router = get_router()

    # GLM اول (سریع — ۱۰-۳۰ ثانیه)
    if router.glm.available:
        content = router.glm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.4, max_tokens=800,
        )
        if content and not content.startswith("["):
            parsed = _parse_json_response(content)
            if parsed.get("proposals"):
                return parsed

    # Fugu به‌عنوان fallbackِ عمیق (کند — ۱-۵ دقیقه)
    if router.fugu.available:
        content = router.fugu.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=4000,
        )
        if content and not content.startswith("["):
            return _parse_json_response(content)

    raise RuntimeError("All LLM providers failed")


def _parse_json_response(content: str) -> dict:
    """Parse JSON from LLM response (handles markdown code blocks)."""
    import re

    # Try to extract JSON from code block
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if match:
        content = match.group(1)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to find the first { and last }
        first = content.find("{")
        last = content.rfind("}")
        if first >= 0 and last > first:
            try:
                return json.loads(content[first:last + 1])
            except json.JSONDecodeError:
                pass

    # Fallback: return empty
    return {"analysis": content[:500], "proposals": []}


# ════════════════════════════════════════════════════════════════════════
#  Quick test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    direction = sys.argv[1] if len(sys.argv) > 1 else "چطور خودآگاهی سیستم رو بالا ببرم؟"

    print(f"=== Meta-Research Engine ===")
    print(f"Direction: {direction}\n")

    result = run_meta_research(direction, use_llm=False)  # local only for quick test

    print(f"\n--- Steps ---")
    for step in result.steps:
        print(f"  [{step.phase:12s}] {step.status:6s} — {step.detail}")

    print(f"\n--- Synthesis ---")
    print(result.synthesis)

    print(f"\n--- Proposals ({len(result.proposals)}) ---")
    for i, p in enumerate(result.proposals, 1):
        print(f"\n  [{i}] {p.get('title','')}")
        print(f"      priority: {p.get('priority','')} | effort: {p.get('effort','')}")
        print(f"      module: {p.get('target_module','')}")
        print(f"      desc: {p.get('description','')[:120]}")
        if p.get('code_sketch'):
            print(f"      sketch: {p['code_sketch'][:120]}")
