"""Read-only dashboard (mini-app) — v0.2, with live scan + 18 visualisations.

Answers NBB-V2 in VERDICT_QUEUE.md with a "yes, read-only" implementation:
the app never touches the vault. It can *record* an approve/reject verdict, and
that verdict is written to the OUTPUT directory only — applying it to notes
remains a separate, human-initiated act (INV-2).

v0.2 adds, without changing any existing behaviour:
  * a **live** file-watcher (watchdog) that flags when the vault changes,
  * a **cache** keyed on the link-graph fingerprint (re-run is instant unless
    the structure actually moved),
  * an **auto-refresh** tick (every 15 s) that surfaces the "changed" banner,
  * a **live-click** modal: click a node → read its real note body (read-only),
  * a new **«نمایش‌ها» (Visualisations)** tab with 18 graphical representations.

    streamlit run src/nbb_cp_kre/ui/streamlit_app.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nbb_cp_kre.app.pipeline import load_result, run_pipeline   # noqa: E402
from nbb_cp_kre.kernel.guard import ReadOnlyGuard, ReadOnlyViolation  # noqa: E402

# dataviz reference palette (light)
BLUE, RED, MUTED, INK2, GRID = "#2a78d6", "#d03b3b", "#898781", "#52514e", "#e1e0d9"
LIVE_GREEN = "#0ca30c"

st.set_page_config(page_title="Octopus · Knowledge Reality", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""<style>
.block-container {{padding-top:2.2rem;max-width:1400px}}
[data-testid="stMetricValue"] {{font-size:1.6rem}}
.ro-badge {{display:inline-block;padding:2px 10px;border-radius:999px;
  background:#eef4fd;color:{BLUE};font-size:.78rem;border:1px solid #d6e5fa}}
.live-badge {{display:inline-block;padding:2px 10px;border-radius:999px;
  background:#eef7ef;color:{LIVE_GREEN};font-size:.78rem;border:1px solid #cfe9cf}}
.warn {{background:#fdf2f2;border-left:3px solid {RED};padding:.6rem .9rem;
  border-radius:4px;margin:.35rem 0;font-size:.88rem}}
.ok {{background:#f1f7ef;border-left:3px solid #0ca30c;padding:.6rem .9rem;
  border-radius:4px;margin:.35rem 0;font-size:.88rem}}
.pending {{background:#fff8e6;border-left:3px solid #e08e0b;padding:.6rem .9rem;
  border-radius:4px;margin:.35rem 0;font-size:.9rem}}
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------- visualisations tab
def _load_view(out_dir: str, fingerprint: str):
    """Build the GraphView once per (output dir, graph fingerprint) and keep it
    in session_state. Rebuilds only when the link graph actually changes — so
    the 18-figure gallery shares one community/layout precompute.

    We deliberately do NOT use st.cache_data: it pickles the return value, and
    a GraphView carries a networkx graph that is large + awkward to round-trip.
    session_state is plenty: it lives for the user's session."""
    key = ("view", out_dir, fingerprint)
    if st.session_state.get(key) is None:
        from nbb_cp_kre.adapters.viz import load_graph_view
        st.session_state[key] = load_graph_view(out_dir)
    return st.session_state[key]


