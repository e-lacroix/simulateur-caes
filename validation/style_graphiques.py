# -*- coding: utf-8 -*-
"""Compatibilité : le style des graphiques vit dans ``caes.graphiques``
depuis la phase 6. Ce module réexporte ses noms pour les scripts de
validation écrits avant."""

from caes.graphiques import (  # noqa: F401
    COULEURS,
    ENCRE,
    ENCRE_2,
    GRILLE,
    SURFACE,
    etiquette_fin,
    nouvelle_figure,
    plt,
    point_reference,
    style_axes,
    terminer,
)
