# Catalogue des formules du simulateur

*Chaque équation utilisée dans le code a sa fiche ici, et le code y renvoie (par exemple `# voir formules.md#F04`). Les fiches sont ajoutées au fil des phases. Modèle de fiche en bas de page. Les « éq. n » renvoient à la numérotation de Dormoy et al. (2024).*

## Index

| Id | Nom | Module | Phase |
|---|---|---|---|
| F01 | Conversion d'unités vers le SI | `caes/registre.py` | 0 |
| F02 | Air réel : équation d'état de Lemmon (CoolProp) | `caes/proprietes.py` | 1 |
| F03 | Gaz parfait à chaleurs massiques constantes | `caes/proprietes.py` | 1 |
| F04 | Compression polytropique : p·vⁿ = constante (éq. 1–3) | `caes/compresseur.py` | 1 |
| F05 | Travail polytropique massique (éq. 4) | `caes/compresseur.py` | 1 |
| F06 | Débit massique aspiré = masse volumique × cylindrée × vitesse | `caes/compresseur.py` | 1 |
| F07 | Lois « varie avec la pression » (interpolation linéaire bornée) | `caes/compresseur.py`, `caes/refroidisseur.py` | 1 |
| F08 | Puissance électrique du compresseur (éq. 5) | `caes/compresseur.py` | 1 |
| F09 | Refroidisseur : méthode de l'efficacité, NTU (éq. 6–9) | `caes/refroidisseur.py` | 1 |
| F10 | Sécheur : perte de débit (éq. 10) | `caes/secheur.py` | 1 |
| F11 | Réservoir équivalent (éq. 11–12) | `caes/reservoir.py` | 1 |
| F12 | Bilan de masse et d'énergie du réservoir (éq. 13–14, 21) | `caes/reservoir.py` | 1 |
| F13 | Bilan d'énergie de la charge complète | `caes/systeme.py` | 1 |
| F14 | RMSE et MAPE (éq. 18–19) | `caes/metriques.py` | 1 |
| F15 | Détendeur isenthalpique (laminage) | `caes/detendeur.py` | 2 |
| F16 | Détendeur, relation de Cheayb et al. (éq. 15) | `caes/detendeur.py` | 2 |
| F17 | Détente polytropique d'un étage de turbine (éq. 16) | `caes/turbine.py` | 2 |
| F18 | Puissance électrique de la turbine (éq. 17) | `caes/turbine.py` | 2 |
| F19 | Réchauffage avant un étage : chaleur suivie par source | `caes/turbine.py` | 2 |
| F20 | Rendement aller-retour, deux définitions (éq. 20) | `caes/systeme.py` | 2 |
| F21 | Exergie d'un écoulement d'air | `caes/exergie.py` | 3 |
| F22 | Exergie d'un réservoir (et éq. 22 de Baniamerian) | `caes/exergie.py` | 3 |
| F23 | Exergie d'une chaleur (facteur de Carnot) | `caes/exergie.py` | 3 |
| F24 | Exergie détruite = T0 × entropie créée | `caes/exergie.py` | 3 |
| F25 | Lit de gravier : équations de Schumann et solution exacte | `caes/lit_gravier.py` | 4 |
| F26 | Schéma numérique cellule par cellule (NTU et relaxation exacte) | `caes/lit_gravier.py` | 4 |
| F27 | Coefficient d'échange air-cailloux : Wakao et Jeffreson | `caes/lit_gravier.py` | 4 |
| F28 | Perte de charge d'Ergun | `caes/lit_gravier.py` | 4 |
| F29 | Conduction axiale et pertes latérales du lit | `caes/lit_gravier.py` | 4 |
| F30 | Couplage des cuves au banc : charge, bypass, pincement | `caes/integre.py` | 5 |
| F31 | Exergie d'un lit de gravier | `caes/integre.py` | 5 |

---

## F01 : conversion d'unités vers le SI

**En bref.** Les articles donnent les pressions en bar, les températures en °C et les énergies en kWh, parce que c'est pratique à lire. Mais les lois physiques ne marchent proprement qu'avec les unités de base (pascal, kelvin, joule). Le simulateur convertit donc tout à l'entrée, une seule fois, comme on convertit des dollars canadiens en dollars américains avant de comparer deux prix.

**Formule.** valeur_SI = valeur × facteur + décalage, avec :

| Unité source | Unité SI | Facteur | Décalage |
|---|---|---|---|
| bar | Pa | 10⁵ | 0 |
| °C | K | 1 | 273,15 |
| kWh | J | 3,6 × 10⁶ | 0 |
| h ; min | s | 3600 ; 60 | 0 |
| m³/h | m³/s | 1/3600 | 0 |
| tr/min | tr/s | 1/60 | 0 |
| % | – | 0,01 | 0 |

**Niveau.** Définition (conventions du Système international).

**D'où elle vient.** Définitions du bar (10⁵ Pa exactement), du kelvin (0 °C = 273,15 K exactement) et du kilowattheure (1 kW pendant 3600 s).

**Hypothèses et validité.** Aucune. Attention à une seule chose : une *différence* de températures (par exemple un RMSE de 2,83 °C) ne reçoit pas le décalage de 273,15. Le registre le signale dans la colonne `notes` pour les paramètres concernés.

**Pourquoi.** L'autre option serait de garder les unités des articles et de convertir dans chaque formule. C'est la source d'erreur la plus classique en calcul scientifique (la sonde Mars Climate Orbiter a été perdue en 1999 pour une confusion livres-force / newtons).

**Exemple à la main.** 190 bar → 190 × 10⁵ = 1,9 × 10⁷ Pa. 55 °C → 55 + 273,15 = 328,15 K. 396 kWh → 396 × 3,6 × 10⁶ = 1,4256 × 10⁹ J.

**Source.** Convention du projet ; table `UNITES` dans `caes/registre.py`.

---

## F02 : air réel, équation d'état de Lemmon (CoolProp)

**En bref.** À 190 bar, l'air est tellement comprimé que ses molécules se gênent : il se comporte un peu autrement qu'un gaz « idéal ». Pour savoir exactement combien de kilos d'air tiennent dans un réservoir, ou à quelle température il sort d'un compresseur, on utilise une équation très précise ajustée sur des milliers de mesures. C'est comme utiliser une vraie carte routière plutôt qu'un plan schématique : sur un court trajet les deux se valent, sur un long trajet seule la carte est fiable.

**Formule.** L'équation de Lemmon et al. (2000) exprime l'énergie libre de Helmholtz réduite α(τ, δ) de l'air (mélange N₂, O₂, Ar) en fonction de la température réduite τ et de la masse volumique réduite δ ; toutes les propriétés (p, h, u, s, cp, cv) en découlent par dérivation. On ne la recopie pas : elle est implémentée dans CoolProp (fluide `Air`). Le simulateur l'appelle par des fonctions de la forme ρ(p, T), T(p, ρ), h(p, T), u(ρ, T), p(ρ, T), T(p, h).

**Niveau.** Modèle physique classique (équation d'état empirique de référence).

**D'où elle vient.** Ajustement multiparamétrique sur les mesures expérimentales de l'air (p, ρ, T, vitesse du son, capacités calorifiques) de 60 à 2000 K et jusqu'à 2000 MPa.

**Hypothèses et validité.** Air **sec**, composition standard. Valide de 60 à 2000 K et jusqu'à 2000 MPa ; le simulateur reste entre 250 et 600 K et sous 35 MPa, très loin des bornes. Incertitude typique sur ρ : 0,1 %.

**Pourquoi.** Dormoy l'utilise ; c'est aussi ce qui permet au simulateur de ne pas avoir d'erreur systématique sur la masse stockée (à 190 bar et 30 °C, le gaz parfait se trompe d'environ 4 % sur ρ, voir le test `test_air_reel_n_est_pas_parfait_a_190_bar`). Alternative : le gaz parfait (F03), gardé pour comparer.

**Exemple à la main.** On ne peut pas faire cette équation à la main ; on vérifie plutôt un ordre de grandeur. À 1 atm et 20 °C, CoolProp donne ρ = 1,2046 kg/m³ ; le gaz parfait donne p/(R·T) = 101 325 / (287,05 × 293,15) = 1,2042 kg/m³ : écart de 0,03 %.

**Source.** `lemmon2000` dans le registre (DOI 10.1063/1.1285884) ; Dormoy §2.2, référence [38].

---

## F03 : gaz parfait à chaleurs massiques constantes

**En bref.** C'est la version « plan schématique » de l'air : pression × volume = masse × R × température. Elle est fausse de quelques pour cent à haute pression, mais elle permet de refaire tous les calculs du simulateur à la calculatrice, et de comprendre d'où viennent les résultats.

**Formule.**
- p = ρ · R · T, avec R = 287,05 J/(kg·K) ;
- h = cp · T, u = cv · T, cv = cp − R, cp = 1006 J/(kg·K) ;
- γ = cp / cv ≈ 1,40.

Symboles : p pression absolue [Pa], ρ masse volumique [kg/m³], T température [K], h enthalpie et u énergie interne massiques [J/kg].

**Niveau.** Modèle physique classique (limite basse pression de tout gaz).

**D'où elle vient.** Théorie cinétique des gaz : molécules ponctuelles sans interaction. R = R_universel / M_air = 8,314 / 0,02896.

**Hypothèses et validité.** Molécules sans volume propre ni attraction : bon à mieux que 1 % sous 10 bar et au-dessus de 250 K. À 190 bar, erreur de l'ordre de 4 % sur ρ. cp constant : erreur < 1 % entre −20 et 250 °C. Le simulateur ne l'utilise que pour **comparer** et pour les tests analytiques.