def _render_viz_tab(out_dir: str, vault_root: str, fingerprint: str) -> None:
    """The ⑤ نمایش‌ها tab: a gallery selector + the chosen figure + a live-click
    inspector for reading a single note's body (read-only)."""
    from nbb_cp_kre.adapters.viz import REGISTRY, viz_by_id

    view = _load_view(out_dir, fingerprint)
    if view is None:
        st.info("No graph artifact yet — run an analysis first.")
        return

    st.subheader("۱۸ نمایش گرافیکیِ گرافِ vault")
    st.caption(f"{view.n_nodes:,} نود · {view.n_edges:,} یال · {view.n_communities} خوشه · "
               f"fingerprint `{view.fingerprint}`")

    # --- gallery grouped by family -----------------------------------------
    col_sel, col_opt = st.columns([1.4, 1])
    with col_sel:
        groups: dict[str, list] = {}
        for e in REGISTRY:
            groups.setdefault(e.group, []).append(e)
        group_tabs = st.tabs(list(groups.keys()))
        choice = st.session_state.get("viz_choice", "force2d")
        for gt, gname in zip(group_tabs, groups):
            for e in groups[gname]:
                dim_tag = {"2D": "۲بعدی", "3D": "۳بعدی", "animated": "انیمیشن",
                           "statistical": "آماری", "matrix": "ماتریسی"}.get(e.dim, e.dim)
                heavy_tag = " · ⏳ کند" if e.heavy else ""
                if gt.button(f"**{e.label}**  ({dim_tag}{heavy_tag})", use_container_width=True,
                             key=f"vizbtn_{e.id}",
                             type="primary" if choice == e.id else "secondary"):
                    st.session_state["viz_choice"] = e.id
                    st.rerun()

    chosen_id = st.session_state.get("viz_choice", "force2d")
    entry = viz_by_id(chosen_id) or REGISTRY[0]

    with col_opt:
        st.markdown("**گزینه‌ها**")
        show_labels = st.checkbox("نمایشِ برچسبِ نودها", value=True,
                                  key=f"opt_labels_{chosen_id}")
        max_nodes = st.slider("حداکثر نود (نمونه‌برداری)", 400, 3000, 1500, 100,
                              key=f"opt_maxnodes_{chosen_id}")
        st.caption("برای گراف‌های بزرگ، چیدمان‌های سنگین نمونه‌برداری می‌کنند — تعداد در "
                   "عنوانِ شکل نوشته می‌شود، هرگز خاموش نیست.")

    # --- render the chosen figure ------------------------------------------
    st.divider()
    heavy = entry.heavy
    with (st.spinner(f"رسمِ «{entry.label}»… این نمایش سنگین است، چند ثانیه…") if heavy
          else st.empty()):
        try:
            fig = entry.render(view, {"max_nodes": max_nodes, "show_labels": show_labels})
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"{entry.label}: {type(exc).__name__}: {exc}")
    if entry.note:
        st.caption(f"ℹ️ {entry.note}")

    # --- live-click: read a note's body -----------------------------------
    st.divider()
    st.markdown("**🔍 خواندنِ محتوای یک نوت (فقط خواندن)**")
    st.caption("نوت را انتخاب کن تا بدنه‌اش از داخلِ vault خوانده شود (بدون هیچ نوشتن). "
               "محتوا به‌عنوانِ دادهٔ نامعتبر karantina می‌شود — هرگز اجرا نمی‌شود.")
    all_nodes = view.nodes
    # search box + datalist-like dropdown: st.selectbox with searchable options
    # via a text input filter for large vaults.
    q = st.text_input("جستجوی نوت (بخشی از نام/مسیر)…", value="", key="viz_note_search")
    matches = [n for n in all_nodes if q.lower() in n.lower()][:200] if q else []
    if q and matches:
        pick = st.selectbox(f"{len(matches)} نوت یافت شد (نمایشِ ۲۰۰تای اول)",
                            options=matches, key="viz_note_pick")
        if pick and st.button("نمایشِ محتوا", key="viz_note_show"):
            try:
                from nbb_cp_kre.app.live import read_note_body
                qtext = read_note_body(vault_root, pick)
                deg = view.degree.get(pick, 0)
                folder = view.folder_of.get(pick, "?")
                st.markdown(f"**{pick}** · فولدر `{folder}` · درجه {deg}")
                # unwrap_for_parsing is the explicit, reviewed path for display
                st.code(qtext.unwrap_for_parsing(), language="markdown")
                st.caption(f"📅 فایل: `{Path(vault_root) / pick}`")
            except ReadOnlyViolation as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"{type(exc).__name__}: {exc}")
    elif q:
        st.info("هیچ نتیجه‌ای یافت نشد.")



