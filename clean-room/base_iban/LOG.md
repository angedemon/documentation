# Journal — clean room `base_iban`

| Étape | Agent | Résultat |
|---|---|---|
| 1 | orchestrateur | Sparse-checkout d'Odoo 18.0 (`1f2b50a`), `addons/base_iban` seulement, hors dépôt. L'orchestrateur ne lit pas l'original. |
| 2 | REA (room A) | SPEC rév. 1 : 17 règles, toutes avec preuve. R15 repose en partie sur un stub. 5 traces. |
| 3 | JEV (gate) | 16 pass, R15 scindée : R15a pass, **R15b fail → REA** (valeurs issues du stub). Fuites réécrites (regex, étapes du checksum, noms internes). Cas Kelvin (U+212A) relevé. |
| 4 | Opus (room B) | `iban.py` depuis SPEC seul. 17 règles, 7 questions. |
| 4' | REA (room A) | En parallèle : rév. 2 avec `base/models/res_bank.py` → R15b prouvée (`'bank'`), R4a (Kelvin), R16a, R18. |
| 5 | Haiku | 54 tests (6 ignorés), 3 mutants. GOAL MET — mais ignorés = trous de couverture. 4 nouvelles questions. |
| 6 | JEV (gate + routage) | Rév. 2 : 0 fail. R16a/R18 = notes informatives (comportement de l'hôte). Noms d'API fixés, 11 réponses. |
| 7 | Opus (room B) | Mise à jour rév. 2 (R4a, API fixée). |
| 8 | Haiku | 74 tests, **0 ignoré**, mutants régénérés. GOAL MET. Question 12 (Kelvin + paire hors table). |
| 9 | JEV (routage) | Q12 vérifiée sur l'original (126 entrées) : message pays confirmé. SPEC rév. 2.1. |
| 10 | orchestrateur | `run_checks.py` relancé : GOAL MET, kills comportementaux. Différentiel original ↔ rebuild : **0 écart / 60 006 entrées**. |