**Pourquoi.** Permet des solutions exactes (par exemple T₂ = T₁ · β^((n−1)/n)) qui servent de référence aux tests du code. Alternative : F02, utilisée pour tous les résultats.

**Exemple à la main.** Masse d'air dans 5,86 m³ à 190 bar et 30 °C : ρ = 190 × 10⁵ / (287,05 × 303,15) = 218 kg/m³, soit 1280 kg. CoolProp donne 1230 kg (−4 %).

**Source.** `air.R_specifique` et `air.cp_1bar_20C` dans le registre (source `lemmon2000`).

---

## F04 : compression polytropique, p·vⁿ = constante (éq. 1 à 3 de Dormoy)

**En bref.** Quand on comprime de l'air avec une pompe à vélo, il chauffe. Combien ? Ça dépend de la vitesse et du refroidissement de la pompe. L'indice polytropique n résume tout ça en un seul nombre : n = 1 si l'air reste à température constante (compression très lente, bien refroidie), n = 1,4 si aucune chaleur ne s'échappe (compression rapide). Un vrai compresseur est entre les deux ; Dormoy a mesuré n = 1,35 à 1,52 selon l'étage.

**Formule.**
- p_in · v_inⁿ = p_out · v_outⁿ (éq. 1), donc v_out = v_in · β^(−1/n) (éq. 2) ;
- β = p_out / p_in, rapport de pression de l'étage (éq. 3) ;
- T_out = T(p_out, ρ_out = 1/v_out) par l'équation d'état (F02).
- Cas du gaz parfait : T_out = T_in · β^((n−1)/n).

Symboles : v volume massique [m³/kg], n indice polytropique [–], β rapport de pression [–].

**Niveau.** Modèle physique classique (transformation polytropique), avec n **calibré** par Dormoy (tableau 2).

**D'où elle vient.** Généralisation des transformations réversibles d'un gaz : n = 1 isotherme, n = γ adiabatique réversible. Pour un compresseur réel, n est un paramètre effectif qui englobe l'échange thermique et une partie des irréversibilités.

**Hypothèses et validité.** Régime quasi stationnaire ; n constant pour chaque étage pendant toute la charge (Dormoy) ; variations d'énergie cinétique et potentielle négligeables. Le code refuse β < 1 et n ≤ 1.

**Pourquoi.** C'est le modèle de Dormoy, et le seul qui permette de réutiliser ses indices calibrés. Alternative : compression isentropique avec rendement isentropique, qui demanderait des rendements que l'article ne donne pas.

**Exemple à la main (étage 1).** T_in = 20 °C = 293,15 K, β = 3,25, n = 1,35. Exposant (n−1)/n = 0,35/1,35 = 0,2593. 3,25^0,2593 = e^(0,2593 × ln 3,25) = e^(0,2593 × 1,1787) = e^0,3056 = 1,357. T_out = 293,15 × 1,357 = 398 K = **125 °C**. Si l'air aspiré est à 52 °C (325 K) : T_out = 441 K = **168 °C**, ce qui correspond à la figure 18 de Dormoy.

**Source.** Dormoy 2024, §2.2.1, éq. 1–3 ; indices : `compresseur.indice_polytropique_etage1..4`.

---

## F05 : travail polytropique massique (éq. 4 de Dormoy)

**En bref.** Comprimer de l'air coûte de l'énergie. Cette formule dit combien de joules il faut pour chaque kilogramme d'air qui traverse un étage. Plus le rapport de pression est grand et plus l'air entre chaud, plus ça coûte : comprimer de l'air froid est moins cher, c'est pourquoi on refroidit entre les étages.

**Formule.** w = n/(n−1) · (p_out · v_out − p_in · v_in) [J/kg].
Cas du gaz parfait : w = n/(n−1) · R · (T_out − T_in).

La chaleur échangée pendant la compression se déduit du premier principe : q = Δh − w. Pour n < γ, q < 0 : le compresseur rejette de la chaleur vers ses parois pendant la compression (en plus de celle que les refroidisseurs retirent ensuite).

**Niveau.** Loi fondamentale (premier principe) appliquée à la transformation polytropique.

**D'où elle vient.** Travail d'un écoulement en régime permanent w = ∫ v dp, intégré le long de p·vⁿ = constante.

**Hypothèses et validité.** Mêmes hypothèses que F04. w est le travail **reçu par l'air** ; les pertes mécaniques et électriques sont ajoutées par F08.

**Pourquoi.** Expression exacte pour une polytropique ; c'est celle de Dormoy. Alternative : w = Δh (compression adiabatique), qui ne vaut que pour n = γ.

**Exemple à la main (étage 1, suite de F04).** w = 1,35/0,35 × 287,05 × (398 − 293,15) = 3,857 × 287,05 × 104,9 = **116 kJ/kg**. Pour les 4 étages, on obtient environ 520 kJ/kg à 190 bar ; avec 0,052 kg/s, cela fait 27 kW de travail sur l'air, puis 39 kW électriques après les rendements (F08).

**Source.** Dormoy 2024, §2.2.1, éq. 4.

---

## F06 : débit massique aspiré

**En bref.** Un compresseur à pistons avale toujours le même **volume** d'air à chaque tour, comme une seringue. Mais la **masse** d'air dans ce volume dépend de sa densité : l'air froid est plus dense, donc on en stocke plus par tour quand il fait froid. C'est pour ça que Dormoy trouve un meilleur rendement à −15 °C.

**Formule.** ṁ_aspiré = ρ(p_asp, T_asp) × V̇, avec V̇ = cylindrée × vitesse = 1,609 × 10⁻³ m³ × 1782 tr/min = 172,4 m³/h = 0,04789 m³/s.
Puis ṁ_refoulé = η_vol × ṁ_aspiré (rendement volumétrique, 83 %).

**Niveau.** Définition (compresseur volumétrique) et paramètre fabricant.

**D'où elle vient.** Cinématique du piston : volume balayé par tour, constant.

**Hypothèses et validité.** Vitesse constante (1782 tr/min) ; l'état de l'air aspiré est celui du point 1 de Dormoy. Le scénario peut imposer directement le débit mesuré (0,052 kg/s) au lieu de le calculer.

**Pourquoi.** Reproduit la dépendance à la température ambiante de Dormoy (0,065 kg/s à −15 °C, 0,056 à 25 °C). Le code vérifie ces deux valeurs dans `test_debit_massique_depend_de_la_densite`.

**Exemple à la main.** À 20 °C et 1,013 bar : ρ = 1,204 kg/m³ → ṁ = 1,204 × 0,04789 = **0,0577 kg/s**. Pour retrouver le 0,052 kg/s mesuré par Dormoy, il faut ρ = 1,086 kg/m³, soit T = 101 325 / (287,05 × 1,086) = 325 K = **52 °C** : l'air aspiré par le compresseur, dans son conteneur, est chaud.

**Source.** Dormoy 2024, §2.1 et §3.1 ; `compresseur.cylindree_piston1`, `compresseur.vitesse_rotation`, `compresseur.debit_volumique_entree`.

---

## F07 : lois « varie avec la pression » (interpolation linéaire bornée)

**En bref.** Dormoy dit que trois choses changent pendant la charge, à mesure que le réservoir se remplit : le rapport de pression de l'étage 3 (3,54 → 4,44), le rendement mécanique (69 → 74 %) et l'efficacité du refroidisseur 4 (74 → 85 %). Mais il ne donne pas la forme de la courbe. On suppose la plus simple : une droite entre les deux bornes. C'est comme deviner la trajectoire d'un ballon entre deux photos : la ligne droite est le pari le plus raisonnable tant qu'on n'a pas la vidéo.

**Formule.** y(p) = y₀ + (y₁ − y₀) · (p − p₀)/(p₁ − p₀), bornée à y₀ pour p ≤ p₀ et à y₁ pour p ≥ p₁, avec p = pression de refoulement, p₀ = 66 bar (pression de refoulement minimale) et p₁ = 190 bar.

L'étage 4 prend le reste : β₄ = (p_refoulement / p_amb) / (β₁ · β₂ · β₃).

**Niveau.** **Hypothèse** du projet (niveau de preuve `hypothese` dans le registre).

**D'où elle vient.** Dormoy §3.1 : « linear increase beyond the 60-bar threshold » pour les rapports des étages 3 et 4 ; §3.2 : « efficiency scaling alongside reservoir pressure » et « ranging between 69 % and 74 % depending on reservoir pressure ».

**Hypothèses et validité.** Le sens de variation du rendement mécanique (croissant avec la pression) est supposé. La pression de refoulement minimale (66 bar) est un calcul personnel : 1,013 × 3,25 × 3,75 × 3,54 × 1,52 = 66,4 bar, cohérent avec le « seuil de 60 bar » de l'article. **À vérifier dès que la figure 8 sera numérisée** (`data/validation/A_NUMERISER.md`).

**Pourquoi.** Seule option sans information supplémentaire. Alternative : rapports constants, qui contredit la figure 8.

**Exemple à la main.** À p = 128 bar (milieu) : β₃ = 3,54 + (4,44 − 3,54) × (128 − 66)/(190 − 66) = 3,54 + 0,90 × 0,5 = 3,99. Rapport total 128/1,013 = 126,4 ; β₄ = 126,4 / (3,25 × 3,75 × 3,99) = **2,60**.

