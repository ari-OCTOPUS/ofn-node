"""
main.py — نقطه‌ی ورود LANGAR.
config → init db → ساختِ CORE (brain + agents + router) → polling.
"""

import datetime as _dt
import logging
import os
import sys
from pathlib import Path

import config as _config  # .env را لود و اعتبارسنجی می‌کند

from telegram.ext import Application, PicklePersistence  # noqa: E402

import agents  # noqa: E402
import ailab as ailab_mod  # noqa: E402
import bot  # noqa: E402
import brain  # noqa: E402
import db  # noqa: E402
import researcher as researcher_pkg  # noqa: E402
from core import HumanCore  # noqa: E402
from core import constitution  # noqa: E402
from core.world_model import WorldModel  # noqa: E402
from core.memory import MemorySystem  # noqa: E402
from safety import PatchManager  # noqa: E402
from observability import tracer, log_event  # noqa: E402

STATE_PATH = Path(
    os.environ.get("LANGAR_STATE", Path(__file__).resolve().parent / "langar_state.pickle")
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("langar")


def build_core(cfg) -> HumanCore:
    bank = brain.QuestionBank()
    provider = brain.get_brain_provider(cfg, bank)
    base_prompt = brain.get_system_prompt()
    ag = [
        agents.HealthAgent(provider, bank, base_prompt),
        agents.ReflectionAgent(provider, bank, base_prompt),
        agents.RelationshipAgent(provider, bank, base_prompt),
    ]
    agents.CoachAgent(provider, bank, base_prompt)  # proactive
    router = agents.AgentRouter(ag, weights=db.get_agent_weights())
    world = WorldModel(db, cfg)
    memory = MemorySystem(db)
    log.info("CORE ساخته شد · provider=%s · %d ایجنت", provider.name, len(ag))
    return HumanCore(db, provider, bank, router, base_prompt,
                     world_model=world, memory=memory)


def build_researcher(cfg, core):
    search = researcher_pkg.get_search_provider(cfg)
    patch = PatchManager(brain=core.brain, db=db)
    r = researcher_pkg.Researcher(core.brain, search, db=db, patch_manager=patch,
                                  gate=constitution.is_compliant)
    log.info("Researcher ساخته شد · search=%s", search.name)
    return r, patch


def main() -> None:
    cfg = _config.CONFIG
    problems = _config.validate(cfg)
    if problems:
        for p in problems:
            log.error("پیکربندی: %s", p)
        log.error("ابتدا .env را کامل کن (cp .env.example .env).")
        sys.exit(1)

    # مطمئن شو bot._owner_id مقدارِ تمیزشده را می‌بیند
    os.environ["OWNER_ID"] = cfg.owner_id

    db.init_db()
    log.info("دیتابیس آماده شد: %s (schema v%s)", db.DB_PATH, db.schema_version())

    core = build_core(cfg)
    bot.set_core(core)
    researcher, patch = build_researcher(cfg, core)
    bot.set_researcher(researcher)
    bot.set_patch(patch)
    # BudgetManager — کنترلِ هزینه‌ی AI-Lab
    import budget as budget_mod
    bmgr = budget_mod.BudgetManager(db, _config.ailab_daily_budget(),
                                    _config.ailab_monthly_budget())
    bot.set_budget(bmgr)
    # AI-Lab مستقل (دادهٔ جدا، فقط پیشنهاد، بدونِ اجرای خودکار، با بودجه)
    lab = ailab_mod.AILab(core.brain, researcher_pkg.get_search_provider(cfg),
                          db=db, patch_manager=patch, gate=constitution.is_compliant,
                          budget=bmgr)
    bot.set_ailab(lab)
    log.info("AI-Lab فعال شد · بودجه‌ی روزانه $%.2f / ماهانه $%.2f",
             bmgr.daily, bmgr.monthly)
    # tracer → event_log (شفافیت)
    tracer.set_sink(lambda name, status, info: log_event(db, f"trace:{name}", {"status": status, "info": info}))

    persistence = PicklePersistence(filepath=str(STATE_PATH))
    app = (
        Application.builder()
        .token(cfg.bot_token)
        .persistence(persistence)
        .post_init(bot.post_init)
        .build()
    )
    bot.register(app)

    # بازتابِ خودبهبودیِ روزانه (خودش اگر داده کم باشد رد می‌کند)
    jq = getattr(app, "job_queue", None)
    if jq is not None:
        async def _reflect_job(ctx):
            try:
                core.reflect_and_improve()
            except Exception:
                log.exception("reflect job failed")
        jq.run_daily(_reflect_job, time=_dt.time(hour=cfg.ping_hour, minute=30))

    log.info("🚀 LANGAR شروع شد. مالک: %s", cfg.owner_id)
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
