# ZORAN — Minimal Frame Extension v1

OBJECT_ID: `ZORAN-BRICK-MIN-FRAME-EXT-V1`  
META_ID: `ZORAN-META-FRAME-MOTION-2026-08-24`  
STATUS: `CANDIDATE / NON_CERTIFIÉ`  
DATE: `2026-08-24`  
BRANCH: `codex/minimal-frame-extension-v1`

## But

Formaliser la chaîne déterministe :

`verdicts K3 -> frontière bloquante -> candidats de cadres -> évaluations déterministes -> contrôle de conservation -> extension minimale`

Le module distingue : `IMPOSSIBLE_DANS_CADRE`, `EXTENSION_COHERENTE_EXISTE`, `NON_MESURÉ`, `IMPOSSIBLE_GLOBAL`.

`IMPOSSIBLE_GLOBAL` est interdit tant que l'espace de recherche n'est pas déclaré exhaustif et accompagné d'identifiants de preuve d'exhaustivité.

## Briques préexistantes retrouvées

Le dépôt déterministe contient déjà :

1. `components/k3_frame_algebra_v1_1/moteur_algebre_cadres.py` : `cout_de_contrainte(...)` identifie une contrainte bloquante ou inconnue critique.
2. `components/nl_k3_boundary_v1/boundary.py` : frontière stricte entre observations sémantiques et autorité K3.
3. `components/complex_nl_intent_v1/intent.py` : génération déterministe de `candidate_frame_ids` depuis l'intention.
4. `SEMANTIC_ENGINE_POLICY_V1.md` : les moteurs sémantiques ne peuvent produire que des candidats/observations ; K3 reste autoritaire.
5. `components/zoran_chat_runtime_v1/runtime.py` : les cadres non supportés deviennent `NON_MESURÉ`, sans invention de verdict.

Aucun de ces éléments ne réalisait le déplacement minimal de cadre complet.

## Nouvelle couture : FRAME-SEARCH-STITCH

`frame_search_stitch.py` ajoute trois étapes :

1. `detect_blocking_boundary(...)` choisit de façon déterministe la première frontière bloquante : `FAIL` avant `NON_MESURÉ`, puis ordre lexical.
2. `discover_candidate_frames(...)` filtre des observations de cadres qui déclarent explicitement pouvoir lever cette contrainte. Chaque observation exige `source_id` et `source_sha256`.
3. `build_extension_candidates(...)` refuse toute promotion tant qu'un évaluateur déterministe n'a pas fourni les verdicts K3, preuves causales et falsificateurs.

La découverte n'a jamais d'autorité de décision :

`Internet / corpus / embedding -> observation scellée -> évaluation déterministe -> K3 -> extension minimale`

Une frontière `NON_MESURÉ` ne déclenche aucune invention de cadre : elle reste `NON_MESURÉ` jusqu'à mesure.

## Invariants de l'extension

Une extension candidate n'est admissible que si :

- la contrainte cible passe à `PASS` ;
- tous les cadres inférieurs explicitement requis restent `PASS` ;
- tous les cadres pairs explicitement requis restent `PASS` ;
- tous les bénéfices supérieurs requis sont `PASS` ;
- aucun cadre requis n'est absent ou `NON_MESURÉ` ;
- aucune régression n'est tolérée ;
- des preuves causales et falsificateurs existent.

Le choix est déterministe : `complexity_cost` minimal, puis `frame_id` lexical.

## Cas racine de -1

Le test dédié encode :

`REAL::SQRT_NEGATIVE = FAIL -> observation MATH::COMPLEX -> évaluation déterministe -> cible PASS + préservation réel/arithmetic + bénéfice solvabilité -> candidat admissible`.

Le test ne prétend pas que la mathématique des complexes est prouvée par le code ; il prouve que la mécanique Zoran de changement de cadre respecte la séparation observation / preuve / décision.

## Tests exécutés

- Minimal Frame Extension : `7/7 PASS`.
- Frame Search Stitch : `10/10 PASS`.
- Total des deux runs de construction : `17 PASS / 0 FAIL`.
- Rejeu d'un checkout complet de la branche : `NON_MESURÉ` dans ce tour.
- Runtime global, ZMOS, campagnes adversariales massives, recherche Internet live et `S > 9` : `NON_MESURÉ`.

## Guards

- `FAIL`, régression, absence de preuve ou cadre requis manquant : blocage.
- `NON_MESURÉ` : blocage de promotion.
- source externe sans SHA-256 : rejet.
- découverte sémantique : aucune autorité de vérité ou de décision.
- `IMPOSSIBLE_GLOBAL` : preuve d'exhaustivité obligatoire.

## Rollback

La brique reste isolée sur `codex/minimal-frame-extension-v1`. `main` n'est pas modifié. Rollback : rejet/suppression de la branche candidate.

## Certification

Verdict : `CANDIDATE / NON_CERTIFIÉ`.

La prochaine condition de promotion est un contre-audit puis un rejeu bout-en-bout sur une copie exécutable du runtime avec sources scellées, K3, conservation multicadre et campagnes adversariales. Tant que le bénéfice causal multicadre et `S > 9` ne sont pas mesurés, ils restent `NON_MESURÉ`.
