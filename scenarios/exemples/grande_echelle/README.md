# Scénario 4 : grande échelle (centrale de 100 MW, Shi 2024)

**La question.** La même bibliothèque de composants décrit-elle une centrale de 100 MW / 600 MWh, et qu'est-ce qui change avec la taille ?

**Le fichier.** `scenarios/validation/shi_100MW.yaml` (phase 8) : quatre compresseurs isentropiques à 200 °C de sortie, refroidisseurs et réchauffeurs à eau sous pression (18 bar, pincement 10 K), réservoir isochore **adiabatique** de 118 000 m³ entre 4 et 10 MPa, trois turbines dont la première en **pression glissante**. Ce cas vient d'une prépublication non révisée (SSRN 5042640) et n'a aucune mesure : c'est un cas test de changement d'échelle, pas une validation. Son ambiance (25 °C, 1 bar) est celle du tableau 4 de Shi ; l'humidité est l'hypothèse commune du projet.

**Régénérer.**

```
python rapports/scenarios_grande_echelle.py         # → rapports/scenarios/grande_echelle.md (≈ 1 min)
python validation/tableau_de_bord.py                # la comparaison chiffre par chiffre avec Shi (phase 8)
```

**Comment lire la réponse.** Le rapport met côte à côte la centrale de Shi et le module de Dormoy avec gravier (`scenarios/D.yaml`) : électricité par mètre cube de réservoir et par tonne d'air, rendement, durées, température du réservoir. Les différences viennent de quatre choix de modèle que le fichier YAML rend visibles : paroi contre adiabatique (F12 contre F38), détendeur contre pression glissante (F15 contre F39), gravier contre eau sous pression (F25 contre F40), 19 MPa contre 10 MPa (air humide dans ou hors de sa formulation, F42). Le tableau de bord de la phase 8 donne l'écart avec les chiffres publiés de Shi (rendement 65,0 % contre 67,64 %).