# ------------------------------------------------------ start the live watcher
# One watcher per Streamlit server process. Stored in st.session_state so it
# survives re-runs. It only reads the vault and writes pending.json OUTSIDE it.
def _ensure_watcher(vault: str, out: str) -> None:
    key = ("watcher", vault, out)
    if st.session_state.get(key) is not None:
        return
    try:
        from nbb_cp_kre.adapters.vault.watcher import VaultWatcher
        w = VaultWatcher(vault, out)
        if w.start():
            st.session_state[key] = w
    except Exception:
        pass                      # live mode is best-effort; manual re-run still works


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### Octopus · Knowledge Reality")
    st.markdown('<span class="ro-badge">vault is READ-ONLY</span> '
                '<span class="live-badge">● LIVE</span>', unsafe_allow_html=True)
    st.caption("This app never writes inside the vault. All artifacts go to the output folder.")
    vault = st.text_input("Vault root", value=os.environ.get("KRE_VAULT", r"F:\backup"))
    out = st.text_input("Output folder", value=os.environ.get("KRE_OUT", r"F:\kre-out"))

    st.divider()
    seeds = st.slider("Splits (seeds)", 3, 15, 5,
                      help="More splits = tighter error bars, linearly more time.")
    test_frac = st.slider("Held-out edge fraction", 0.05, 0.40, 0.20, 0.05)
    top_k = st.slider("Missing-link proposals", 10, 200, 40, 10)
    extra_ex = st.text_input("Extra excluded folders (comma-separated)", value="")
    include_embeds = st.checkbox("Count ![[embeds]] as links", value=True)
    live_mode = st.checkbox("Live scan (file watcher + auto-refresh)", value=True,
                            help="Watches the vault for .md changes and re-scans when the link graph moves.")

    go = st.button("Run analysis", type="primary", use_container_width=True)
    st.caption("Re-running never modifies the vault; it only refreshes the output folder.")


def _do_run(force=False):
    """Run the live pipeline (fingerprint-cached) and clear the pending flag."""
    try:
        ReadOnlyGuard([vault]).assert_out_dir(out)
    except ReadOnlyViolation as exc:
        st.error(f"Read-only guard tripped — pick an output folder outside the vault.\n\n{exc}")
        st.stop()
    bar = st.progress(0.0, text="starting…")
    try:
        from nbb_cp_kre.app.live import run_live
        run_live(
            vault, out, seeds=list(range(seeds)), test_frac=test_frac, top_k=top_k,
            extra_excludes=frozenset(x.strip() for x in extra_ex.split(",") if x.strip()),
            include_embeds=include_embeds, quick=False, force=force,
            progress=lambda f, m: bar.progress(min(f, 1.0), text=m),
        )
    except Exception as exc:                                    # fail closed + show why
        bar.empty()
        st.error(f"{type(exc).__name__}: {exc}")
        st.stop()
    bar.empty()
    # tell the watcher the scan is accepted → clears the "vault changed" banner
    try:
        from nbb_cp_kre.adapters.vault.watcher import clear_pending
        clear_pending(vault, out)
    except Exception:
        pass


if live_mode and vault and out:
    _ensure_watcher(vault, out)

if go:
    _do_run(force=True)

data = load_result(out) if out else None

# ---------------------------------------------------- the live "changed" banner
_pending = None
if live_mode and out:
    try:
        from nbb_cp_kre.adapters.vault.watcher import read_pending
        _pending = read_pending(out)
    except Exception:
        _pending = None

if _pending is not None and _pending.pending and _pending.n_events_since_scan > 0:
    st.markdown(
        f'<div class="pending">📡 <b>vault تغییر کرد</b> — {_pending.n_events_since_scan} '
        f'رویداد از آخرین اسکن (آخرین تغییر: {_pending.last_event_at}). '
        f'<b>اسکنِ خودکار در حال اجراست…</b></div>', unsafe_allow_html=True)
    if live_mode:
        # auto re-run only when the graph structure is likely to have changed.
        # We don't rebuild on every keystroke — the auto-refresh fragment below
        # gates this on the fingerprint probe.
        _do_run(force=False)
        st.rerun()

