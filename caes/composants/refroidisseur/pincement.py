"""Refroidisseur à pincement (Tola 2022 : 20 K air/air, 10 K air/huile ;
Shi 2024 : 10 K), formules.md#F37.

L'échangeur est supposé assez grand pour que l'air ressorte à la
température de la source froide plus l'écart minimal δ :
T_out = max(T_in, T_froid + δ) si T_in > T_froid + δ, sinon T_in.
La chaleur retirée est q = h(p, T_in) − h(p, T_out) (enthalpie réelle),
et la part au-dessus du seuil est comptée comme pour le modèle à
efficacité (formules.md#F09).
"""

from __future__ import annotations

from caes.proprietes import Air
from caes.refroidisseur import ResultatRefroidisseur


def refroidir_pincement(
    air: Air, p_pa: float, T_in_K: float, T_froid_K: float,
    pincement_K: float, T_seuil_K: float,
) -> ResultatRefroidisseur:
    """Refroidissement isobare jusqu'à T_froid + δ (#F37)."""
    if pincement_K < 0:
        raise ValueError(f"pincement {pincement_K} < 0")
    T_out = max(min(T_in_K, T_froid_K + pincement_K), T_froid_K + pincement_K)
    T_out = min(T_out, T_in_K)
    h_in = air.h(p_pa, T_in_K)
    h_out = air.h(p_pa, T_out)
    q = h_in - h_out
    if T_in_K > T_seuil_K:
        q_sup = h_in - air.h(p_pa, max(T_out, T_seuil_K))
    else:
        q_sup = 0.0
    ecart = T_in_K - T_froid_K
    eff = (T_in_K - T_out) / ecart if ecart > 1e-9 else 0.0
    return ResultatRefroidisseur(
        p_pa=p_pa, T_in_K=T_in_K, T_out_K=T_out, efficacite=eff, q=q,
        q_sup_seuil=q_sup,
    )
