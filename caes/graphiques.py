# -*- coding: utf-8 -*-
"""Style commun des graphiques de validation.

Palette catégorielle validée (ordre fixe, 4 couleurs), encres neutres,
grille discrète, étiquettes directes en fin de courbe.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COULEURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
ENCRE = "#0b0b0b"
ENCRE_2 = "#52514e"
GRILLE = "#e6e5e1"
SURFACE = "#fcfcfb"


def nouvelle_figure(
    largeur: float = 8.0, hauteur: float = 4.5
) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(largeur, hauteur), dpi=130)
    fig.patch.set_facecolor(SURFACE)
    return fig, ax


def style_axes(ax: plt.Axes, titre: str, x: str, y: str) -> None:
    ax.set_facecolor(SURFACE)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)
    ax.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=ENCRE_2, labelsize=9)
    ax.set_title(titre, loc="left", color=ENCRE, fontsize=11)
    ax.set_xlabel(x, color=ENCRE_2, fontsize=9)
    ax.set_ylabel(y, color=ENCRE_2, fontsize=9)


def etiquette_fin(
    ax: plt.Axes, x: float, y: float, texte: str, couleur: str
) -> None:
    ax.annotate(
        texte, (x, y), xytext=(6, 0), textcoords="offset points",
        va="center", fontsize=9, color=ENCRE_2,
        bbox={"boxstyle": "round,pad=0.15", "fc": SURFACE, "ec": "none"},
    )
    ax.plot([x], [y], marker="o", ms=5, color=couleur, mec=SURFACE, mew=1.5)


def point_reference(
    ax: plt.Axes, x: float, y: float, texte: str
) -> None:
    ax.plot(
        [x], [y], marker="D", ms=7, color=ENCRE, mec=SURFACE, mew=1.5,
        linestyle="none", label=texte,
    )


def terminer(
    fig: plt.Figure,
    ax: plt.Axes,
    chemin: Path,
    legende: str | None = "best",
) -> str:
    if legende:
        ax.legend(frameon=False, fontsize=8, labelcolor=ENCRE_2, loc=legende)
    fig.tight_layout()
    fig.savefig(chemin)
    plt.close(fig)
    return chemin.name