if not data:
    st.title("Knowledge Reality Engine")
    st.info("Set the vault root and output folder in the sidebar, then press **Run analysis**.")
    st.markdown(
        "**What this does** — walks the vault read-only, builds the real `[[wikilink]]` "
        "graph with Obsidian-accurate resolution, makes several mathematical "
        "representations compete on held-out link prediction, and ranks the links your "
        "vault is missing. Nothing is written to the vault, ever.\n\n"
        "**v0.2** — 18 تصویری، اسکنِ زنده، و کلیک روی نود برای دیدنِ محتوای نوت.")
    st.stop()

scan, graph, bake, props = data["scan"], data["graph"], data.get("bakeoff"), data.get("proposals", [])

st.title("Knowledge Reality Engine")
live_tag = ' <span class="live-badge">● LIVE</span>' if live_mode else ""
st.caption(f"vault `{data['vault_root']}` · scanned {scan['scanned_at']} · "
           f"graph fingerprint `{graph['fingerprint']}`{live_tag}",
           unsafe_allow_html=True)

c = st.columns(5)
c[0].metric("Notes", f"{graph['n_nodes']:,}")
c[1].metric("Links", f"{graph['n_edges']:,}")
c[2].metric("Avg degree", f"{graph['avg_degree']:.2f}")
c[3].metric("Orphans", f"{graph['isolated_notes']:,}",
            delta=f"{graph['isolated_pct']*100:.1f}% of vault", delta_color="off")
c[4].metric("Broken links", f"{graph['broken_links']:,}")

for w in scan.get("warnings", []):
    st.markdown(f'<div class="warn">⚠ {w}</div>', unsafe_allow_html=True)

t_scan, t_graph, t_comp, t_prop, t_viz = st.tabs(
    ["① Scan health", "② Link graph", "③ Representation competition",
     "④ Missing links", "⑤ نمایش‌ها (Visualisations)"])

# ------------------------------------------------------------------ ① scan
with t_scan:
    a, b = st.columns([1.35, 1])
    with a:
        st.subheader("Notes per top-level folder")
        df = (pd.DataFrame(list(scan["per_top_folder"].items()), columns=["folder", "notes"])
              .sort_values("notes", ascending=False).head(25))
        st.bar_chart(df.set_index("folder"), color=BLUE, height=430)
        st.caption("If one folder holds almost everything, it is probably tooling, not notes — "
                   "add it to the excludes and re-run.")
    with b:
        st.subheader("Scan facts")
        st.dataframe(pd.DataFrame({
            "metric": ["dirs walked", "files seen", "markdown notes", "markdown MB",
                       "elapsed (s)", "cap hit", "unreadable", "too large"],
            "value": [f"{scan['n_dirs_walked']:,}", f"{scan['n_files_seen']:,}",
                      f"{scan['n_markdown']:,}", f"{scan['bytes_markdown']/1048576:.1f}",
                      scan["elapsed_s"], "YES" if scan["cap_hit"] else "no",
                      len(scan["unreadable"]), len(scan["skipped_too_large"])],
        }), hide_index=True, use_container_width=True)
        if scan["excluded_hits"]:
            st.subheader("Excluded folders (hits)")
            st.dataframe(pd.DataFrame(list(scan["excluded_hits"].items())[:20],
                                      columns=["folder", "times skipped"]),
                         hide_index=True, use_container_width=True)

