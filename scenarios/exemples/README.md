# Scénarios d'exemple (phase 11) : comment poser une question au simulateur

Chaque dossier est une **question** posée au simulateur : les fichiers YAML qui la décrivent, un `README.md` qui explique la question, les hypothèses et comment lire la réponse, et un script de rapport qui régénère chaque chiffre en une commande. Les pages de résultats sont dans `rapports/scenarios/` et ne doivent pas être éditées à la main.

| Dossier | Question | Fichiers | Rapport |
|---|---|---|---|
| [`dormoy_gravier/`](dormoy_gravier/README.md) | Sur le banc de Dormoy, que reste-t-il du 16,8 % quand la chaleur vient du gravier, et par −20 °C ? | `scenarios/A.yaml` à `E.yaml`, `D_hiver.yaml` | `python rapports/scenarios_dormoy_gravier.py` → `rapports/scenarios/dormoy_gravier.md` |
| [`transport/`](transport/README.md) | Après 7 à 56 jours de transport, combien de chaleur et d'électricité reste-t-il ? Isolant, hiver et été, échelle, fuites, chaudière d'appoint | `transport.yaml`, `transport_appoint.yaml`, `meteo_hiver.csv`, `meteo_ete.csv` | `python rapports/scenarios_transport.py` → `rapports/scenarios/transport.md` |
| [`centre_urgence/`](centre_urgence/README.md) | Combien de modules pour tenir 100 kW pendant 72 h avec une demande jour / nuit, et comment se comparent-ils aux batteries et au diesel ? | `module.yaml`, `demande_72h.csv` | `python rapports/scenarios_centre_urgence.py` → `rapports/scenarios/centre_urgence.md` |
| [`grande_echelle/`](grande_echelle/README.md) | La même bibliothèque à 100 MW (Shi 2024) : qu'est-ce qui change avec la taille ? | `scenarios/validation/shi_100MW.yaml` | `python rapports/scenarios_grande_echelle.py` → `rapports/scenarios/grande_echelle.md` |

Le scénario 5 du plan (stockage fixe couplé au solaire, boucle heure par heure de Wang 2020) n'est pas fait : il demande un profil solaire sourcé et un pilotage heure par heure qui n'existe pas encore dans le simulateur (voir `JOURNAL.md`).

## La démarche, en quatre étapes

1. **Écrire la question** avec ses nombres (durée, puissance, climat) et dire d'où ils viennent : registre (`registre:<id>`) ou `{valeur, unite, source}`.
2. **Partir du scénario le plus proche** (`scenarios/README.md`), ne changer que ce que la question change ; `python -m caes verifier` avant de simuler. Les fichiers dérivés d'un autre sont générés par `generer_exemples.py`, jamais édités à la main.
3. **Balayer** avec `--modifier` (ou `caes.analyse.lot.simuler_lot` en parallèle) plutôt que de multiplier les fichiers.
4. **Lire la réponse avec ses réserves** : unités SI en interne, hypothèses marquées au registre, avertissements de domaine dans `resume.md`, intervalle d'incertitude quand il existe (phase 10). Un résultat négatif se présente comme tel.
