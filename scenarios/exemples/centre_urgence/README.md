# Scénario 3 : centre d'urgence à demande variable

**La question.** Un centre d'urgence consomme 100 kW en moyenne pendant 72 h (7,2 MWh), plus le jour que la nuit. Combien de modules d'air comprimé chargés d'avance faut-il pour le tenir, que pèsent-ils, et comment se comparent-ils à des batteries en conteneur et à une génératrice diesel ? Qu'est-ce qu'il faudrait pour que l'air comprimé soit viable ici ?

**Les fichiers** (générés par `../generer_exemples.py`) :

| Fichier | Contenu |
|---|---|
| `module.yaml` | un module = l'installation de transport (D isolée) chargée la veille (attente d'un jour), déchargée à débit nominal : sa courbe de puissance sert à la flotte |
| `demande_72h.csv` | demande du centre au pas d'une minute : 120 kW de 6 h à 22 h, 60 kW la nuit (`centre_urgence.facteur_jour / facteur_nuit`, **hypothèses** ; à remplacer par un profil mesuré, par exemple des données ouvertes de bâtiment) |

**La méthode** (`caes/flotte.py`, fiche F47). La flotte est pilotée seconde par seconde comme la vanne ON/OFF de Zhang S. (2025) : on démarre un module quand la puissance en marche ne couvre pas la demande, on en met un en pause quand l'excédent dépasse la puissance d'un module, le reste est écrêté. Le nombre de modules est le plus petit qui fournit 99,9 % de l'énergie demandée. Le réservoir tampon et la régulation fine de Zhang ne sont pas modélisés : un module est un bloc de puissance.

**Les comparaisons** viennent du registre : fiche Tesla Megapack (2020 : 3 080 kWh, 770 kW, 25,4 t, 90 %), fiche Caterpillar D100 GC (2020 : 100 kW, 16,7 à 27,9 L/h), projections de coût NREL 2023 (245 à 403 $/kWh en 2030), coût des réservoirs hors sol cité par Dormoy d'après Bazdar (200 à 250 $/kWh). Les coûts sont des ordres de grandeur, pas un devis.

**Régénérer.**

```
python rapports/scenarios_centre_urgence.py        # → rapports/scenarios/centre_urgence.md, deux figures (≈ 1 min)
```

**Comment lire la réponse.** Le résultat est négatif et présenté comme tel : le nombre de modules se compte en centaines, la masse en centaines de tonnes. La section « qu'est-ce qu'il faudrait » donne les facteurs à gagner (électricité par tonne, par mètre cube, rendement) et ce que les leviers connus du simulateur peuvent apporter. La masse d'un module ne compte que les bouteilles (F44) et le gravier : compresseur, turbine et échangeurs manquent, le vrai chiffre est plus lourd.
