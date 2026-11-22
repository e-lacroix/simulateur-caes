# Ajouter un modèle ou un composant

*Un composant n'entre dans la bibliothèque que complet : fiche de formule, paramètres au registre, tests de bilan et de cas limite, avertissement hors domaine, page de documentation, ligne de validation quand des données existent. Ce guide donne l'interface, la liste de contrôle et un exemple pas à pas (le séparateur d'eau de la phase 9, qui est dans le dépôt).*

## 1. L'interface (`caes/composants/base.py`, fiche F33)

| Objet | Rôle |
|---|---|
| `EtatAir` | l'air à un point de la chaîne : `p_abs_pa`, `T_K`, `m_dot_kg_s`, eau en vapeur et en liquide par kg d'air (`w_vapeur_kg_kg`, `w_liquide_kg_kg`) ; immuable, `remplacer(...)` rend une copie |
| `Contexte` | ce qu'un pas de temps sait du monde : propriétés de l'air (`air`), `ambiance`, instant `t_s`, pas `dt_s`, pression de refoulement de la chaîne |
| `Flux` | ce qu'un composant a fait pendant le pas : travail (`W_pol_w`), chaleur ajoutée avec sa source (`Q_ajoute_w`, `source`), chaleur retirée, débit perdu, perte de charge, eau condensée ou séparée, chaleur latente, givre |
| `Composant` | classe de base : `TYPE`, `MODELES`, `param(nom)` / `nombre(nom, defaut)` pour lire les paramètres (déjà en SI), `avertir(message)` (dédoublonné, compté), `verifier_validite()` (statique), `description()` |
| `FABRIQUES` | dictionnaire `type → classe`, dans `caes/composants/__init__.py` ; l'assembleur s'en sert pour construire ce que le YAML déclare |

Méthodes par fonction : `pas(etat, ctx)` pour ce qui transforme l'air (refroidisseur, sécheur, détente, étage de compresseur ou de turbine) ; `charger_air` et `rechauffer` pour un stockage de chaleur ; `remplir`, `vider`, `attendre` pour le réservoir ; `executer` pour l'attente. Après toute transformation, appeler `mettre_a_l_equilibre(etat, flux, self)` (F43) pour remettre l'eau à l'équilibre.

Trois règles non négociables : unités SI à l'intérieur ; aucun chiffre en dur (tout vient des paramètres, donc du scénario ou du registre) ; la seule source de température et de pression extérieures est `ctx.ambiance`.

## 2. Liste de contrôle

1. **Fiche** dans `docs/formules.md` (format en bas du fichier : en bref, formule, niveau, origine, hypothèses et validité, pourquoi celle-ci, exemple à la main, source) ; ajouter la ligne à l'index ; le code renvoie à la fiche par `# voir formules.md#Fnn`.
2. **Registre** : chaque paramètre nouveau dans `data/registre/generer_registre_phase0.py` avec sa référence (DOI vérifié ou PDF déposé dans `data/sources/`), son unité, ses conditions, son niveau de preuve ; régénérer (`python -I data/registre/generer_registre_phase0.py`). Une hypothèse est permise si elle est marquée `hypothese` et expliquée dans `notes`.
3. **Physique** dans `caes/composants/<type>/<modele>.py` (fonctions pures, testables seules) ; branchement dans la classe du type (`MODELES`, branche dans `pas` ou équivalent), ou nouvelle classe héritant de `Composant` inscrite dans `FABRIQUES`.
4. **Avertissement hors domaine** : `self.avertir("texte fixe sans nombre variable")` quand une corrélation sort de sa plage ou qu'une hypothèse est forcée ; une sortie du domaine où le modèle n'a plus de sens lève `HorsDomaine` (la simulation s'arrête proprement et le dit).
5. **Tests** (`tests/test_modeles_phase7.py` et `tests/test_humidite.py` comme modèles) : conservation de la masse et de l'énergie, cas limite (rendement 1, pression égale, réservoir vide, débit nul), avertissement attendu, et une ligne dans `tests/test_combinaisons.py` (toutes les combinaisons du noyau doivent fermer leurs bilans à 1 %). `tests/test_non_regression.py` doit rester vert.
6. **Scénario d'exemple** : un bloc dans `scenarios/variantes/generer_variantes.py` (`BLOCS`), régénérer ; `python -m caes verifier` sur le résultat.
7. **Page** `docs/composants/<type>.md` : ligne dans le tableau des modèles (physique, paramètres, source, quand l'utiliser), domaine de validité.
8. **Validation** : si une donnée publiée existe, une ligne dans `validation/tableau_de_bord.py` (jeu de données dans `data/validation/<source>/` avec `provenance.md`) ; tout écart > 5 % a son paragraphe d'explication ou la mention « non expliqué ».
9. **Journal** : entrée dans `JOURNAL.md` (ce qui est fait, choix, limites).

## 3. Exemple pas à pas : le séparateur d'eau (phase 9)

**La question.** Après un refroidisseur, l'air porte des gouttes d'eau. Un séparateur les retient (une fraction `efficacite_separation`), sans perdre d'air ni changer p et T. Il faut pouvoir le mettre entre un refroidisseur et le compresseur suivant.

**Fiche.** F43 décrit l'équilibre vapeur / liquide et le séparateur : « retient une fraction η_sép de l'eau liquide ; la vapeur n'est pas touchée ». Niveau : paramètre au niveau hypothèse (0,98, aucune donnée dans les études lues).

**Registre.** Dans `generer_registre_phase0.py` :

```python
p("separateur.efficacite", "Fraction de l'eau liquide retenue par un séparateur",
  0.98, "-", D, "non publié", "hypothese", "",
  "Hypothèse du projet (ordre de grandeur des séparateurs industriels).")
```

**Code.** Le séparateur est un modèle du type `secheur` (`caes/composants/secheur/__init__.py`), parce qu'il occupe la même place dans une chaîne :

```python
class Secheur(Composant):
    TYPE = "secheur"
    MODELES = ("perte_debit", "aucun", "separateur")

    def __init__(self, nom, parametres, provenance=None):
        super().__init__(nom, parametres, provenance)
        if self.modele == "separateur":
            self.efficacite_separation = self.nombre("efficacite_separation")
            if not 0.0 <= self.efficacite_separation <= 1.0:
                raise ErreurComposant(f"{nom} : efficacite_separation hors de [0, 1]")

    def pas(self, etat, ctx):
        m = etat.m_dot_kg_s
        if self.modele == "separateur":                       # formules.md#F43
            retiree = etat.w_liquide_kg_kg * self.efficacite_separation
            flux = Flux(eau_separee_kg_s=retiree * m)
            return etat.remplacer(w_liquide_kg_kg=etat.w_liquide_kg_kg - retiree), flux
        ...
```

Le paramètre arrive déjà en SI (ici sans dimension) : le YAML dit `efficacite_separation: registre:separateur.efficacite`.

**Test** (`tests/test_humidite.py`) : un refroidisseur condense, le séparateur retire 98 % du liquide, le débit d'air est inchangé, l'eau séparée du flux vaut 0,98 × liquide × débit (conservation de l'eau).

**Scénario.** `scenarios/humidite/generer_humidite.py` insère `separateur_i` après chaque `refroidisseur_i` dans la chaîne de charge ; `python -m caes verifier scenarios/humidite/B_separateur.yaml` affiche la chaîne.

**Page.** `docs/composants/secheur.md` : ligne `separateur` (physique, paramètre, source « – », « après chaque refroidisseur ; seul, il ne retire pas la vapeur »).

**Validation.** Aucune donnée publiée sur un séparateur dans les études lues : pas de ligne au tableau de bord ; c'est écrit dans la page et le journal. Le rapport de la phase 9 (`rapports/phase9/humidite.md`) montre ce que le séparateur change.

## 4. Pièges fréquents

- Lire un paramètre avec une valeur par défaut chiffrée (`self.nombre("x", 0.9)`) est un chiffre en dur : la valeur par défaut doit être neutre (0, `None`) ou venir du registre.
- Un avertissement avec un nombre qui varie (`f"Re = {Re:.0f}"`) ne se dédoublonne pas et remplit `resume.md` : texte fixe, le nombre va dans une série.
- Ajouter de la chaleur à l'air sans étiquette de source casse le bilan de chaleur (règle du projet) : `Flux(Q_ajoute_w=..., source="externe")` ou le nom du stockage.
- Oublier `mettre_a_l_equilibre` après une transformation : l'eau n'est plus suivie, les bilans d'eau de la phase 9 se faussent.
- Un modèle « qui marche » sur Dormoy mais qui n'a pas de test de cas limite se cassera dans `test_combinaisons` (90 combinaisons) : écrire le cas limite d'abord.
