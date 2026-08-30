"""Registry of all 18 visualisations, grouped + bilingual.

The dashboard imports :data:`REGISTRY` to build its selector and dispatch to
the right renderer. Adding a 19th figure = add a ``VizEntry`` here + a
``render_*`` in the appropriate module. No dashboard edits needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .data import GraphView

__all__ = ["VizEntry", "REGISTRY", "viz_by_id"]


@dataclass(frozen=True)
class VizEntry:
    id: str                 # stable key, never localised
    label: str              # human label (Farsi, shown in the selector)
    group: str              # grouping label for the gallery sections
    dim: str                # "2D" | "3D" | "animated" | "statistical" | "matrix"
    render: Callable[[GraphView, dict], object]   # (view, opts) -> figure
    note: str = ""          # one-line explainer shown under the figure
    heavy: bool = False     # True ⇒ may take a few seconds (show spinner)


def viz_by_id(vid: str) -> VizEntry | None:
    for e in REGISTRY:
        if e.id == vid:
            return e
    return None


# -------------------------------------------------------------------- laziness
# Import the render modules lazily inside each entry so that a broken optional
# dependency (e.g. matplotlib absent) only disables its own figures, not the
# whole import chain.

def _r_network():
    from . import network as m
    return m


def _r_embed():
    from . import embeddings as m
    return m


def _r_stats():
    from . import stats as m
    return m


def _r_time():
    from . import temporal as m
    return m


REGISTRY: tuple[VizEntry, ...] = (
    # ── group: شبکه‌ای / توپولوژیک ──────────────────────────────────────────
    VizEntry("force2d", "گرافِ فشاری ۲بعدی", "شبکه‌ای", "2D",
             lambda v, o: _r_network().render_force2d(v, **o),
             "نودها با spring layout؛ رنگ = فولدر. قلب متراکمِ گراف را نشان می‌دهد.", heavy=True),
    VizEntry("force3d", "گرافِ فشاری ۳بعدی", "شبکه‌ای", "3D",
             lambda v, o: _r_network().render_force3d(v, **o),
             "همان گراف در سه بُعد — بچرخانید تا خوشه‌ها پدیدار شوند.", heavy=True),
    VizEntry("circular", "چیدمانِ حلقوی", "شبکه‌ای", "2D",
             lambda v, o: _r_network().render_circular(v, **o),
             "نودها روی یک دایره، یال‌ها به‌صورت قوس. الگوهای کراس‌لینک را آشکار می‌کند."),
    VizEntry("hierarchy", "درختِ سلسله‌مراتبی", "شبکه‌ای", "2D",
             lambda v, o: _r_network().render_hierarchy(v, **o),
             "ساختارِ فولدر/زیرفولدر به‌شکل درخت."),
    VizEntry("arc", "نمودارِ قوسی (Arc)", "شبکه‌ای", "2D",
             lambda v, o: _r_network().render_arc(v, **o),
             "نودها روی محور افقی، یال‌ها به‌شکل نیم‌دایره — متراکم‌بودنِ لینک‌ها را نشان می‌دهد."),
    VizEntry("bipartite", "دوجهتهٔ فولدر↔نود", "شبکه‌ای", "2D",
             lambda v, o: _r_network().render_bipartite(v, **o),
             "هر نوت به فولدرِ بالادستی‌اش متصل است — توزیع نوت‌ها در فولدرها."),

    # ── group: تعبیه‌شده / سه‌بعدی ────────────────────────────────────────────
    VizEntry("spectral3d", "تعبیهٔ طیفی ۳بعدی", "تعبیه‌شده", "3D",
             lambda v, o: _r_embed().render_spectral3d(v, **o),
             "سه ویژگیِ اولِ eigendecompositionِ لاپلاسین گراف.", heavy=True),
    VizEntry("tsne2d", "تعبیهٔ t-SNE دوبعدی", "تعبیه‌شده", "2D",
             lambda v, o: _r_embed().render_tsne2d(v, **o),
             "کاهش بُعدِ غیرخطی — خوشه‌های معناییِ نهفته را نمایان می‌کند.", heavy=True),
    VizEntry("isomap2d", "تعبیهٔ Isomap دوبعدی", "تعبیه‌شده", "2D",
             lambda v, o: _r_embed().render_isomap2d(v, **o),
             "MDS روی فاصلهٔ ژئودزیکِ گراف — ساختارِ متناظر را می‌کشد.", heavy=True),
    VizEntry("globe3d", "کرهٔ ۳بعدی (pydeck)", "تعبیه‌شده", "3D",
             lambda v, o: _r_embed().render_globe3d(v, **o),
             "نودها روی یک کره پراکنده‌اند — نمایشِ نمایشیِ ساختار."),

    # ── group: تحلیلی / آماری ────────────────────────────────────────────────
    VizEntry("degreedist", "توزیعِ درجه (Power-law)", "تحلیلی", "statistical",
             lambda v, o: _r_stats().render_degree_dist(v, **o),
             "log-log توزیعِ درجه — آیا vault از قانونِ قدرت پیروی می‌کند؟"),
    VizEntry("adjmatrix", "ماتریسِ مجاورت", "تحلیلی", "matrix",
             lambda v, o: _r_stats().render_adjacency(v, **o),
             "ماتریسِ مجاورتِ مرتب‌شده بر اساس خوشه — بلوک‌بندی را آشکار می‌کند."),
    VizEntry("treemap", "Treemap خوشه‌ها", "تحلیلی", "2D",
             lambda v, o: _r_stats().render_treemap(v, **o),
             "هر خوشه/فولدر یک مستطیل به‌اندازهٔ تعداد نوت."),
    VizEntry("folderheat", "حرارتیِ فولدر↔فولدر", "تحلیلی", "matrix",
             lambda v, o: _r_stats().render_folder_heat(v, **o),
             "تعداد یالِ بینِ هر جفت فولدر — پل‌های بین‌فولدری."),
    VizEntry("radar", "رادارِ مقایسهٔ hubها", "تحلیلی", "2D",
             lambda v, o: _r_stats().render_radar(v, **o),
             "مقایسهٔ ۵ hub برتر روی چند معیار."),

    # ── group: زمانی / انیمیشنی ──────────────────────────────────────────────
    VizEntry("growth", "رشدِ انیمیشنی گراف", "زمانی", "animated",
             lambda v, o: _r_time().render_growth(v, **o),
             "گراف در طول زمانِ mtime رشد می‌کند — فریم‌به‌فریم.", heavy=True),
    VizEntry("sunburst", "Sunburst فولدرها", "زمانی", "2D",
             lambda v, o: _r_time().render_sunburst(v, **o),
             "سلسله‌مراتبِ فولدرها به‌شکل خورشیدی."),
    VizEntry("sankey", "Sankey جریانِ فولدرها", "زمانی", "2D",
             lambda v, o: _r_time().render_sankey(v, **o),
             "یال‌های بین‌فولدری به‌شکل جریان — حجمِ اتصالِ فولدرها."),
)


GROUPS = ("شبکه‌ای", "تعبیه‌شده", "تحلیلی", "زمانی")
