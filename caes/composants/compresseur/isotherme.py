"""Compression isotherme : la borne inférieure du travail (formules.md#F36).

Équation 8 de Baniamerian et al. (2025) : W = p·Q·ln(r), soit, par kg
d'air, w = p_in·v_in·ln(β). Aucun compresseur réel ne fait mieux : la
chaleur de compression est évacuée au fur et à mesure et la
température ne monte pas. C'est le cas limite n = 1 de la loi
polytropique (formules.md#F05), déjà implémenté dans
:func:`caes.compresseur.comprimer_etage`.
"""

from __future__ import annotations

from caes.compresseur import ResultatEtage, comprimer_etage
from caes.proprietes import Air

INDICE_ISOTHERME = 1.0


def comprimer_isotherme(
    air: Air, p_in_pa: float, T_in_K: float, beta: float,
) -> ResultatEtage:
    """Compression isotherme réversible : T_out = T_in, w = p·v·ln β."""
    return comprimer_etage(air, p_in_pa, T_in_K, beta, INDICE_ISOTHERME)
