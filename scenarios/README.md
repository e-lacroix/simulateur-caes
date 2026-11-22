# Scénarios : décrire une installation dans un fichier YAML

Un scénario est un fichier YAML qui décrit **une installation** (ses composants et l'ordre dans lequel l'air les traverse), **les conditions extérieures** et **ce qu'on simule** (une charge, une décharge ou des cycles). Il se lance sans écrire de code :

```text
.venv\Scripts\python -m caes simuler scenarios/D.yaml --sortie resultats/D
.venv\Scripts\python -m caes simuler scenarios/D.yaml --modifier ambiance.T_amb=-20degC
.venv\Scripts\python -m caes verifier scenarios/D.yaml
```

Le dossier de résultats contient `resume.md` (installation, résultats, rendements, bilans, avertissements), les séries temporelles en CSV, le tableau « 1000 unités » et sa cascade, des graphiques et `provenance.md` (chaque paramètre et sa source, avec les DOI des références citées).

## Les fichiers d'exemple

| Fichier | Mode | Ce qu'il montre |
|---|---|---|
| `dormoy_charge_1_190.yaml` | charge | Essai de charge mesuré de Dormoy (1 → 190 bar), hypothèses minimales |
| `dormoy_charge_1_190_aspiration_chaude.yaml` | charge | Même essai avec l'air aspiré à 52 °C (scénario retenu en phase 1) |
| `dormoy_charge_55_190.yaml` | charge | Recharge 55 → 190 bar (bilan de chaleur du tableau 6) |
| `dormoy_decharge_essai.yaml` | décharge | Essai de décharge mesuré (190 → 50 bar, sans turbine, débit imposé) |
| `dormoy_decharge_base.yaml` | décharge | Cas de base simulé par Dormoy : un étage, sans réchauffage |
| `dormoy_decharge_3etages.yaml` | décharge | Trois étages réchauffés par une source externe |
| `A.yaml` à `E.yaml` | cycles | Les cinq architectures de la phase 5 (base, chaleur externe, huile idéale, gravier direct, gravier + boucle d'air) |
| `D_hiver.yaml` | cycles | `D.yaml` par −20 °C : seule l'ambiance change |
| `variantes/*.yaml` | charge, décharge, cycles | Un scénario par modèle de la phase 7, dérivé de Dormoy (compresseur isentropique, polytropique, isotherme ; refroidisseur à pincement et à perte de charge ; sans sécheur ; réservoir adiabatique ; turbine isentropique et polytropique ; pression glissante avec et sans Flügel ; huile à deux réservoirs ; eau sous pression ; isolant de laine minérale sur 14 jours ; attente sans pertes). Générés par `variantes/generer_variantes.py` : ne pas les éditer à la main. Comparés dans `rapports/phase7/variantes.md` |

| `exemples/<nom>/` | cycles | Scénarios d'**exemple** (phase 11) : une question, ses fichiers, son README et son rapport régénérable (`rapports/scenarios_<nom>.py`) : banc de Dormoy avec gravier, transport (isolant, hiver / été par `ambiance.profil`, fuites, appoint), centre d'urgence (flotte de modules, F47), grande échelle ; voir `exemples/README.md` |
| `analyse/*.yaml` | – | Fichiers d'**analyse** (phase 10) : scénario de base, paramètres à faire varier avec leur plage, sorties, réglages de Sobol, des incertitudes et de NSGA-II ; `python -m caes analyser scenarios/analyse/D.yaml` ; format dans `analyse/README.md` |
| `humidite/*.yaml` | cycles | Architectures A et B avec trois traitements de l'eau (sécheur par adsorption, séparateurs seuls, séparateurs et sécheur d'appoint), générés par `humidite/generer_humidite.py` ; comparés dans `rapports/phase9/humidite.md` |
| `validation/*.yaml` | charge, décharge, cycles | Les cas des autres études, pour le tableau de bord (phase 8) : `shi_100MW.yaml` (cas test de 100 MW, eau sous pression, pression glissante), `tola_charge.yaml` et `tola_decharge_A/B/C.yaml` (10 MW, polytropique à rendement, répartition égale glissante) |