# ----------------------------------------------------------------- ② graph
with t_graph:
    a, b = st.columns([1, 1])
    with a:
        st.subheader("Most connected notes (hubs)")
        st.dataframe(pd.DataFrame(graph["hubs"]), hide_index=True, use_container_width=True)
        st.subheader("Link resolution")
        r = graph["resolution"]
        st.dataframe(pd.DataFrame({"how the link resolved": list(r), "count": list(r.values())}),
                     hide_index=True, use_container_width=True)
        if r.get("ambiguous"):
            st.markdown(
                f'<div class="warn">{r["ambiguous"]:,} links matched more than one note by '
                f'basename (e.g. several <code>INDEX.md</code>). The shortest path won; '
                f'write those links as full vault paths to remove the guesswork.</div>',
                unsafe_allow_html=True)
    with b:
        st.subheader("Structure")
        st.dataframe(pd.DataFrame({
            "metric": ["nodes", "edges", "avg degree", "median degree", "orphan notes",
                       "orphan %", "broken links", "ambiguous links"],
            "value": [graph["n_nodes"], graph["n_edges"], graph["avg_degree"],
                      graph["median_degree"], graph["isolated_notes"],
                      f"{graph['isolated_pct']*100:.1f}%", graph["broken_links"],
                      graph["ambiguous_links"]],
        }), hide_index=True, use_container_width=True)
        st.subheader("Notes per folder")
        st.dataframe(pd.DataFrame(list(graph["notes_per_top_folder"].items())[:25],
                                  columns=["folder", "notes"]),
                     hide_index=True, use_container_width=True)