**Source.** Dormoy 2024, §3.1–3.2, fig. 8, tableau 2 ; `compresseur.loi_rapport_etage3`, `compresseur.loi_rendement_mecanique`, `refroidisseur.loi_efficacite_etage4`, `compresseur.pression_refoulement_min`.

---

## F08 : puissance électrique du compresseur (éq. 5 de Dormoy)

**En bref.** Le moteur électrique n'envoie pas toute son énergie à l'air : une partie chauffe le moteur lui-même, une autre se perd en frottements dans les pistons et les paliers. Pour 100 unités d'électricité, Dormoy a mesuré qu'environ 70 arrivent à l'air. C'est la première grosse perte du système.

**Formule.** P_él = ṁ · Σᵢ wᵢ / (η_méc · η_él) [W], avec wᵢ le travail de chaque étage (F05).

**Niveau.** Définition des rendements ; η_méc **calibré** (69–74 %, tableau 2), η_él **fabricant** (94–95 %, tableau 7).

**D'où elle vient.** Bilan de puissance sur le groupe moteur-compresseur.

**Hypothèses et validité.** Le débit ṁ sur lequel s'applique le travail est le débit **aspiré** (0,052 kg/s), comme dans le tableau 6 de Dormoy ; le rendement mécanique calibré absorbe sans doute une partie des pertes volumétriques. Le rendement électrique est pris au milieu de la plage (94,5 %), hypothèse notée dans la provenance du scénario.

**Pourquoi.** C'est l'équation de Dormoy. Alternative : un rendement global unique, moins traçable.

**Exemple à la main.** Avec Σ wᵢ ≈ 520 kJ/kg à 190 bar, ṁ = 0,052 kg/s, η_méc = 0,74, η_él = 0,945 : P_él = 0,052 × 520 000 / (0,74 × 0,945) = 27 040 / 0,699 = **38,7 kW**. Dormoy mesure 39 kW en moyenne.

**Source.** Dormoy 2024, §2.2.1, éq. 5 ; `compresseur.rendement_mecanique`, `compresseur.rendement_electrique`.

---

## F09 : refroidisseur, méthode de l'efficacité (éq. 6 à 9 de Dormoy)

**En bref.** Après chaque étage, l'air chaud passe dans un radiateur ventilé par l'air extérieur. Un radiateur parfait ramènerait l'air exactement à la température extérieure ; un vrai radiateur n'y arrive qu'à 80 ou 90 %. Ce pourcentage, l'efficacité, est tout ce qu'on a besoin de connaître pour calculer la température de sortie, sans savoir à quoi ressemble le radiateur.

**Formule.**
- T_out = T_in − ε · (T_in − T_froid) (éq. 8) ;
- chaleur retirée : q = h(p, T_in) − h(p, T_out) [J/kg] (éq. 7, qui intègre cp(T)) ;
- puissance : Q̇ = ṁ · q ; total : somme sur les 4 étages (éq. 9) ;
- part « récupérable » au-dessus d'un seuil T_s : q_sup = h(p, T_in) − h(p, max(T_out, T_s)) si T_in > T_s, sinon 0.

**Niveau.** Modèle physique classique (méthode ε-NTU), avec ε **calibré** (82 / 85 / 88 / 74–85 %).

**D'où elle vient.** Définition de l'efficacité d'un échangeur : chaleur échangée / chaleur maximale possible, où le maximum correspond au fluide de plus faible débit capacitif (ici l'air comprimé) ramené à la température d'entrée de l'autre fluide.

**Hypothèses et validité.** Débits constants pendant un pas ; pas de perte de charge ; le débit capacitif minimal est toujours celui de l'air comprimé (Dormoy : la source froide débite 11 000 m³/h). La température de la source froide est l'ambiant (20 °C supposés).

**Pourquoi.** Dormoy n'a pas la géométrie des échangeurs ; l'efficacité est la seule grandeur mesurable. Alternative : un modèle NTU complet (UA, surfaces), impossible sans les plans.

**Exemple à la main (étage 1, suite de F04).** T_in = 125 °C, T_froid = 20 °C, ε = 0,82 : T_out = 125 − 0,82 × 105 = **39 °C**. Chaleur retirée : q ≈ cp × ΔT = 1006 × 86 = 86,5 kJ/kg, soit 4,5 kW pour 0,052 kg/s. Rien au-dessus de 130 °C puisque T_in < 130 °C. Avec un air aspiré à 52 °C (T_in = 168 °C) : T_out = 168 − 0,82 × 148 = **47 °C**, et q_sup = 1006 × (168 − 130) = 38 kJ/kg → 2,0 kW, contre 1,9 kW dans le tableau 6 de Dormoy.

**Source.** Dormoy 2024, §2.2.2, éq. 6–9, tableau 2 ; `refroidisseur.efficacite_etage1..4`.

---

## F10 : sécheur, perte de débit (éq. 10 de Dormoy)

**En bref.** L'air comprimé doit être sec, sinon l'eau gèlerait dans la turbine. Le sécheur retient l'humidité dans des billes, puis utilise une partie de l'air comprimé pour « rincer » les billes et rejette cet air dehors. Résultat : 19 % de l'air comprimé, et donc 19 % de l'énergie dépensée pour le comprimer, part à la poubelle.

**Formule.** ṁ_out = η_sécheur · ṁ_in, avec η_sécheur = 0,81 ; p et T inchangées.

**Niveau.** Paramètre **mesuré** (Dormoy §2.2.3 ; le fabricant annonce 75–80 %).

**D'où elle vient.** Mesure du débit avant et après le sécheur sur le banc.

**Hypothèses et validité.** Perte constante quelle que soit l'humidité de l'air aspiré. La phase 8 remplacera ce modèle par un bilan d'eau (point de rosée sous pression, séparateur).

**Pourquoi.** Seule donnée disponible. Note : 0,052 × 0,83 × 0,81 = 0,035 kg/s, alors que Dormoy mesure 0,032 kg/s à la sortie du sécheur ; le scénario peut imposer la valeur mesurée (variantes C et D du rapport de validation).

**Exemple à la main.** 0,043 kg/s entrent, 0,043 × 0,81 = 0,0348 kg/s sortent, 0,0082 kg/s sont rejetés : en 10 h, 295 kg d'air comprimé perdus.

**Source.** Dormoy 2024, §2.2.3, éq. 10 ; `secheur.efficacite`, `secheur.debit_massique_sortie`.

---

## F11 : réservoir équivalent (éq. 11 et 12 de Dormoy)

**En bref.** Le banc a 20 bouteilles reliées entre elles. Comme elles sont toutes à la même pression et presque à la même température, on les remplace par une seule grosse bouteille imaginaire qui a leur volume total et leur surface totale. Ça simplifie le calcul sans rien perdre d'important.

**Formule.** V_éq = 8 × 0,32 + 12 × 0,275 = 5,86 m³ ; A_éq = 8 × 3,6 + 12 × 3,06 = 65,5 m².

**Niveau.** Hypothèse de modélisation de Dormoy + données fabricant.

**D'où elle vient.** Additivité des volumes et des surfaces de réservoirs en parallèle à l'équilibre.

