# -*- coding: utf-8 -*-
"""Masse des réservoirs d'air à paroi mince (formules.md#F44) et masse
des stockages de chaleur.

Pour une enveloppe cylindrique à fonds hémisphériques, la contrainte
circonférentielle σ = p·r/t fixe l'épaisseur ; la masse de paroi est

    m = S · p / (σ_adm / ρ) · (2 V_cyl + 1,5 V_fonds)

avec S le coefficient de sécurité, p la pression de conception
(relative), σ_adm / ρ la résistance spécifique de la paroi (J/kg) et
V_cyl, V_fonds les volumes de la partie cylindrique et des deux fonds.
La résistance spécifique « équivalente » de la paroi composite des
bouteilles de Dormoy est calibrée sur leur masse (registre
``reservoir.resistance_specifique_equivalente``) ; celle d'une paroi
tout aluminium 6061-T6 vaut σ_y / ρ (``reservoir.alu.limite_elastique``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from caes.registre import Registre
from caes.scenario import PREFIXE_REGISTRE

if TYPE_CHECKING:
    from caes.assembleur import Installation


@dataclass(frozen=True)
class MasseReservoir:
    masse_kg: float
    volume_cylindre_m3: float
    volume_fonds_m3: float
    epaisseur_equivalente_m: float
    """Épaisseur de paroi pour la masse volumique de référence donnée
    (information ; ∞ si la masse volumique est inconnue)."""


def masse_reservoir_paroi_mince(
    p_conception_pa: float, volume_m3: float, diametre_m: float,
    resistance_specifique_j_kg: float, coefficient_securite: float,
    masse_volumique_kg_m3: float | None = None,
) -> MasseReservoir:
    """Masse d'une enveloppe cylindrique à fonds hémisphériques (#F44).

    ``p_conception_pa`` est la pression **relative** (différence avec
    l'extérieur). Si le volume est plus petit que la sphère de ce
    diamètre, l'enveloppe est une sphère de ce volume (épaisseur
    p·r / 2σ, masse 1,5 · S · p · V / (σ/ρ)).
    """
    if volume_m3 <= 0 or diametre_m <= 0:
        raise ValueError("volume et diamètre doivent être positifs")
    if resistance_specifique_j_kg <= 0 or coefficient_securite <= 0:
        raise ValueError("résistance spécifique et coefficient de "
                         "sécurité doivent être positifs")
    p = max(p_conception_pa, 0.0)
    r = diametre_m / 2.0
    v_fonds = 4.0 / 3.0 * math.pi * r**3
    k = coefficient_securite * p / resistance_specifique_j_kg
    if volume_m3 <= v_fonds:
        v_cyl, v_fonds = 0.0, volume_m3
        r = (3.0 * volume_m3 / (4.0 * math.pi)) ** (1.0 / 3.0)
        masse = k * 1.5 * v_fonds
        ep = coefficient_securite * p * r / (2.0 * resistance_specifique_j_kg)
    else:
        v_cyl = volume_m3 - v_fonds
        masse = k * (2.0 * v_cyl + 1.5 * v_fonds)
        ep = coefficient_securite * p * r / resistance_specifique_j_kg
    if masse_volumique_kg_m3:
        # t = S·p·r/σ avec σ = (σ/ρ)·ρ
        ep /= masse_volumique_kg_m3
    else:
        ep = float("inf")
    return MasseReservoir(masse, v_cyl, v_fonds, ep)


def _resoudre(valeur: Any, reg: Registre) -> float:
    if isinstance(valeur, str) and valeur.startswith(PREFIXE_REGISTRE):
        return reg.si(valeur[len(PREFIXE_REGISTRE):])
    if isinstance(valeur, dict) and "valeur" in valeur:
        from caes.analyse.parametres import vers_si

        return vers_si(float(valeur["valeur"]), str(valeur.get("unite",
                                                               "-")))
    return float(valeur)


@dataclass(frozen=True)
class ParametresMasse:
    """Bloc ``masse`` du fichier d'analyse, résolu."""

    chemin_pression: str
    diametre_m: float
    resistance_specifique_j_kg: float
    coefficient_securite: float
    masse_volumique_kg_m3: float | None

    @classmethod
    def depuis_bloc(cls, bloc: dict[str, Any],
                    reg: Registre) -> ParametresMasse | None:
        if not bloc:
            return None
        manquantes = [k for k in ("pression", "diametre",
                                  "resistance_specifique",
                                  "coefficient_securite") if k not in bloc]
        if manquantes:
            raise ValueError(f"bloc « masse » : clés manquantes "
                             f"{manquantes}")
        rho = bloc.get("masse_volumique")
        return cls(
            chemin_pression=str(bloc["pression"]),
            diametre_m=_resoudre(bloc["diametre"], reg),
            resistance_specifique_j_kg=_resoudre(
                bloc["resistance_specifique"], reg),
            coefficient_securite=_resoudre(bloc["coefficient_securite"],
                                           reg),
            masse_volumique_kg_m3=_resoudre(rho, reg) if rho else None,
        )


def masses_installation(inst: Installation, p_conception_abs_pa: float,
                        pm: ParametresMasse) -> dict[str, float]:
    """Masses des réservoirs d'air (F44) et des stockages de chaleur
    (gravier : volume × (1 − ε) × ρ ; liquides : masse déclarée)."""
    from caes.composants import ReservoirAir, StockageChaleur

    p_rel = p_conception_abs_pa - inst.ambiance.p_amb_pa
    m_res = 0.0
    v_res = 0.0
    for c in inst.composants.values():
        if isinstance(c, ReservoirAir):
            m = masse_reservoir_paroi_mince(
                p_rel, c.volume_m3, pm.diametre_m,
                pm.resistance_specifique_j_kg, pm.coefficient_securite,
                pm.masse_volumique_kg_m3)
            m_res += m.masse_kg
            v_res += c.volume_m3
    m_cuves = 0.0
    v_cuves = 0.0
    for c in inst.composants.values():
        if not isinstance(c, StockageChaleur) or not c.physique:
            continue
        if c.modele == "gravier":
            mat = c.materiau
            m_cuves += (c.volume_m3 * (1.0 - mat.porosite)
                        * mat.masse_volumique_kg_m3)
            v_cuves += c.volume_m3
        else:
            m_cuves += float(getattr(c, "masse_kg", 0.0) or 0.0)
    return {
        "masse_reservoirs_kg": m_res,
        "masse_cuves_kg": m_cuves,
        "masse_totale_kg": m_res + m_cuves,
        "volume_reservoirs_m3": v_res,
        "volume_cuves_m3": v_cuves,
    }
