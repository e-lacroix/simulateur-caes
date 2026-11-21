# Matériaux de stockage de chaleur

Les propriétés sont dans le registre (`data/registre/parametres.csv`), sous les identifiants `materiau.<nom>.<propriete>`, pour garder une seule source de vérité. Le module `caes/materiaux.py` les assemble :

```python
from caes.materiaux import charger_materiau
gravier = charger_materiau("gravier_tola")
```

| Matériau | Propriétés | Source | Niveau |
|---|---|---|---|
| `gravier_tola` | 2750 kg/m³, 900 J/(kg·K), particules de 3 cm, porosité 0,3 | Tola 2022, tableau 3 | simulation publiée |
| … conductivité | 2,5 W/(m·K) | Robertson 1988 (USGS, roches silicatées) | hypothèse |

Pour ajouter une roche : ajouter ses lignes dans `generer_registre_phase0.py` avec une source vérifiée (DOI ou URL), puis régénérer le registre.
