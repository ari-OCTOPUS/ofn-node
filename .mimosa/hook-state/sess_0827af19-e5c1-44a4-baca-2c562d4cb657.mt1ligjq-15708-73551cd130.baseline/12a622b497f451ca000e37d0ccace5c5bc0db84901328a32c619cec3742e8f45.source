"""Standalone test — runs all harvesters once and prints to stdout.

No Telegram needed. Use this BEFORE running main.py to validate that:
  - API keys are correct
  - Network reaches PlanningAlerts / AusTender / EstimateOne
  - DB writes work
  - Scoring (Anthropic) works

Usage:  python test_run.py                       # all sources
        python test_run.py --source austender    # one source only
"""
from __future__ import annotations

import asyncio
import sys

from rich.console import Console
from rich.table import Table

import sys as _s
_s.path.insert(0, ".")

from config import settings  # noqa: E402
from db import Lead, get_session, init_db, recent_leads  # noqa: E402
from harvesters import ALL  # noqa: E402
from sqlmodel import select  # noqa: E402

console = Console()


async def main() -> None:
    console.rule("[bold cyan]Paint Leads Bot — test run")
    console.print(f"Operator: [yellow]{settings.operator_name}[/]")
    console.print(f"Suburbs:  [yellow]{', '.join(settings.suburbs_list)}[/]")
    console.print(f"Value:    [yellow]${settings.operator_min_value_aud:,} – ${settings.operator_max_value_aud:,}[/]")
    console.print(f"DB:       [yellow]{settings.db_path}[/]\n")

    init_db()
    console.print("[green]✓[/] DB initialised\n")

    # --- Harvest ---
    console.rule("[bold]Harvesters")
    only = None
    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        only = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if only not in [c.name for c in ALL]:
            console.print(
                f"[red]Unknown source {only!r}. Available: {', '.join(c.name for c in ALL)}[/]"
            )
            return
    targets = [cls for cls in ALL if only in (None, cls.name)]
    for cls in targets:
        console.print(f"[cyan]→ {cls.name}[/]", end=" ")
        try:
            total, new = await cls().run()
            console.print(f"[green]ok[/] fetched={total} new={new}")
        except Exception as e:
            console.print(f"[red]FAIL[/] {type(e).__name__}: {e}")

    # --- Score ---
    console.rule("[bold]Scoring with Claude")
    try:
        from scorer import score_unscored

        scored = score_unscored()
        console.print(f"[green]✓[/] scored {scored} leads\n")
    except Exception as e:
        console.print(f"[red]✗ Scoring failed: {type(e).__name__}: {e}[/]")
        console.print("[yellow]  → verify ANTHROPIC_API_KEY and credit at console.anthropic.com[/]\n")

    # --- Show leads ---
    console.rule("[bold]Recent leads (last 24h)")
    leads = recent_leads(24)
    if not leads:
        console.print("[yellow]No leads found.[/]")
        console.print("[dim]If harvesters reported 0 new, check API keys and network.[/]")
        return

    table = Table(show_lines=False)
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Cat", style="magenta")
    table.add_column("Source", style="cyan")
    table.add_column("Title")
    table.add_column("URL", style="blue", overflow="fold", max_width=40)
    for lead in leads[:20]:
        table.add_row(
            str(lead.score),
            lead.category,
            lead.source,
            lead.title[:70],
            lead.url[:60],
        )
    console.print(table)

    # --- Stats ---
    console.rule("[bold]Stats")
    with get_session() as s:
        total = len(list(s.exec(select(Lead)).all()))
    console.print(f"Total leads in DB: [bold]{total}[/]")
    high = sum(1 for l in leads if l.score >= 80)
    med = sum(1 for l in leads if 50 <= l.score < 80)
    low = sum(1 for l in leads if l.score < 50)
    console.print(f"  high (≥80): [green]{high}[/]   medium (50-79): [yellow]{med}[/]   low (<50): [red]{low}[/]")
    console.print("\n[green bold]✓ Test run complete.[/]")
    console.print("[dim]If everything looks right, run `python main.py` for the full bot.[/]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