Les anciens fichiers (format des phases 1 à 5) sont conservés dans `v1/` pour les scripts de validation.

## Structure d'un fichier

```yaml
nom: D
description: une phrase.

ambiance:          # obligatoire : la seule source de conditions extérieures
  T_amb: ...
  p_amb: ...
  humidite_relative: ...
  T_aspiration: ...   # optionnel, défaut T_amb
  profil: meteo.csv   # optionnel : température extérieure dans le temps

composants:        # chaque brique : type, modele, paramètres
  compresseur: {type: compresseur, modele: polytropique_dormoy, ...}
  refroidisseur_1: {type: refroidisseur, modele: efficacite, ...}
  cuve_1: {type: stockage_chaleur, modele: gravier, ...}
  reservoir: {type: reservoir_air, modele: paroi, ...}
  detendeur: {type: detente, modele: isenthalpique, ...}
  turbine: {type: turbine, modele: polytropique_deprag, ...}
  attente: {type: attente, duree: ...}

charge:            # l'ordre dans lequel l'air traverse les briques
  chaine: [compresseur.1, cuve_1, refroidisseur_1, compresseur.2, ..., secheur, reservoir]
  p_cible: ...
  dt: ...
  reservoir_initial: {p: ..., T: ...}   # mode charge seulement

decharge:
  chaine: [reservoir, detendeur, cuve_3, turbine.1, cuve_2, turbine.2, cuve_1, turbine.3]
  dt: ...
  reservoir_initial: {p: ..., T: ..., T_paroi: ...}   # mode decharge seulement
  debit: ...                                           # s'il n'y a pas de turbine

simulation:
  mode: cycles        # charge | decharge | cycles
  attente: attente    # nom du composant d'attente (optionnel)
  p_initiale: ...     # pression de départ des cycles
  nombre_max: 6
  tolerance: 0.01
```

### Les valeurs

Chaque valeur physique est, au choix :

- `registre:<id>` : la valeur du registre scientifique (`data/registre/parametres.csv`), convertie en SI, avec sa source et son niveau de preuve ; `registre:<id>#min`, `#max` ou `#moyen` pour une plage ;
- `{valeur: 52, unite: degC, source: "pourquoi"}` : une valeur propre au scénario, convertie en SI (unités de la table `UNITES` de `caes/registre.py` : bar, degC, K, kWh, h, min, m3, L, W/m2K...), **avec sa justification** ;
- un nombre nu, seulement pour les grandeurs sans dimension ou de réglage (nombre de cellules, tolérance, booléens).

Le fichier `provenance.md` du dossier de résultats liste chaque feuille et sa source.

### Le bloc `ambiance`

| Clé | Rôle | Qui s'en sert |
|---|---|---|
| `T_amb` | Température extérieure | source froide des refroidisseurs, pertes du réservoir et des cuves, état mort de l'exergie, température initiale des cuves |
| `p_amb` | Pression atmosphérique | aspiration du compresseur, cuves à pression atmosphérique, état mort |
| `humidite_relative` | Humidité de l'air aspiré | teneur en eau de l'air aspiré (F42), suivie jusqu'au rejet : condensation dans les refroidisseurs et le réservoir, givre aux turbines (F43) |
| `T_aspiration` | Température de l'air aspiré par le compresseur (défaut `T_amb`) | débit massique aspiré, température d'entrée de l'étage 1 |
| `profil` | CSV optionnel (`t_s`/`t_h`/`t_j` et `T_amb_K`/`T_amb_degC`) | température extérieure interpolée dans le temps ; l'écart `T_aspiration − T_amb` est conservé |

Pour simuler l'hiver québécois, il suffit de changer `T_amb` (fichier `D_hiver.yaml`, ou `--modifier ambiance.T_amb=-20degC`).

