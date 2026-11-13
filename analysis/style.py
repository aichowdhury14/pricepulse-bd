"""Matplotlib house style: validated categorical palette, thin marks, hairline chrome.

Palette = dataviz reference instance (light mode). Categorical slots are used in
fixed order and follow the entity, never its rank.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
CONTEXT = "#c3c2b7"  # de-emphasised series (highlight-one, grey-the-rest)
# diverging blue <-> red with grey midpoint
DIVERGING = ["#184f95", "#3987e5", "#9ec5f4", "#f0efec", "#f2a3a2", "#e34948", "#a32a2a"]
UP, DOWN = "#e34948", "#2a78d6"  # price up = red, price down = blue (polarity, not status)


def apply() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 10,
        "text.color": INK, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2, "xtick.major.size": 0, "ytick.major.size": 0,
        "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
        "legend.frameon": False, "legend.fontsize": 9,
        "axes.prop_cycle": mpl.cycler(color=SERIES),
    })


def subtitle(ax, text: str) -> None:
    # offset in points (not axes fraction) so tall figures don't push it into the title
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction", xytext=(0, 5),
                textcoords="offset points", color=INK_2, fontsize=9, va="bottom")


def save(fig, name: str) -> str:
    from .data import FIGURES
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return str(path)
