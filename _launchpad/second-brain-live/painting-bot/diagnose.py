"""Full diagnostic — tests each API key and source in isolation.

Run BEFORE test_run.py or main.py to know exactly what works.

Usage:  python diagnose.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console

console = Console()
results: dict[str, tuple[bool, str]] = {}


def check(name: str):
    """Decorator-ish wrapper. Captures pass/fail with message."""
    def wrap(fn):
        async def run():
            console.print(f"\n[bold cyan]► {name}[/]")
            try:
                msg = await fn() if asyncio.iscoroutinefunction(fn) else fn()
                results[name] = (True, msg or "OK")
                console.print(f"  [green]✓ PASS[/] {msg or ''}")
            except Exception as e:
                results[name] = (False, f"{type(e).__name__}: {e}")
                console.print(f"  [red]✗ FAIL[/] {type(e).__name__}: {e}")
                if "--verbose" in sys.argv:
                    traceback.print_exc()
        return run
    return wrap


# ──────────────────────────────────────────────────────────────

@check("Config loads")
def t_config():
    from config import settings
    return (
        f"operator={settings.operator_name} | "
        f"suburbs={len(settings.suburbs_list)} | "
        f"model={settings.llm_model}"
    )


@check("Anthropic API key works")
def t_anthropic():
    from anthropic import Anthropic
    from config import settings
    c = Anthropic(api_key=settings.anthropic_api_key)
    # Try several model names since names change frequently
    for model in ("claude-sonnet-4-5", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"):
        try:
            r = c.messages.create(
                model=model,
                max_tokens=20,
                messages=[{"role": "user", "content": "reply: OK"}],
            )
            text = r.content[0].text.strip()
            return f"model={model} reply={text!r} tokens_in={r.usage.input_tokens} out={r.usage.output_tokens}"
        except Exception as e:
            if "model" in str(e).lower() or "404" in str(e):
                continue
            raise
    raise RuntimeError("no working model found")


@check("Anthropic — configured model (settings.llm_model)")
def t_anthropic_configured():
    from anthropic import Anthropic
    from config import settings
    c = Anthropic(api_key=settings.anthropic_api_key)
    r = c.messages.create(
        model=settings.llm_model,
        max_tokens=20,
        messages=[{"role": "user", "content": "reply: OK"}],
    )
    return f"model={settings.llm_model} reply={r.content[0].text.strip()!r}"


@check("Tavily API key works")
def t_tavily():
    from tavily import TavilyClient
    from config import settings
    c = TavilyClient(api_key=settings.tavily_api_key)
    r = c.search(query="Sydney NSW painting tender", max_results=2)
    n = len(r.get("results", []))
    if n == 0:
        raise RuntimeError("0 results returned")
    return f"{n} results, first={r['results'][0].get('title','')[:60]!r}"


@check("Telegram bot token (getMe)")
def t_telegram():
    import httpx
    from config import settings
    r = httpx.get(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe",
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"API error: {data}")
    bot = data["result"]
    return f"@{bot['username']} (id={bot['id']})"


@check("Telegram — chat_id resolves to a real chat")
def t_telegram_chat():
    import httpx
    from config import settings
    raw = str(settings.telegram_chat_id).strip()
    if raw.endswith("_bot"):
        raise RuntimeError(
            f"chat_id is a BOT username ({raw}). Bot cannot DM itself. "
            "Get your personal id from getUpdates."
        )
    r = httpx.get(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/getChat",
        params={"chat_id": settings.chat_id_for_telegram},
        timeout=10,
    )
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"chat not reachable: {data.get('description','?')}")
    chat = data["result"]
    return f"type={chat.get('type')} title={chat.get('title') or chat.get('first_name','-')}"


@check("PlanningAlerts API key works")
async def t_planning_alerts():
    import asyncio
    import httpx
    from config import settings
    delay = 3.0
    async with httpx.AsyncClient(timeout=20) as c:
        for attempt in range(4):
            r = await c.get(
                "https://api.planningalerts.org.au/authorities/sydney/applications.json",
                params={"key": settings.planning_alerts_api_key, "page": 1},
            )
            if r.status_code == 429:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            break
        r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        n = len(data)
    elif isinstance(data, dict):
        n = len(data.get("applications", []))
    else:
        n = 0
    return f"sydney council returned {n} applications"


@check("AusTender search page reachable")
async def t_austender():
    import httpx
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"},
        timeout=20, follow_redirects=True,
    ) as c:
        r = await c.get("https://www.tenders.gov.au/atm/search/", params={"keyword": "painting"})
    return f"HTTP {r.status_code}, length={len(r.text):,} chars"


@check("EstimateOne page reachable")
async def t_estimate_one():
    import httpx
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
                 "Accept": "text/html,application/xhtml+xml",
                 "Accept-Language": "en-AU,en;q=0.9"},
        timeout=20, follow_redirects=True,
    ) as c:
        r = await c.get("https://estimateone.com/tenders/new-south-wales-tenders/")
    return f"HTTP {r.status_code}, length={len(r.text):,} chars"


@check("Run all harvesters (real fetch)")
async def t_harvesters():
    from db import init_db
    init_db()
    from harvesters import ALL
    counts = []
    for cls in ALL:
        try:
            total, new = await cls().run()
            counts.append(f"{cls.name}={total}")
        except Exception as e:
            counts.append(f"{cls.name}=ERR({type(e).__name__})")
    return " | ".join(counts)


# ──────────────────────────────────────────────────────────────

async def main():
    console.rule("[bold magenta]Paint Leads Bot — diagnostics")
    for fn in [
        t_config, t_anthropic, t_anthropic_configured, t_tavily,
        t_telegram, t_telegram_chat, t_planning_alerts,
        t_austender, t_estimate_one, t_harvesters,
    ]:
        await fn()

    console.rule("[bold]Summary")
    pass_count = sum(1 for ok, _ in results.values() if ok)
    fail_count = len(results) - pass_count
    for name, (ok, msg) in results.items():
        mark = "[green]✓[/]" if ok else "[red]✗[/]"
        console.print(f"  {mark} {name}")
    console.print(
        f"\n[bold green]{pass_count} passed[/]  [bold red]{fail_count} failed[/]"
    )
    if fail_count == 0:
        console.print("\n[green bold]All systems go — run `python main.py`[/]")
    else:
        console.print("\n[yellow]Fix the failures above, then re-run `python diagnose.py`[/]")
        console.print("[dim]Run with --verbose for full tracebacks[/]")


if __name__ == "__main__":
    asyncio.run(main())
