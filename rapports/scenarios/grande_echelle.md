# Scénario d'exemple : grande échelle (centrale de 100 MW)

*Généré par `rapports/scenarios_grande_echelle.py` à partir de `scenarios/validation/shi_100MW.yaml` (cas test de Shi 2024, prépublication non révisée) et de `scenarios/D.yaml` (module de Dormoy avec gravier). Mêmes composants, mêmes équations : seuls les modèles choisis et les nombres changent.*

**Question.** Que change la taille ? Un réservoir de 118 000 m³ contre 5.86 m³  100 MW contre 60 kW  quatre étages à 10 MPa contre 19 MPa  eau sous pression contre gravier  pression glissante contre détendeur.

## Les deux installations, dernier cycle

| Grandeur | Shi 2024 (100 MW) | Dormoy D (gravier) |
|---|---|---|
| Volume du réservoir d'air (m³) | 118 000 | 5.86 |
| Pression de travail (bar) | 100 | 190 |
| Masse d'air stockée par cycle (t) | 5331.65 | 0.76 |
| Durée de la charge (h) | 7.47 | 6.05 |
| Électricité consommée (MWh) | 838.921 | 0.239 |
| Durée de la décharge (h) | 5.63 | 0.66 |
| Électricité livrée (MWh) | 545.334 | 0.041 |
| Puissance électrique moyenne (MW) | 96.805 | 0.062 |
| Rendement aller-retour (%) | 65.0 | 17.1 |
| Électricité livrée par m³ de réservoir (kWh/m³) | 4.62 | 7.00 |
| Électricité livrée par tonne d'air (kWh/t) | 102.3 | 53.9 |
| Température finale du réservoir après charge (°C) | 76 | 40 |
| Air rejeté, minimum (°C) | 29 | 15 |

## Ce qui change avec la taille

- **La paroi ne compte plus.** Les 20 bouteilles de Dormoy (65 m² pour 5,86 m³) évacuent la chaleur de compression en quelques heures ; la caverne de Shi est modélisée adiabatique (F38) : l'air y reste chaud, la pression cible est atteinte avec moins de masse, et cette chaleur ressort à la décharge. Même composant `reservoir_air`, modèle `paroi` contre `adiabatique`.
- **Le détendeur disparaît.** Shi fait entrer la première turbine directement à la pression du réservoir (pression glissante, F39) ; Dormoy jette l'exergie de 190 à 40 bar dans un détendeur (phase 3 : 68 % de l'exergie stockée dans le cas de base). C'est la première raison de l'écart de rendement.
- **La chaleur est stockée dans l'eau sous pression** (18 bar, F40) et rendue par des échangeurs à pincement de 10 K ; le gravier de D est traversé directement par l'air. Les deux sont des stockages sensibles ; l'eau est limitée par son ébullition (plafond à 202 °C), le gravier par le front thermique.
- **La pression de travail est plus basse** (4 à 10 MPa) : l'air humide reste dans le domaine de sa formulation (F42), le travail de compression par kilogramme est plus petit, mais il faut 20 000 fois plus de volume.
- **Ce que le tableau de bord dit de ce cas** (phase 8) : compresseurs 1 à 3 à 0,1 %, turbines à 3 %, rendement 65,0 % contre 67,64 % publié ; durées et masse à −6 à −9 % (réservoir adiabatique, quatrième refroidisseur) ; ce n'est pas une validation, aucune mesure n'existe pour cette centrale.

*2 simulations, 73 s.*