# ----------------------------------------------------------- ③ competition
with t_comp:
    if not bake:
        st.info("No competition was run for this snapshot.")
    elif not bake["scores"]:
        for n in bake["notes"]:
            st.markdown(f'<div class="warn">{n}</div>', unsafe_allow_html=True)
    else:
        if bake["control_ok"]:
            st.markdown(
                f'<div class="ok">Control check passed — the random scorer landed at AUC '
                f'{bake["control_auc"]:.3f} (chance = 0.500), so the held-out split did not '
                f'leak. The numbers below are trustworthy.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warn">CONTROL FAILED — results are void.</div>',
                        unsafe_allow_html=True)

        rows = [s for s in bake["scores"] if not s["skipped"]]
        df = pd.DataFrame(rows)[["name", "auc_mean", "auc_std", "ap_mean", "seconds"]]
        df.columns = ["representation", "AUC", "±sd", "AP", "sec"]
        a, b = st.columns([1.3, 1])
        with a:
            st.subheader("AUC by representation")
            # 0.50 is a real midpoint (chance), so bars grow OUT of it and the two
            # sides get opposite hues — a diverging encoding, not a plain magnitude bar.
            d = df.rename(columns={"representation": "rep"}).copy()
            d["lo"] = d["AUC"].clip(upper=0.5)
            d["hi"] = d["AUC"].clip(lower=0.5)
            d["side"] = ["above chance" if v >= 0.5 else "below chance" for v in d["AUC"]]
            base = alt.Chart(d)
            bars = base.mark_bar(height=18, cornerRadius=3, stroke="#fcfcfb",
                                 strokeWidth=2).encode(
                y=alt.Y("rep:N", title=None,
                        sort=alt.EncodingSortField(field="AUC", order="descending"),
                        axis=alt.Axis(labelColor=INK2, domain=False, ticks=False)),
                x=alt.X("lo:Q", title="AUC   ·   0.50 = chance",
                        scale=alt.Scale(domain=[0.40, max(0.75, float(d["AUC"].max()) + 0.05)]),
                        axis=alt.Axis(gridColor=GRID, domainColor=GRID,
                                      tickColor=GRID, labelColor=MUTED)),
                x2="hi:Q",
                color=alt.Color("side:N", scale=alt.Scale(
                    domain=["above chance", "below chance"], range=[BLUE, RED]),
                    legend=alt.Legend(title=None, orient="bottom", labelColor=INK2)),
                tooltip=[alt.Tooltip("rep:N", title="representation"),
                         alt.Tooltip("AUC:Q", format=".3f"),
                         alt.Tooltip("±sd:Q", format=".3f"),
                         alt.Tooltip("AP:Q", format=".3f"),
                         alt.Tooltip("sec:Q", title="seconds", format=".1f")])
            labels = base.mark_text(align="left", dx=6, color=INK2, fontSize=11).encode(
                y=alt.Y("rep:N", sort=alt.EncodingSortField(field="AUC", order="descending")),
                x=alt.X("AUC:Q"),
                text=alt.Text("AUC:Q", format=".3f"))
            rule = alt.Chart(pd.DataFrame({"x": [0.5]})).mark_rule(
                color=MUTED, strokeWidth=1.2).encode(x="x:Q")
            st.altair_chart((bars + rule + labels).properties(height=max(240, 42 * len(d))),
                            use_container_width=True)
            st.caption("Bars grow out of 0.50 (chance). Left of the line the representation is "
                       "actively anti-predictive on this vault, not merely useless. "
                       "Hover for AP and runtime; the full table is on the right.")
        with b:
            st.subheader("Winner")
            if bake["winner"]:
                w = next(s for s in rows if s["name"] == bake["winner"])
                st.metric(bake["winner"], f"{w['auc_mean']:.3f}",
                          delta=(f"{bake['winner_beats_baseline_by']:+.3f} vs {bake['baseline']}"
                                 if bake["winner_beats_baseline_by"] is not None else None))
            st.dataframe(df.style.format({"AUC": "{:.3f}", "±sd": "{:.3f}",
                                          "AP": "{:.3f}", "sec": "{:.1f}"}),
                         hide_index=True, use_container_width=True)
        skipped = [s for s in bake["scores"] if s["skipped"]]
        if skipped:
            st.subheader("Skipped (and why) — no silent caps")
            st.dataframe(pd.DataFrame([{"representation": s["name"], "reason": s["skip_reason"]}
                                       for s in skipped]),
                         hide_index=True, use_container_width=True)
        for n in bake["notes"]:
            st.markdown(f'<div class="warn">{n}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------ ④ proposals
with t_prop:
    st.subheader("Links your vault is probably missing")
    st.caption("Ranked by the representation that actually won on YOUR vault. "
               "These are proposals — approving one records a verdict in the output "
               "folder; it does not edit any note.")
    if not props:
        st.info("No proposals in this snapshot.")
    else:
        vp = Path(out) / "verdicts.json"
        verdicts = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else {}
        df = pd.DataFrame([{
            "rank": p["rank"], "score": round(p["score"], 3),
            "source": p["source"], "target": p["target"],
            "shared": p["evidence"].get("shared_neighbours", 0),
            "verdict": verdicts.get(p["proposal_id"] if "proposal_id" in p else
                                    f"{p['source']}->{p['target']}", "—"),
        } for p in props])
        edited = st.data_editor(
            df, hide_index=True, use_container_width=True, height=520,
            column_config={"verdict": st.column_config.SelectboxColumn(
                "verdict", options=["—", "approve", "reject"], width="small")},
            disabled=["rank", "score", "source", "target", "shared"])
        if st.button("Save verdicts (to the output folder only)"):
            try:
                guard = ReadOnlyGuard([data["vault_root"]])
                new = {f"{r.source}->{r.target}": r.verdict
                       for r in edited.itertuples() if r.verdict != "—"}
                with guard.open_write(vp) as fh:
                    json.dump(new, fh, ensure_ascii=False, indent=2)
                st.success(f"{len(new)} verdicts saved to {vp} — the vault was not touched.")
            except ReadOnlyViolation as exc:
                st.error(str(exc))
        st.download_button("Download proposals as CSV",
                           edited.to_csv(index=False).encode("utf-8"),
                           file_name="missing_links.csv", mime="text/csv")

# ----------------------------------------------------- ⑤ visualisations (NEW)
with t_viz:
    _render_viz_tab(out, vault, graph["fingerprint"])


# ------------------------------------------------- auto-refresh fragment
# Polls pending.json every 15s. If the vault changed, it re-runs (cached unless
# the fingerprint moved) and rerolls the page. This is the "auto-refresh دورهای"
# requirement — implemented as a fragment so it doesn't reload the whole app on
# every interaction, only on the timer.
if live_mode and data:
    @st.fragment(run_every=15)
    def _heartbeat():
        try:
            from nbb_cp_kre.adapters.vault.watcher import read_pending
            st_status = read_pending(out)
        except Exception:
            st_status = None
        if st_status is not None and st_status.pending and st_status.n_events_since_scan > 0:
            st.toast(f"📡 vault changed ({st_status.n_events_since_scan} events) — re-scanning…")
            st.rerun()

    _heartbeat()
