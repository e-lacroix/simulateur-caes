# Guide de démarrage : installer, simuler, lire les résultats

*Objectif : reproduire un scénario d'exemple en moins d'une heure, sans aide. Si une étape ne marche pas comme décrit, c'est un défaut du guide : le noter dans `JOURNAL.md`.*

## 1. Installer (10 minutes)

Prérequis : Python 3.11 ou plus récent, git, environ 1 Go de disque (CoolProp et matplotlib compris).

```text
git clone https://github.com/e-lacroix/simulateur-caes.git
cd simulateur-caes
python -m venv .venv
.venv\Scripts\activate            (Windows)   |   source .venv/bin/activate   (Linux, macOS)
pip install -e ".[dev]"
```

Dépendances installées automatiquement : CoolProp (propriétés de l'air réel et de l'air humide), numpy, scipy, pandas, matplotlib, pyyaml, pytest. Aucune compilation.

Vérifier l'installation (30 secondes) :

```text
python -m caes verifier scenarios/D.yaml
```

La commande affiche l'ambiance, les composants, les deux chaînes (charge, décharge) et « assemblage valide ». Sur Windows, si des caractères accentués s'affichent mal, mettre `PYTHONIOENCODING=utf-8` dans l'environnement.

Les commandes ci-dessous supposent l'environnement activé ; sinon remplacer `python` par `.venv\Scripts\python` (Windows) ou `.venv/bin/python`.

## 2. Première simulation (5 minutes)

```text
python -m caes simuler scenarios/D.yaml --sortie resultats/D
```

Architecture D : le banc de Dormoy (compresseur 45 kW à 4 étages, 20 bouteilles, 190 bar, turbine DEPRAG à 3 étages) avec trois cuves de gravier qui récupèrent la chaleur de compression. Mode « cycles » : charge, attente d'une heure, décharge, répétés jusqu'au régime stable (environ 1 minute 30).

Ce que contient `resultats/D/` :

| Fichier | Contenu |
|---|---|
| `resume.md` | l'installation, les résultats du dernier cycle, les **deux rendements** (sans et avec chaleur externe), les bilans de masse et d'énergie, l'eau et le givre, les **avertissements de domaine de validité** |
| `charge.csv`, `decharge.csv` | séries temporelles en unités SI (Pa, K, kg/s, W) |
| `tableau_1000.md`, `cascade_*.png` | le bilan d'exergie « 1000 unités » et sa cascade (phase 3) |
| `provenance.md` | chaque paramètre avec sa source (identifiant du registre, DOI) |
| `*.png` | pressions, températures, puissances |

Lire d'abord `resume.md`. Un rendement sans son contexte ne dit rien : regarder dans le même tableau la température de l'air rejeté, la chaleur externe, les avertissements (« cuve trop froide pour la cible », « givre », « Reynolds hors de Wakao »).

## 3. Changer une chose sans toucher au fichier (5 minutes)

```text
python -m caes simuler scenarios/D.yaml --modifier ambiance.T_amb=-20degC --sortie resultats/D_hiver
python -m caes simuler scenarios/D.yaml --modifier composants.cuve_1.volume=0.5m3 --modifier charge.p_cible=150bar
```

`--modifier chemin=valeur[unite]` remplace une feuille du YAML avant l'assemblage ; les unités acceptées sont celles de la table `UNITES` de `caes/registre.py` (bar, degC, m3, kWh, j, h, min, %, …). Le bloc `ambiance` est la seule source de conditions extérieures : changer `T_amb` change l'air aspiré, les refroidisseurs, les pertes des cuves et du réservoir, le point de rosée et l'état mort de l'exergie.

## 4. Reproduire un scénario d'exemple (20 minutes)

Les scénarios d'exemple sont des questions complètes : `scenarios/exemples/README.md` les liste. Chacun a un README (question, fichiers, hypothèses, lecture) et un script qui régénère sa page de résultats :

```text
python rapports/scenarios_transport.py --procs 4        # ≈ 3 min → rapports/scenarios/transport.md
python rapports/scenarios_centre_urgence.py             # ≈ 1 min → rapports/scenarios/centre_urgence.md
```

Comparer la page régénérée à celle du dépôt : les chiffres doivent être identiques (les simulations sont déterministes ; seule la durée change).

## 5. Comprendre d'où viennent les chiffres

- **Le registre** `data/registre/parametres.csv` : chaque nombre avec sa source, son unité, ses conditions et son niveau de preuve (`mesure`, `fabricant`, `calibration`, `simulation_publiee`, `calcul_personnel`, `hypothese`). `data/registre/references.csv` : les sources, avec DOI vérifié ou PDF déposé dans `data/sources/`. Le registre se régénère par `python -I data/registre/generer_registre_phase0.py` (le script est la seule source ; ne pas éditer les CSV).
- **Les formules** `docs/formules.md` : une fiche par équation (F01 à F47), avec un « en bref » vulgarisé, les hypothèses, le domaine de validité et un exemple à la main ; le code renvoie à la fiche (`# voir formules.md#F12`).
- **Les composants** `docs/composants/` : une page par type (compresseur, refroidisseur, sécheur, réservoir, détente, turbine, stockage de chaleur, attente) avec ses modèles, leurs paramètres et quand utiliser lequel.
- **La validation** `rapports/validation/tableau_de_bord.md` : chaque grandeur comparée à un chiffre publié (Dormoy mesuré, Tola, Shi), avec le verdict ; régénéré par `python validation/tableau_de_bord.py`.
- **L'état du projet** `JOURNAL.md` : ce qui est fait, les écarts connus (le cas de base de Dormoy à −15 %, non expliqué), les questions ouvertes.

## 6. Aller plus loin

| Besoin | Où |
|---|---|
| Écrire son propre scénario | `scenarios/README.md` (format), puis copier l'exemple le plus proche |
| Faire varier dix paramètres, Sobol, incertitudes, Pareto | `scenarios/analyse/README.md`, `python -m caes analyser` |
| Ajouter un modèle ou un composant | `docs/ajouter-un-composant.md` |
| Ajouter une étude ou un jeu de données de validation | `docs/ajouter-une-etude.md` |
| Référence de l'API Python | `docs/api.md` (`from caes.assembleur import charger_installation`) |
| Tout régénérer, vérifier les chiffres cités, lancer les tests | `python generer_tout.py --liste` |
| Les limites des études publiées et ce que le simulateur en couvre | `docs/limites-couvertes.md` |

## En Python, directement

```python
from caes.assembleur import charger_installation

inst = charger_installation("scenarios/D.yaml",
                            modifications=["ambiance.T_amb=-20degC"])
res = inst.simuler()
print(res.resume())
print(res.rendements())            # les deux définitions du rendement
c = res.dernier_cycle
c.decharge.series[["t_s", "p_res_pa", "P_el_w"]].head()
for a in res.avertissements:
    print(a)
```