### Les chaînes

- **Charge** : commence par `compresseur.1`, contient chaque étage du compresseur une fois dans l'ordre, finit par le réservoir. Entre deux étages : des stockages de chaleur (`stockage_chaleur`), des refroidisseurs, un sécheur, une perte de débit. `compresseur` seul = tous ses étages à la suite.
- **Décharge** : commence par le réservoir, puis (optionnel) le détendeur, puis les étages de turbine dans l'ordre, chacun précédé des réchauffeurs (`stockage_chaleur`) qui l'alimentent. La cible de chaque réchauffeur est la température nominale `T_entree_cible` de l'étage qui suit. Sans turbine, `decharge.debit` fixe le débit (essai « ventilation »).
- L'assembleur vérifie : ordre des étages, un seul réservoir (le même en charge et en décharge pour les cycles), consigne du détendeur égale à la pression d'entrée du premier étage, pressions décroissantes d'un étage de turbine au suivant (la petite chute entre deux étages est un laminage), cuves de gravier chargées avant d'être déchargées.

### Les composants

Un composant = un `type` (sa fonction) et un `modele` (la physique choisie). Les paramètres de chaque modèle, son domaine de validité et ses sources sont dans `docs/composants/<type>.md`.

| `type` | Modèles (phases 6 et 7) | Rôle |
|---|---|---|
| `compresseur` | `polytropique_dormoy`, `isentropique`, `polytropique_rendement`, `isotherme` | machine à N étages ; étages à rapport fixe, à température de sortie visée ou libres |
| `refroidisseur` | `efficacite`, `pincement` (+ `perte_de_charge`) | échangeur vers l'ambiant, source froide = ambiance |
| `secheur` | `perte_debit` (+ `point_de_rosee_sortie`), `separateur`, `aucun` | sécheur par adsorption, séparateur d'eau, ou rien |
| `perte_debit` | `fraction` | rendement volumétrique (convention de Dormoy) ou fuite |
| `reservoir_air` | `K_global`, `paroi`, `adiabatique` (+ `surpression_entree`) | réservoir équivalent, trois modèles thermiques |
| `stockage_chaleur` | `gravier`, `huile_deux_reservoirs`, `eau_sous_pression`, `huile_ideale`, `source_externe` (+ bloc `isolation`) | ce qui réchauffe l'air avant une turbine, et d'où vient la chaleur |
| `detente` | `isenthalpique`, `cheayb`, `isotherme`, `pression_glissante` | régulateur de pression, ou pas de régulateur |
| `turbine` | `polytropique_deprag`, `isentropique`, `polytropique_rendement`, `flugel` | machine à N étages ; point fixe, pression variable, ou loi de Flügel |
| `attente` | `pertes_statiques`, `sans_pertes` | temps entre charge et décharge |

Toute chaleur ajoutée à l'air porte l'étiquette de sa source : le nom du stockage (`cuve_3`, `huile`) ou `externe`. Le rendement est donné sous les deux définitions (sans et avec la chaleur externe) ; c'est toujours un résultat.

### Les avertissements

Chaque composant signale quand il sort de son domaine de validité (corrélation de Wakao hors plage, détendeur de Cheayb au-delà de 150 bar, air rejeté sous 0 °C, cuve trop froide pour atteindre la cible, lois en pression extrapolées...). Les avertissements apparaissent dans la console et dans `resume.md` ; ils n'arrêtent pas la simulation.

## Ajouter un scénario

1. Copier le fichier d'exemple le plus proche.
2. Changer les composants, les chaînes, l'ambiance ; chaque nouvelle valeur porte sa source.
3. `python -m caes verifier mon_scenario.yaml` : l'assembleur dit ce qui manque ou ce qui est incompatible.
4. `python -m caes simuler mon_scenario.yaml` ; lire `resume.md` et ses avertissements.
