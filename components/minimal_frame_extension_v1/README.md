# ZORAN — Minimal Frame Extension v1

OBJECT_ID: `ZORAN-BRICK-MIN-FRAME-EXT-V1`  
META_ID: `ZORAN-META-FRAME-MOTION-2026-08-24`  
STATUS: `CANDIDATE / NON_CERTIFIÉ`  
DATE: `2026-08-24`  
BRANCH: `codex/minimal-frame-extension-v1`

## But

Formaliser le passage déterministe suivant :

`blocage dans C_n -> diagnostic -> candidats C_(n+1) -> contrôle de conservation -> sélection minimale`

Le module distingue explicitement :

- `IMPOSSIBLE_DANS_CADRE`
- `EXTENSION_COHERENTE_EXISTE`
- `NON_MESURÉ`
- `IMPOSSIBLE_GLOBAL`

`IMPOSSIBLE_GLOBAL` est interdit tant que l'espace de recherche n'est pas déclaré exhaustif et accompagné d'identifiants de preuve d'exhaustivité.

## Origine des briques retrouvées

Le dépôt déterministe contient déjà :

1. `components/k3_frame_algebra_v1_1/moteur_algebre_cadres.py` avec `cout_de_contrainte(...)`, qui identifie une contrainte `BLOQUANTE` ou `INCERTITUDE_CRITIQUE` mais ne choisit pas d'extension de cadre.
2. `components/nl_k3_boundary_v1/boundary.py`, qui impose une frontière stricte entre observations sémantiques et autorité K3 et bloque les cadres candidats non évalués.

Cette brique ne modifie pas `zorania2025/Zoran-IA-deteriniste`. Elle est déposée ici comme couture candidate réutilisable.

## Invariants

Une extension candidate n'est admissible que si :

- la contrainte cible passe à `PASS` ;
- tous les cadres inférieurs explicitement requis restent `PASS` ;
- tous les cadres pairs explicitement requis restent `PASS` ;
- tous les bénéfices des cadres supérieurs explicitement requis sont `PASS` ;
- aucun de ces cadres n'est absent ;
- aucun n'est `NON_MESURÉ` ;
- aucune régression n'est tolérée ;
- des identifiants de preuve causale existent ;
- des falsificateurs existent.

Le choix parmi les candidats admissibles est déterministe :

1. `complexity_cost` minimal ;
2. `frame_id` lexical pour départager une égalité.

## Guards

- `FAIL` sur un cadre préservé, pair ou supérieur : blocage.
- `NON_MESURÉ` ou cadre manquant : blocage de promotion.
- absence de preuve causale : exception.
- absence de falsificateur : exception.
- `IMPOSSIBLE_GLOBAL` sans preuve d'exhaustivité : impossible.
- aucune autorité sémantique implicite : les candidats sont fournis à la brique, pas inventés par elle.

## Rollback

La brique est isolée sur branche dédiée. Rollback = suppression/rejet de la branche `codex/minimal-frame-extension-v1`. Aucun fichier de `main` n'est modifié par cette candidature.

## Tests

Commande :

`python -m unittest -v test_frame_extension.py`

Résultat du run de construction : `7/7 PASS`.

Cas couverts : sélection minimale, régression bloquante, NON_MESURÉ bloquant, preuve d'exhaustivité, cadre courant NON_MESURÉ, hash sémantique déterministe, cadre supérieur absent.

## Limites

La brique ne découvre pas elle-même les cadres candidats. Elle sélectionne et contrôle des extensions proposées par une couche amont. La recherche sémantique de nouveaux cadres, la preuve physique/métier de causalité et le calcul d'un score S global restent hors scope.

## Certification

Verdict actuel : `CANDIDATE / NON_CERTIFIÉ`.

Raison : les tests unitaires locaux passent, mais la couture bout-en-bout avec le runtime, ZMOS, K3, moteur sémantique et campagnes adversariales massives n'a pas été rejouée dans ce tour. Le bénéfice multicadre global et S > 9 restent `NON_MESURÉ`.