**Hypothèses et validité.** Température uniforme dans tout le volume (Dormoy, d'après Chen et al.) ; volume constant ; pas de perte de charge entre bouteilles. Remarque : avec 0,27 m³ par petite bouteille (tableau 8) on obtient 5,80 m³ ; le simulateur garde les 5,86 m³ utilisés par Dormoy.

**Pourquoi.** Dormoy fait ce choix ; un modèle par bouteille ne changerait rien sans mesures individuelles.

**Exemple à la main.** Ci-dessus.

**Source.** Dormoy 2024, §2.2.4, éq. 11–12, tableau 8 ; `reservoir.volume_total`, `reservoir.surface_equivalente_totale`.

---

## F12 : bilan de masse et d'énergie du réservoir (éq. 13, 14 et 21 de Dormoy)

**En bref.** Un réservoir qu'on remplit, c'est une tirelire : la masse d'air augmente de ce qui entre moins ce qui sort. Pour l'énergie, c'est pareil, avec une subtilité : l'air qui entre « pousse » l'air déjà là, donc il apporte un peu plus que sa seule énergie interne (c'est l'enthalpie). C'est pour ça qu'un réservoir qu'on gonfle chauffe, même si l'air qui entre est tiède. Et comme une bouteille thermos imparfaite, le réservoir perd de la chaleur vers l'extérieur.

**Formule.** Sur un pas Δt :
- masse : Δm = (ṁ_in − ṁ_out) · Δt ;
- énergie : ΔU = ṁ_in · h_in · Δt − ṁ_out · h_out · Δt − Q_perte (éq. 13–14) ;
- pertes, modèle « K global » : Q_perte = K · A · (T − T_amb) · Δt, K = 8,8 W/(m²·K) ;
- pertes, modèle « paroi » (éq. 21) : Q_perte = h_int · A · (T − T_paroi) · Δt, et la paroi évolue selon C_paroi · ΔT_paroi = h_int·A·(T − T_paroi)·Δt − h_ext·A·(T_paroi − T_amb)·Δt ;
- puis T = T(ρ = m/V, u = U/m) par l'équation d'état (F02, méthode de Newton) et p = p(ρ, T).

Mise en œuvre : le terme de perte est intégré exactement sur le pas (facteur τ/Δt · (1 − e^(−Δt/τ)) avec τ = m·cv/(K·A)), ce qui reste stable au début de la charge où la masse d'air est minuscule.

**Niveau.** Loi fondamentale (conservation de la masse et de l'énergie) + coefficients **calibrés** (K, h_int, h_ext).

**D'où elle vient.** Premier principe pour un volume de contrôle ouvert, sans travail (volume constant), énergies cinétique et potentielle négligées.

**Hypothèses et validité.** Température uniforme ; pas de rayonnement ; K constant. Le modèle « paroi » suppose une température de paroi uniforme et une capacité thermique totale de 1,77 MJ/K (calcul personnel à partir du tableau 8).

**Pourquoi.** C'est le modèle de Dormoy, validé par lui avec un MAPE ≤ 1,1 % sur la température en décharge. Le modèle « K global » suffit pour la charge ; le modèle « paroi » sera utilisé en décharge (phase 2), où Dormoy a constaté que la chaleur accumulée dans la structure compte.

**Exemple à la main (gaz parfait).** On remplit un réservoir vide, sans pertes, avec de l'air à T_in. Toute l'enthalpie entrée devient énergie interne : m · cv · T_final = m · cp · T_in, donc T_final = γ · T_in = 1,4 × 293 K = 410 K = **137 °C**. C'est le test `test_remplissage_adiabatique_tend_vers_gamma_T_in`. En réalité les pertes (K·A = 577 W/K) ramènent l'air vers l'ambiant pendant les 10 h de charge.

**Source.** Dormoy 2024, §2.2.4 et §3.2, éq. 13–14 et 21 ; `reservoir.K_global`, `reservoir.h_conv_int`, `reservoir.h_conv_ext`, `reservoir.capacite_thermique_paroi`.

---

## F13 : bilan d'énergie de la charge complète

**En bref.** À la fin, on vérifie que rien ne s'est perdu dans les calculs : toute l'électricité consommée doit se retrouver quelque part, soit en chaleur (moteur, compresseur, refroidisseurs, parois du réservoir), soit dans l'air rejeté, soit dans l'air stocké. C'est comme vérifier qu'un budget est équilibré : si la somme des postes ne redonne pas le total, il y a une erreur quelque part.

**Formule.**
E_él = (E_él − E_pol) + Q_poly + Q_refroidisseurs + E_air_perdu + Q_paroi + E_stockée, avec :
- E_pol = ∫ ṁ_asp · Σ wᵢ dt : travail reçu par l'air ;
- Q_poly = ∫ ṁ_asp · Σ (−qᵢ) dt : chaleur rejetée pendant les compressions (F05) ;
- Q_refroidisseurs = ∫ ṁ_asp · Σ q_ref,i dt (F09) ;
- E_air_perdu = ∫ (ṁ_asp − ṁ_rés) · (h_sortie − h_amb) dt : enthalpie emportée par l'air rejeté (volumétrique + sécheur) ;
- Q_paroi = ∫ Q̇_perte dt (F12) ;
- E_stockée = ΔU_réservoir − m_entrée · h_amb : énergie interne gagnée par le réservoir, comptée par rapport à l'enthalpie de l'air aspiré.

**Niveau.** Loi fondamentale (premier principe sur le système complet).

**D'où elle vient.** Somme des bilans de chaque composant ; les termes intermédiaires (enthalpies entre étages) se télescopent.

**Hypothèses et validité.** Même référence d'enthalpie partout (CoolProp). Le test `test_bilan_d_energie_ferme_a_1_pourcent` exige un résidu < 1 % ; en pratique il est < 0,001 %.

**Pourquoi.** Un modèle dont le bilan ne ferme pas a une erreur de code ou de physique. Ce bilan est aussi la base du tableau « 1000 unités » de la phase 3, qui, lui, comptera l'**exergie** (énergie utile) et non l'énergie.

**Exemple à la main.** Scénario A du rapport de validation : 373 kWh électriques = 124 (pertes moteur et mécanique) + 7 (chaleur de compression) + 241 (refroidisseurs) + 0,5 (air rejeté) + 40 (parois) − 39 (air stocké, négatif car il finit à peu près à l'ambiant avec une énergie interne massique inférieure à l'enthalpie entrée) = 373 kWh.

**Source.** Convention du projet ; `caes/systeme.py`, fonction `simuler_charge`.

---

## F14 : RMSE et MAPE (éq. 18 et 19 de Dormoy)

**En bref.** Pour dire si une simulation « colle » à une mesure, il faut un chiffre. Le RMSE donne l'écart typique dans l'unité de la grandeur (par exemple 2,8 °C) ; le MAPE donne l'écart moyen en pourcentage (par exemple 1,9 %). Dormoy obtient un MAPE inférieur à 3,6 % sur la charge : c'est la barre que le simulateur vise.

**Formule.**
- RMSE = √( (1/N) · Σᵢ (ŷᵢ − yᵢ)² ) ;
- MAPE = (100/N) · Σᵢ |(ŷᵢ − yᵢ)/yᵢ| ;
avec ŷᵢ la valeur simulée, yᵢ la valeur mesurée, N le nombre de points. Les courbes simulées sont interpolées aux instants des mesures.

**Niveau.** Définition statistique.

**D'où elle vient.** Moyennes quadratique et absolue des écarts.

**Hypothèses et validité.** Le MAPE est indéfini si une mesure vaut zéro (le code refuse). Pour une température, le MAPE dépend de l'unité (°C ou K) : Dormoy l'exprime en °C.

**Pourquoi.** Ce sont les indicateurs de Dormoy (tableaux 3 et 4), donc directement comparables.

**Exemple à la main.** Mesures 10, 20, 30 ; simulation 11, 19, 33. Écarts 1, −1, 3. RMSE = √((1 + 1 + 9)/3) = √3,67 = 1,91. MAPE = (10 % + 5 % + 10 %)/3 = 8,3 %.

**Source.** Dormoy 2024, §2.3, éq. 18–19.

---

## F15 : détendeur isenthalpique (laminage)

**En bref.** Le détendeur, c'est un robinet à moitié fermé qui fait chuter la pression de 190 bar à 35 bar sans rien produire. Pour un gaz parfait, la température ne changerait pas. Pour l'air réel à haute pression, elle baisse d'une vingtaine de degrés : c'est l'effet Joule-Thomson, celui qui refroidit la bombe aérosol quand on appuie dessus. L'énergie ne disparaît pas (l'enthalpie est conservée), mais la **capacité de produire du travail** est détruite : on en reparlera en phase 3 avec l'exergie.

**Formule.** h(p_out, T_out) = h(p_in, T_in), donc T_out = T(p_out, h_in) par l'équation d'état (F02). Le détendeur fonctionne tant que p_réservoir − p_consigne ≥ 15 bar ; en dessous, il s'arrête (Dormoy § 2.1).

**Niveau.** Loi fondamentale (premier principe en écoulement permanent, sans travail ni échange de chaleur).

**D'où elle vient.** Bilan d'énergie d'un écoulement adiabatique sans travail, énergies cinétique et potentielle négligées : ce qui entre (h_in) égale ce qui sort (h_out).

**Hypothèses et validité.** Adiabatique (le gaz passe trop vite pour échanger de la chaleur avec la vanne) ; pas de variation de vitesse notable. Validé par Dormoy : MAPE 0,39 % sur la température de sortie (tableau 4).

**Pourquoi.** C'est le modèle le plus simple et il est validé. Alternative : la relation de Cheayb (F16), légèrement meilleure chez Dormoy (0,21 %) mais hors de sa plage de validité à 190 bar.

**Exemple à la main.** Pour un gaz parfait, h ne dépend que de T : T_out = T_in, pas de refroidissement. Pour l'air réel, CoolProp donne, de 190 bar et 55 °C à 35 bar : T_out ≈ 35 °C, soit environ 20 K de moins. Règle approximative : 0,2 K par bar de chute à basse pression, moins à haute pression.

**Source.** Dormoy 2024, § 2.2.5 ; `detendeur.ecart_pression_min`.

---

## F16 : détendeur, relation de Cheayb et al. (éq. 15 de Dormoy)

**En bref.** Au lieu de passer par l'équation d'état complète, Cheayb et al. ont ajusté une petite formule (une parabole en pression) sur des mesures de détente d'air, d'après les travaux anciens de Hoxton. Elle donne directement la température de sortie à partir de la température et des pressions. C'est une « recette » empirique : rapide, mais seulement fiable là où elle a été ajustée (25 à 150 bar).

**Formule.** T(P) = a·P² + b·P + c, avec P en **bar** et T en **kelvin** :
- a = ½ · (0,0297/T_in − 1,674/T_in² − 19 093/T_in³ + 0,0000157) ;
- b = 50,1/T_in + 14 830/T_in² + 366 000/T_in³ − 0,122 ;
- c = T_in − a·P_in² − b·P_in (pour que T(P_in) = T_in).

**Niveau.** Corrélation empirique.

**D'où elle vient.** Ajustement sur des mesures de détente isenthalpique de l'air (Hoxton, repris par Cheayb et al. [27]). La dérivée dT/dP = 2aP + b est le coefficient de Joule-Thomson, environ 0,2 K/bar à basse pression.

**Hypothèses et validité.** 25 à 150 bar. Dormoy l'emploie jusqu'à 190 bar et observe qu'elle reste bonne (MAPE 0,21 %). Le code signale `hors_validite` quand p_in sort de la plage. Transcrite à partir de l'image de la page 8 de l'article (le texte extrait était illisible).

**Pourquoi.** Permet de comparer deux modèles indépendants : s'ils concordent, on a confiance. Le test `test_cheayb_coherent_avec_isenthalpique` exige moins de 8 K d'écart ; en pratique l'écart est d'environ 1 K.

**Exemple à la main.** T_in = 328,15 K (55 °C), P_in = 190 bar, P_out = 35 bar. a = ½ (9,05·10⁻⁵ − 1,55·10⁻⁵ − 5,40·10⁻⁴ + 1,57·10⁻⁵) = ½ (−4,49·10⁻⁴) = −2,25·10⁻⁴. b = 0,1527 + 0,1377 + 0,0104 − 0,122 = 0,1788. ΔT = a (35² − 190²) + b (35 − 190) = −2,25·10⁻⁴ × (−34 875) + 0,1788 × (−155) = 7,8 − 27,7 = **−19,9 K** : l'air sort à 35 °C.

**Source.** Dormoy 2024, § 2.2.5, éq. 15 ; `detendeur.cheayb.*`.

---

## F17 : détente polytropique d'un étage de turbine (éq. 16 de Dormoy)

**En bref.** C'est la compression à l'envers : l'air se détend, pousse les aubes de la turbine et se refroidit. Le même indice n sert, mais ici il a été mesuré sur les turbines DEPRAG (1,19 / 1,23 / 1,27). Un n proche de 1 signifie que l'air se refroidit peu pour la pression perdue, ce qui n'est pas « gratuit » : ça traduit les frottements dans la turbine qui réchauffent l'air.

**Formule.**
- v_out = v_in · (p_in/p_out)^(1/n) (éq. 16) ; T_out = T(p_out, 1/v_out) ;
- travail polytropique produit : w_pol = n/(n−1) · (p_in·v_in − p_out·v_out) [J/kg], > 0.
- Gaz parfait : T_out = T_in · (p_out/p_in)^((n−1)/n).

**Niveau.** Modèle physique classique avec n **fabricant** (tableau 9, « calculated polytropic index »).

**D'où elle vient.** Même dérivation que F04 et F05, avec p_out < p_in.

**Hypothèses et validité.** n constant ; débit constant (0,321 kg/s) ; pas de perte de charge sauf la petite chute entre étages (11,5 → 11 bar, traitée comme un laminage F15). Le test `test_tableau_9_deprag_reproduit` vérifie qu'on retrouve les températures de sortie du tableau 9 à 2,5 K près.

**Pourquoi.** C'est le modèle de Dormoy, calé sur la fiche DEPRAG. Alternative : détente isentropique avec rendement isentropique, qui demanderait des données que la fiche ne donne pas sous cette forme.

**Exemple à la main (étage 1).** T_in = 130 °C = 403,15 K, p 40 → 11,5 bar, n = 1,19. Exposant (n−1)/n = 0,1597 ; (11,5/40)^0,1597 = e^(0,1597 × ln 0,2875) = e^(0,1597 × (−1,2465)) = e^(−0,199) = 0,8195. T_out = 403,15 × 0,8195 = 330,4 K = **57 °C** (tableau 9 : 59,2 °C). w_pol = 1,19/0,19 × 287 × (403,15 − 330,4) = 6,263 × 287 × 72,7 = **130,7 kJ/kg**.

**Source.** Dormoy 2024, § 2.2.6, éq. 16 ; `turbine.etageN.*`.

---

## F18 : puissance électrique de la turbine (éq. 17 de Dormoy)

**En bref.** La turbine ne transforme pas tout le travail de détente en électricité : une partie part en frottements (rendement « mécanique », 53 à 73 % selon l'étage, mesuré par DEPRAG) et une autre dans la génératrice (90 à 92 %). Pour l'étage 1, sur 100 unités de travail de détente, 53 arrivent à l'arbre et 48 au réseau.

**Formule.** P_mec = η_mec · ṁ · w_pol ; P_él = η_él · P_mec ; total sur les étages (éq. 17).

Vérification physique : le travail à l'arbre vaut à peu près la chute d'enthalpie de l'air, ṁ·(h_in − h_out) ≈ P_mec. Le petit reste (« chaleur résiduelle ») est suivi dans le bilan.

**Niveau.** Définition des rendements, paramètres **fabricant** (tableau 9).

**D'où elle vient.** Bilan de puissance sur la turbine et la génératrice.

**Hypothèses et validité.** Rendements constants quel que soit l'état de l'air (Dormoy). Le test `test_tableau_9_deprag_reproduit` retrouve 22,1 / 22,0 / 23,7 kW mécaniques et 61,9 kW électriques à 3 % près.

**Pourquoi.** Seules données disponibles. Alternative : courbe de rendement selon le débit ou la pression (phase 7, pression glissante).

**Exemple à la main (étage 1, suite de F17).** P_mec = 0,53 × 0,321 × 130,7 = **22,2 kW** (tableau 9 : 22,1). P_él = 0,90 × 22,2 = **20,0 kW** (tableau 9 : 20,0).

**Source.** Dormoy 2024, § 2.2.6, éq. 17 ; `turbine.etageN.rendement_mecanique`, `turbine.etageN.rendement_electrique`.

---

## F19 : réchauffage avant un étage, chaleur suivie par source

**En bref.** Avant chaque étage, on réchauffe l'air (130 °C, puis 90 °C, puis 90 °C) : plus il est chaud, plus il pousse fort en se détendant, et il ne givre pas en sortie. La règle du projet : **cette chaleur n'est jamais gratuite par défaut**. Chaque joule ajouté porte une étiquette qui dit d'où il vient : « externe » (il faudra le compter dans la consommation) ou « cuve_X » (il vient de la chaleur de compression stockée dans une cuve de gravier, phases 4 et 5).

**Formule.** q_réchauffage = h(p, T_cible) − h(p, T_in) si T_in < T_cible, sinon 0 ; Q̇ = ṁ · q. Le résultat de chaque étage porte `source_chaleur`. Le bilan de la décharge cumule la chaleur par source ; le rendement F20 en dépend.

**Niveau.** Loi fondamentale (bilan d'enthalpie à pression constante) + convention du projet.

**D'où elle vient.** Premier principe sur l'échangeur côté air ; température cible du tableau 9.

**Hypothèses et validité.** Pas de perte de charge dans le réchauffeur ; la source est toujours capable de fournir la température cible (vrai pour « externe » ; pour une cuve, la phase 5 limitera T_cible à ce que la cuve peut donner).

**Pourquoi.** Dormoy impose 130/90/90 °C sans dire d'où vient la chaleur, et obtient 16 %. Sans l'étiquette, on ne peut pas savoir si ce 16 % est honnête. Le test `test_regle_du_bilan_de_chaleur` vérifie que toute chaleur a une source.

**Exemple à la main (étage 1).** L'air arrive à 15 °C après le détendeur ; cible 130 °C ; cp ≈ 1010 J/(kg·K) : q = 1010 × 115 = 116 kJ/kg, Q̇ = 0,321 × 116 = **37,3 kW** (tableau 5 : 33,5 à 38,0 kW). Sur 38 min : 23,6 kWh (tableau 5 : 24,8).

**Source.** Dormoy 2024, § 3.3.5, tableau 5 ; convention du projet (`00-consignes-communes.md`).

---

## F20 : rendement aller-retour, deux définitions (éq. 20 de Dormoy)

**En bref.** Le rendement, c'est « ce qu'on récupère divisé par ce qu'on a mis ». Mais qu'est-ce qu'on a mis ? Seulement l'électricité du compresseur, ou aussi la chaleur pour réchauffer l'air avant la turbine ? Dormoy ne compte que l'électricité et trouve 16 %. Si on compte aussi la chaleur, on tombe à 13 %. Les deux chiffres sont vrais ; il faut juste dire lequel on utilise.

**Formule.**
- RTE_sans_chaleur = E_produite / E_consommée (éq. 20) ;
- RTE_avec_chaleur_externe = E_produite / (E_consommée + Q_externe), où Q_externe est la chaleur de source « externe » (F19).

**Niveau.** Définition.

**D'où elle vient.** Convention. La seconde traite 1 kWh de chaleur comme 1 kWh d'électricité, ce qui est sévère (la chaleur à 130 °C vaut moins qu'autant d'électricité : voir l'exergie, phase 3) mais honnête tant que la source n'est pas précisée.

**Hypothèses et validité.** E_consommée est la recharge **depuis la pression d'arrêt de la décharge** (18 bar pour un étage, 55 bar pour trois) : le coussin d'air qui reste n'est pas une perte par cycle.

**Pourquoi.** Deux chiffres valent mieux qu'un chiffre ambigu. Le registre interdit d'ailleurs d'utiliser un rendement global comme donnée d'entrée : il doit sortir du modèle.

**Exemple à la main.** 3 étages : 39,0 kWh produits, 276 kWh consommés, 44,6 kWh de chaleur externe. RTE sans chaleur = 39,0/276 = **14,1 %** ; avec = 39,0/(276 + 44,6) = **12,2 %**.

**Source.** Dormoy 2024, § 2.4, éq. 20 ; `caes/systeme.py`, `rendements_aller_retour`.

---

## F21 : exergie d'un écoulement d'air

**En bref.** L'énergie ne se perd jamais, mais elle se dégrade : la chaleur à 20 °C dans l'air du conteneur contient de l'énergie, et pourtant elle ne peut plus rien faire tourner. L'exergie, c'est la partie **utile** de l'énergie : le travail maximal qu'on pourrait tirer d'un kilogramme d'air en le ramenant à l'état de l'air ambiant (20 °C, 1 bar). De l'air à 190 bar en a beaucoup ; de l'air tiède à 1 bar, presque pas. Contrairement à l'énergie, l'exergie **se détruit** à chaque gaspillage, ce qui permet de dire exactement où.

**Formule.** ex = (h − h₀) − T₀ · (s − s₀) [J/kg], avec h et s l'enthalpie et l'entropie massiques de l'air à (p, T), h₀ et s₀ les mêmes à l'état mort (T₀, p₀), et T₀ en kelvins.

**Niveau.** Loi fondamentale (combinaison du premier et du deuxième principe).

**D'où elle vient.** Travail maximal d'un écoulement qui passe de (p, T) à (p₀, T₀) en n'échangeant de la chaleur qu'avec l'ambiant à T₀ : W_max = (h − h₀) − T₀(s − s₀). Tout processus réel donne moins ; la différence est l'exergie détruite (F24).

**Hypothèses et validité.** État mort fixé par le scénario (T_amb, p_amb). Énergies cinétique et potentielle négligées. L'exergie d'un écoulement à une pression inférieure à p₀ peut être légèrement négative (l'air ne peut pas « sortir » dans l'ambiant) : c'est le cas de la sortie DEPRAG à 1,0 bar contre 1,013 bar.

**Pourquoi.** C'est la seule grandeur qui permet de comparer une perte de pression (détendeur), une perte de chaleur (refroidisseur) et une perte d'air (sécheur) sur la même échelle. Dormoy recommande cette analyse dans ses perspectives. Alternative : le bilan d'énergie seul (F13), qui dit combien de chaleur sort mais pas ce qu'elle vaut.

**Exemple à la main (gaz parfait, 20 °C).** Air à 190 bar et 20 °C : h − h₀ = 0 (même température), s − s₀ = −R ln(190/1,013) = −287 × 5,23 = −1502 J/(kg·K). ex = 0 + 293,15 × 1502 = **440 kJ/kg**. Air à 1 bar et 130 °C : h − h₀ = 1006 × 110 = 110,7 kJ/kg ; s − s₀ = 1006 × ln(403/293) = 320 J/(kg·K) ; ex = 110,7 − 293,15 × 0,320 = **17 kJ/kg**. La chaleur à 130 °C vaut 25 fois moins que la pression à 190 bar, par kilogramme.

**Source.** Thermodynamique classique ; Baniamerian 2025 § 2 ; `caes/exergie.py`, `Exergie.flux`.

---

## F22 : exergie d'un réservoir (et équation 22 de Baniamerian)

**En bref.** Pour une masse d'air **enfermée** dans un réservoir (plutôt qu'un écoulement), la formule change un peu : il faut tenir compte du travail que fait l'atmosphère quand le volume change. Pour un réservoir à la température ambiante, on obtient la formule simple de Baniamerian, celle qui donnait 132 kWh pour les réservoirs de Dormoy dans la fiche.

**Formule.** Ex = m · [(u − u₀) + p₀ · (v − v₀) − T₀ · (s − s₀)] [J], avec u l'énergie interne et v le volume massiques.
Cas particulier, gaz parfait à T = T₀ (éq. 22 de Baniamerian) : Ex = V · p₀ · (r · ln r − (r − 1)), avec r = p/p₀.

**Niveau.** Loi fondamentale ; l'éq. 22 est un cas particulier (gaz parfait, isotherme).

**D'où elle vient.** Travail maximal d'un système fermé ramené à (p₀, T₀), moins le travail « gratuit » fourni par la pression atmosphérique p₀ · ΔV. Pour un gaz parfait à T₀ : u = u₀, s − s₀ = −R ln r, v − v₀ = v₀(1/r − 1), et m = r p₀ V/(R T₀), d'où la formule de Baniamerian. Le test `test_eq_22_baniamerian_egale_exergie_fermee_gaz_parfait` vérifie l'identité.

**Hypothèses et validité.** Température uniforme dans le réservoir (hypothèse de Dormoy). Avec l'air réel, l'exergie à 190 bar est environ 3 % plus faible qu'avec le gaz parfait.

**Pourquoi.** C'est ce qui est « stocké » entre la charge et la décharge. Le tableau 1000 unités l'utilise pour la ligne « exergie stockée » et pour le coussin (masse morte).

**Exemple à la main.** V = 5,86 m³, p = 190 bar, p₀ = 1,013 bar, T₀ = 15 °C : r = 187,6 ; r ln r = 187,6 × 5,234 = 982 ; r − 1 = 186,6 ; Ex = 5,86 × 101 325 × (982 − 186,6) = 4,72 × 10⁸ J = **131 kWh** (la fiche disait 132). L'air réel donne 127 kWh.

**Source.** Baniamerian 2025, éq. 22 ; `Exergie.fermee`, `Exergie.air_comprime_gaz_parfait`.

---

## F23 : exergie d'une chaleur (facteur de Carnot)

**En bref.** Une chaleur Q n'est utile qu'en proportion de sa température : avec de la chaleur à 130 °C, le meilleur moteur du monde ne pourrait produire que 27 % de Q en travail ; avec de la chaleur à 45 °C, 8 %. C'est le facteur de Carnot. Il explique pourquoi les refroidisseurs de Dormoy rejettent 689 unités de chaleur mais seulement 156 unités d'exergie.

**Formule.** Ex_Q = Q · (1 − T₀/T) [J], T en kelvins, la température à laquelle la chaleur est échangée. Négatif si T < T₀ : du « froid » est aussi une exergie (il faut du travail pour le produire).

**Niveau.** Loi fondamentale (deuxième principe, rendement de Carnot).

**D'où elle vient.** Un moteur réversible entre T et T₀ produit au plus Q(1 − T₀/T).

**Hypothèses et validité.** Pour une chaleur échangée pendant que la température varie (refroidissement de 168 à 47 °C), le code intègre : l'exergie de la chaleur retirée à l'air est exactement la baisse d'exergie de l'air (F21), ce qui revient à utiliser la température instantanée. Pour la chaleur échangée pendant la compression, on utilise la température logarithmique moyenne.

**Pourquoi.** C'est ce qui dit ce qu'une cuve de gravier peut au mieux récupérer : non pas 689 unités, mais 156, et surtout la part au-dessus de 130 °C.

**Exemple à la main.** 100 kWh de chaleur à 130 °C (403 K), ambiant 20 °C (293 K) : Ex = 100 × (1 − 293/403) = 100 × 0,273 = **27 kWh**. Les mêmes 100 kWh à 45 °C (318 K) : 100 × (1 − 293/318) = **7,9 kWh**.

**Source.** Thermodynamique classique ; `Exergie.chaleur`.

---

## F24 : exergie détruite = T₀ × entropie créée (théorème de Gouy-Stodola)

**En bref.** À chaque fois qu'un processus est irréversible (frottement, chute de pression dans une vanne, chaleur qui passe d'un corps chaud à un corps froid), de l'entropie est créée, et une quantité d'exergie égale à T₀ fois cette entropie disparaît pour toujours. C'est ainsi que le simulateur calcule, composant par composant, ce que chacun détruit, sans jamais avoir besoin de « deviner » : il compte l'entropie qui entre, celle qui sort, et la différence est la casse.

**Formule.** D = T₀ · S_gen [J], avec S_gen = S_sortie − S_entrée − Σ Q_i/T_i (bilan d'entropie du composant : entropie emportée par les flux, moins celle apportée par les chaleurs à leur température).
Cas utilisés :
- compresseur polytropique : S_gen = ṁ (s_out − s_in) − ṁ q/T_lm ; pour un isotherme réversible à T₀, D = 0 ;
- détendeur isenthalpique : D = ṁ (ex_in − ex_out) ;
- turbine : D = ṁ (ex_in − ex_out) − W_arbre ;
- réservoir en charge : S_gen = ΔS_réservoir − ∫ ṁ_in s_in dt + ∫ Q_perte/T dt.

**Niveau.** Loi fondamentale (deuxième principe).

**D'où elle vient.** Combinaison des bilans d'énergie et d'entropie d'un volume de contrôle ; démontrée par Gouy (1889) et Stodola (1898).

**Hypothèses et validité.** Les températures d'échange doivent être celles du bilan d'entropie (sinon le bilan global ne ferme pas). Le test `test_bilan_charge_ferme_a_1_pourcent` vérifie que la somme des destructions, des pertes et du stock redonne l'électricité entrée à mieux que 1 % (en pratique 0,2 %) : comme chaque poste est calculé indépendamment, cette fermeture est une vraie vérification.

**Pourquoi.** C'est la seule méthode qui donne une perte **par composant**. Le bilan d'énergie (F13) ne sait pas qu'un détendeur détruit quelque chose, puisque l'enthalpie y est conservée.

**Exemple à la main (détendeur, gaz parfait).** 1 kg d'air passe de 190 à 3 bar à température constante. s_out − s_in = R ln(190/3) = 287 × 4,149 = 1191 J/(kg·K). D = 293,15 × 1191 = **349 kJ/kg**. Sur 1100 kg soutirés : 384 MJ = 107 kWh, soit, pour 352 kWh consommés, **303 unités sur 1000** (le simulateur, avec l'air réel et les températures variables, trouve 234).

**Source.** Thermodynamique classique ; `caes/exergie.py`, `exergie_etage_compression`, `bilan_exergie_charge`, `bilan_exergie_decharge`.

---

## F25 : lit de gravier, équations de Schumann (1929) et solution exacte

**En bref.** Quand de l'air chaud traverse une cuve de cailloux froids, il ne réchauffe pas toute la cuve d'un coup : il réchauffe d'abord les cailloux du haut, puis ceux d'en dessous, et un **front chaud** descend lentement dans la cuve, comme une vague. Tant que le front n'a pas atteint le bas, l'air ressort froid. Schumann a écrit en 1929 les deux équations qui décrivent ça (une pour l'air, une pour les cailloux) et les a résolues exactement pour le cas simple.

**Formule.** Par mètre cube de lit, avec x la position le long de l'axe et t le temps :
- air : ε·ρ_f·c_f·∂T_f/∂t + G·c_f·∂T_f/∂x = h·a_v·(T_s − T_f) ;
- solide : (1−ε)·ρ_s·c_s·∂T_s/∂t = h·a_v·(T_f − T_s) ;
avec ε la porosité, G = ṁ/A le débit par m² de section, h le coefficient d'échange (F27), a_v = 6(1−ε)/d la surface des cailloux par m³ de lit.

Solution exacte (capacité de l'air négligée, lit initialement uniforme, échelon de température à l'entrée) avec ξ = h·a_v·A·x/(ṁ·c_f) et η = h·a_v·t/((1−ε)·ρ_s·c_s) :
θ_f = J(ξ, η), θ_s = 1 − J(η, ξ), où J(x, y) = 1 − e^(−y)·∫₀ˣ e^(−τ)·I₀(2√(yτ)) dτ et θ = (T − T_initial)/(T_entrée − T_initial).

**Niveau.** Loi fondamentale (bilans d'énergie de l'air et du solide) + corrélation pour h.

**D'où elle vient.** Bilan d'énergie sur une tranche de lit : l'air perd ce que les cailloux gagnent, proportionnellement à l'écart de température et à la surface de contact.

**Hypothèses et validité.** Écoulement uniforme sur la section (pas de passage préférentiel le long des parois) ; température uniforme dans chaque caillou (corrigée par Jeffreson, F27) ; pas de conduction axiale ni de pertes dans la solution exacte (ajoutées dans le schéma, F29). Tola utilise le même modèle (sa réf. [29–30]).

**Pourquoi.** C'est le modèle standard des lits de roches, et il a une solution exacte qui permet de **vérifier le code** (test `test_convergence_vers_schumann` : erreur < 1 % avec 80 cellules). Alternative : une cuve « bien mélangée » à une seule température (n_cellules = 1), gardée pour l'explication : elle laisse sortir l'air tiède tout de suite, sans front.

**Exemple à la main.** Vitesse du front : la chaleur apportée par l'air par seconde, ṁ·c_f, remplit le lit à raison de (1−ε)·ρ_s·c_s·A par mètre. Pour Dormoy (0,052 kg/s, cuve de 0,5 m) : v = 0,052 × 1006 / (0,7 × 2750 × 900 × 0,196) = 52,3 / 339 800 = **0,154 mm/s**, soit 0,55 m par heure. Une cuve de 2 m se remplit de chaleur en 3,6 h ; pendant ce temps l'air ressort froid. Pour Tola (12,3 kg/s, cuve de 5,2 m) : 12 370 / (1,73·10⁶ × 21,2) = 0,34 mm/s, 10,4 m en 8,5 h : la charge de 6 h ne remplit que les deux tiers, d'où la « sortie constante pendant les deux tiers ».

**Source.** `schumann1929` ; Tola 2022 § 2.3 ; `caes/lit_gravier.py`, `solution_schumann`.

---

## F26 : schéma numérique cellule par cellule (NTU et relaxation exacte)

**En bref.** L'ordinateur découpe la cuve en tranches (40 à 160). À chaque pas de temps, il fait passer l'air de tranche en tranche : dans chacune, l'air se rapproche de la température des cailloux (plus l'échange est bon, plus il s'en rapproche), et les cailloux se réchauffent de ce que l'air a perdu. Comme on utilise la formule exacte du « rapprochement » plutôt qu'une approximation, le schéma ne peut jamais exploser, même avec de grands pas de temps, et l'énergie est conservée au joule près.

**Formule.** Pour une cellule de capacité C = (1−ε)·ρ_s·c_s·A·Δx, avec l'air entrant à T_in et le solide à T_s :
- NTU = h·a_v·A·Δx/(ṁ·c_f), efficacité e = 1 − exp(−NTU) ;
- constante de temps τ = C/(ṁ·c_f·e) ;
- nouveau solide : T_s' = T_s + (T_in − T_s)·(1 − exp(−Δt/τ)) ;
- chaleur reçue Q = C·(T_s' − T_s) ; air sortant moyen : T_out = T_in − Q/(ṁ·c_f·Δt).
Sens = +1 : l'air entre en haut (charge) ; −1 : par le bas (décharge).

**Niveau.** Méthode numérique (volumes finis, intégration exacte par cellule).

**D'où elle vient.** Dans une cellule à T_s constant, l'air sort à T_s + (T_in − T_s)·e^(−NTU) (échangeur à un seul fluide capacitif). En supposant T_in constant pendant Δt, le solide suit une exponentielle exacte.

**Hypothèses et validité.** Erreur d'ordre Δx (l'air est supposé « voir » le solide de la cellule entière) : elle décroît comme 1/n (test `test_convergence_vers_schumann`). Le pas de temps n'est limité que par la précision voulue (60 s pour Tola, 10 s pour Dormoy).

**Pourquoi.** Un schéma explicite classique exigerait Δt < Δx/u_air ≈ 0,1 s : 20 cycles de Tola prendraient des heures. Ici, 3 minutes.

**Exemple à la main.** Cuve de Dormoy, 40 cellules de 5 cm : C = 1,73·10⁶ × 0,196 × 0,05 = 17 000 J/K. h = 33 W/m²K, a_v = 140 m²/m³ : NTU = 33 × 140 × 0,196 × 0,05/(0,052 × 1006) = 45,3/52,3 = 0,87, e = 0,58. τ = 17 000/(52,3 × 0,58) = 560 s. Avec Δt = 10 s, le solide fait 1,8 % du chemin vers T_in à chaque pas.

**Source.** Convention du projet ; `LitGravier.pas`.

---

## F27 : coefficient d'échange air-cailloux (Wakao) et correction de Jeffreson

**En bref.** À quelle vitesse la chaleur passe-t-elle de l'air aux cailloux ? Ça dépend de la vitesse de l'air (plus il va vite, mieux il « frotte » les cailloux) et de la taille des cailloux. La corrélation de Wakao, ajustée sur des centaines d'essais, donne la réponse. Et comme un gros caillou chauffe d'abord en surface, Jeffreson corrige un peu vers le bas.

**Formule.**
- Re = ρ_f·u_s·d/μ (vitesse superficielle u_s = ṁ/(ρ_f·A)), Pr = μ·c_f/k_f ;
- Nu = 2 + 1,1·Re^0,6·Pr^(1/3) (Wakao et al. 1979), h = Nu·k_f/d ;
- Bi = h·d/(2·k_s) ; h_eff = h/(1 + Bi/5) (Jeffreson 1972).

**Niveau.** Corrélations empiriques.

**D'où elle vient.** Wakao : réanalyse des mesures d'échange dans des lits de particules en tenant compte de la dispersion ; valable pour 15 < Re < 8500. Jeffreson : comparaison du modèle à une seule température par particule avec le modèle à conduction interne.

**Hypothèses et validité.** Particules à peu près sphériques ; 15 < Re < 8500 (le code signale la sortie de plage : à 50 bar chez Dormoy, Re ≈ 10, Nu → 2, conduction pure) ; Bi < 1 pour que la correction suffise (Bi ≈ 0,2 chez Dormoy, 0,5 chez Tola). Les propriétés de l'air (ρ, μ, k, cp) viennent de CoolProp à la pression de la cuve.

**Pourquoi.** Corrélation de référence des lits fixes, citée partout. Alternative : Gunn (1978), équivalente dans cette plage.

**Exemple à la main (Dormoy, 3 bar, 170 °C).** ρ_f = 2,36 kg/m³, μ = 2,5·10⁻⁵ Pa·s, k_f = 0,036 W/mK, u_s = 0,052/(2,36 × 0,196) = 0,112 m/s. Re = 2,36 × 0,112 × 0,03/2,5·10⁻⁵ = **317**. Pr ≈ 0,70. Nu = 2 + 1,1 × 317^0,6 × 0,888 = 2 + 1,1 × 31,6 × 0,888 = **32,9**. h = 32,9 × 0,036/0,03 = **39 W/m²K**. Bi = 39 × 0,03/(2 × 2,5) = 0,23 ; h_eff = 39/1,047 = **38 W/m²K**.

**Source.** `wakao1979`, `jeffreson1972` ; `lit.wakao.*`, `lit.jeffreson.facteur` ; `coefficient_echange`.

---

## F28 : perte de charge d'Ergun

**En bref.** Pousser de l'air à travers un tas de cailloux demande une petite surpression, comme souffler dans une paille remplie de billes. Ergun a mesuré cette perte de pression : une partie vient du frottement visqueux (proportionnelle à la vitesse), l'autre des tourbillons (proportionnelle au carré de la vitesse). Pour Dormoy, c'est négligeable : moins de 100 Pa, alors que le compresseur fournit 3 à 50 bar.

**Formule.** Δp/L = 150·μ·(1−ε)²·u_s/(ε³·d²) + 1,75·ρ_f·(1−ε)·u_s²/(ε³·d).

**Niveau.** Corrélation empirique.

**D'où elle vient.** Ergun et Orning (1949), puis Ergun (1952) : mesures sur des colonnes de particules, interpolation entre le régime visqueux (Kozeny-Carman) et le régime inertiel (Burke-Plummer).

**Hypothèses et validité.** 1 < Re_p < 2500 environ ; particules de taille uniforme ; pas d'effet de paroi (D/d > 10 : 17 chez Dormoy, 173 chez Tola).

**Pourquoi.** Formule standard, demandée par le plan pour répondre à « la perte de charge dans le gravier coûte-t-elle de l'énergie au compresseur ? » Réponse : non (5 à 90 Pa).

**Exemple à la main (Dormoy, 3 bar).** u_s = 0,112 m/s, ε = 0,3, d = 0,03 m, L = 2 m. Visqueux : 150 × 2,5·10⁻⁵ × 0,49 × 0,112/(0,027 × 9·10⁻⁴) = 2,06·10⁻⁴/2,43·10⁻⁵ = 8,5 Pa/m. Inertiel : 1,75 × 2,36 × 0,7 × 0,0125/(0,027 × 0,03) = 0,0361/8,1·10⁻⁴ = 44,6 Pa/m. Total **53 Pa/m, soit 106 Pa pour 2 m** (le code : 89 Pa, propriétés exactes).

**Source.** `ergun1949` ; `lit.ergun.A`, `lit.ergun.B` ; `perte_de_charge_ergun`.

---

## F29 : conduction axiale et pertes latérales du lit

**En bref.** Pendant l'attente (le transport), deux choses abîment le stock de chaleur : la chaleur s'étale du haut chaud vers le bas froid à travers les cailloux (le front se floute), et elle fuit à travers l'isolant vers l'extérieur. La première ne perd pas d'énergie mais la rend moins utile (plus tiède) ; la seconde la perd.

**Formule.**
- conduction : (1−ε)·ρ_s·c_s·∂T_s/∂t = k_eff·∂²T_s/∂x², avec k_eff = (1−ε)·k_s (hypothèse simple : conduction par le squelette solide seulement) ; schéma explicite sous-cyclé pour respecter Δt < 0,4·Δx²/α ;
- pertes : chaque cellule cède U·π·D·Δx·(T_s − T_amb) à travers la paroi, intégré exactement sur le pas (relaxation exponentielle). U est le coefficient global de l'isolant, fourni par le futur module `isolation` (phase 6) ; U = 0 : isolation parfaite.

**Niveau.** Loi fondamentale (conduction de Fourier) + hypothèse sur k_eff + paramètre d'isolation.

**D'où elle vient.** Loi de Fourier dans le solide ; bilan de la paroi latérale.

**Hypothèses et validité.** k_eff = (1−ε)·k_s est une borne basse (les contacts entre cailloux conduisent mal, l'air immobile presque pas) ; la conduction compte peu (α ≈ 10⁻⁶ m²/s : 1 cm par heure, 30 cm en semaine). Pertes par le haut et le bas négligées pour l'instant.

**Pourquoi.** Nécessaire pour la phase 6 (attente de 7 à 56 jours) ; sans conduction, un profil en marche resterait net pour toujours, ce qui est faux.

**Exemple à la main.** Distance de diffusion en 14 jours : √(α·t) = √(10⁻⁶ × 1,2·10⁶) = **1,1 m**. Le front d'une cuve de 2 m s'étale donc sur toute la hauteur en deux semaines : la chaleur reste là, mais à une température moyenne plus basse. C'est l'« effet de fin de décharge » que la phase 6 chiffrera.

**Source.** Convention du projet ; `materiau.gravier_tola.conductivite` (hypothèse) ; `LitGravier.pas`.

---

## F30 : couplage des cuves au banc (charge, bypass, pincement)

**En bref.** En charge, l'air chaud qui sort d'un étage de compression traverse sa cuve de gravier avant le radiateur : la cuve prend ce qu'elle peut, le radiateur finit le travail. En décharge, l'air froid qui sort du détendeur traverse la cuve en sens inverse et en ressort chaud avant d'entrer dans la turbine. Si la cuve est plus chaude que nécessaire, une vanne de bypass mélange de l'air froid pour viser exactement la température de la turbine : on ne gaspille pas la chaleur, on la garde pour plus tard. Si la cuve est trop froide, la turbine reçoit de l'air trop froid et produit moins : il n'y a pas d'appoint magique.

**Formule.**
- Charge, étage i : T_entrée,cuve = T_sortie,compresseur − δ ; la cuve rend T_sortie,cuve (F26) ; T_entrée,refroidisseur = T_sortie,cuve + δ (jamais plus que T_sortie,compresseur).
- Décharge, turbine i ← cuve n−i+1 : T_plein = sortie de la cuve si tout le débit la traverse, moins δ ; fraction de bypass f = (T_plein − T_cible)/(T_plein − T_avant) bornée à [0, 1[ ; débit dans la cuve ṁ·(1−f) ; T_turbine = f·T_avant + (1−f)·(T_sortie,cuve − δ), plafonnée à T_cible.
- δ = 0 pour le gravier direct (D) ; δ = 20 K par échangeur pour la boucle d'air (E).

**Niveau.** Convention de modélisation (bilan de mélange) + paramètre δ (Tola, tableau 2).

**D'où elle vient.** Mélange adiabatique de deux débits d'air à la même pression ; pincement minimal d'un échangeur air-air à contre-courant équilibré (les deux débits ont la même capacité thermique, donc l'écart est constant le long de l'échangeur).

**Hypothèses et validité.** Pas de perte de charge dans les échangeurs ; le bypass suppose que la sortie de la cuve ne change pas quand le débit baisse (vrai à quelques degrés près : la cuve a un NTU élevé). L'air comprimé traverse la cuve à la pression de l'étage (D) ; dans E, la boucle est à 1 bar et transporte le même débit massique que l'air comprimé (échangeur équilibré).

**Pourquoi.** C'est ce qui fait que D et E produisent autant que C : la température d'entrée des turbines est régulée, comme dans toute installation réelle. Alternative : laisser la turbine recevoir toute la chaleur de la cuve (plus de puissance au début, cuve vide plus tôt) ; non retenue parce que la fiche DEPRAG ne donne pas de limite de température.

**Exemple à la main.** Cuve 3 à 188 °C en haut, air du détendeur à −10 °C, cible 130 °C : f = (188 − 130)/(188 + 10) = 0,29. 29 % de l'air contourne la cuve, 71 % la traverse ; le mélange sort à 130 °C et la cuve se vide 29 % moins vite.

**Source.** Convention du projet ; Tola 2022, tableau 2 (pincement 20 °C pour l'air) ; `caes/integre.py`, `CouplageCuvesCharge`, `RechauffeurCuves`.

---

## F31 : exergie d'un lit de gravier

**En bref.** Comme pour l'air (F21), on peut calculer ce qu'un tas de cailloux chauds « vaut » en travail : plus ils sont chauds par rapport à l'air ambiant, plus ils valent, mais avec le même facteur de Carnot qui pénalise la chaleur tiède. Ça permet de mettre les cuves dans le tableau « 1000 unités » : exergie stockée en charge, exergie puisée en décharge, et la différence détruite dans les échanges air-gravier.

**Formule.** Ex = Σ_cellules C · [(T − T₀) − T₀ · ln(T/T₀)], avec C la capacité thermique du solide d'une cellule [J/K]. Nulle à T = T₀, positive sinon (y compris pour une cuve plus froide que l'ambiant).

**Niveau.** Loi fondamentale (exergie d'un corps incompressible).

**D'où elle vient.** Travail maximal d'un solide de capacité C ramené de T à T₀ par un moteur de Carnot : ∫ C (1 − T₀/T') dT'.

**Hypothèses et validité.** Le gravier est un solide incompressible à capacité constante ; l'air interstitiel est négligé.

**Pourquoi.** Permet de fermer le bilan d'exergie de la charge (entrée = pertes + stock dans l'air + stock dans les cuves) et de la décharge (entrée = stock de l'air + exergie puisée dans les cuves). Les tests `test_D_bilan_d_exergie_ferme` vérifient la fermeture à 1–2 %.

**Exemple à la main.** 500 kg de gravier (C = 450 kJ/K) à 180 °C (453 K), ambiant 293 K : Ex = 450 × [(453 − 293) − 293 × ln(453/293)] = 450 × [160 − 293 × 0,4357] = 450 × 32,3 = **14,5 MJ = 4,0 kWh**, pour 20 kWh de chaleur stockée : la chaleur à 180 °C vaut 20 % de son énergie en travail.

**Source.** Thermodynamique classique ; `caes/integre.py`, `exergie_cuve`.

---

## Modèle de fiche

```markdown
## Fnn : nom de la formule

**En bref.** 3 ou 4 phrases sans jargon, avec une analogie de la vie courante.

**Formule.** L'équation, avec chaque symbole et son unité.

**Niveau.** Loi fondamentale / modèle physique classique / corrélation empirique / paramètre mesuré ou calibré.

**D'où elle vient.** Démonstration résumée, ou l'expérience sur laquelle elle a été ajustée.

**Hypothèses et validité.** Ce qu'elle suppose, son domaine, et comment le code vérifie qu'on y reste.

**Pourquoi.** Pourquoi cette formule plutôt qu'une autre (en nommer au moins une).

**Exemple à la main.** Calcul chiffré refaisable à la calculatrice.

**Source.** Référence au registre (id de `references.csv`, section ou équation).
```
