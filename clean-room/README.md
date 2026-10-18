# Clean-room rebuild — REA × JEV

Ce dossier applique le workflow « clean room » : on reconstruit une
fonctionnalité **sans que l'équipe qui écrit le nouveau code ait vu
l'original**.

```
REA (room A) ──SPEC.md──► JEV (spec gate) ──SPEC validé──► Opus (room B) ──► Haiku : tests + 3 versions cassées
     ▲                        │      ▲                                              │
     └── règle sans preuve ───┘      └──────────── questions / points flous ◄───────┘
                                    boucle /goal : tant que les 3 versions cassées ne sont pas toutes détectées
```

| Rôle | Fichier | Voit l'original ? | Écrit le nouveau code ? |
|---|---|---|---|
| REA — lit et décrit | [`agents/rea.md`](agents/rea.md) | oui | jamais |
| JEV — juge les preuves, route les questions | [`agents/jev.md`](agents/jev.md) | oui (pour vérifier) | jamais |
| Room B — reconstruit (Opus) | [`agents/rebuilder.md`](agents/rebuilder.md) | **jamais** | oui |
| Tests + mutants (Haiku) | [`agents/tester.md`](agents/tester.md) | **jamais** | tests uniquement |

## Premier cas : `base_iban` (Odoo 18.0)

Cible : la logique IBAN/BBAN du module Odoo Community `base_iban`
(commit `1f2b50a`, LGPLv3) — normalisation, validation par pays, checksum
MOD 97-10, affichage, extraction du BBAN, type de compte.

| Dossier | Contenu |
|---|---|
| [`base_iban/room_a/`](base_iban/room_a) | `SPEC.md` complet de REA (avec preuves `fichier:ligne`) et `evidence/` : traces d'exécution et harnais (faux paquet `odoo` pour charger l'original **non modifié**). |
| [`base_iban/gate/`](base_iban/gate) | `JEV_REPORT.md` (verdicts des 3 tours) et les scripts de vérification de JEV. |
| [`base_iban/room_b/`](base_iban/room_b) | Ce que la room B a reçu (`SPEC.md` sans preuves ni références à l'original), la reconstruction `iban.py`, les tests, les 3 mutants, `QUESTIONS.md` / `ANSWERS.md`. |
| [`base_iban/final_check/`](base_iban/final_check) | Comparaison différentielle original ↔ reconstruction, faite **après** la reconstruction. |
| [`base_iban/LOG.md`](base_iban/LOG.md) | Journal de la session, tour par tour. |

### Résultat

- `room_b/run_checks.py` : **GOAL MET** — 74 tests, 0 ignoré ; la
  reconstruction passe, les 3 mutants échouent (longueur, normalisation,
  checksum), sur le comportement et non sur une erreur d'import.
- Comparaison différentielle : **0 écart** sur 60 006 entrées × 4 fonctions
  (dont 15 303 IBAN valides, avec bruit Unicode, minuscules, séparateurs).

### Rejouer

```sh
# Room B (ne nécessite pas Odoo)
cd clean-room/base_iban/room_b && python3 run_checks.py

# Room A et contrôle final (nécessitent les sources d'Odoo 18.0)
git clone --depth 1 -b 18.0 https://github.com/odoo/odoo.git /path/odoo
export ODOO_SRC=/path/odoo
cd clean-room/base_iban/room_a/evidence/harness && python3 -I -B trace.py && python3 -I -B trace_rev2.py
cd clean-room/base_iban/final_check && python3 -I -B diff_fuzz.py
```

`gate/jev_tools/trace_rev3.py` s'exécute depuis `room_a/evidence/harness/`
(il réutilise les stubs `stubs_rev2/`).

## Appliquer à une autre fonctionnalité

1. Choisir un périmètre petit et testable sans serveur complet.
2. Placer les sources originales **hors du dépôt** (dossier temporaire), lancer
   REA avec `agents/rea.md`.
3. JEV contrôle chaque règle ; celles sans preuve retournent à REA. JEV produit
   le `SPEC.md` de la room B (sans preuves ni chemins vers l'original).
4. Lancer une **session neuve** pour la room B, avec ce seul `SPEC.md` dans son
   dossier.
5. Tests + 3 mutants, `run_checks.py` ; les questions repassent par JEV.
6. Boucler jusqu'à « GOAL MET » avec 0 test ignoré, puis faire la
   comparaison différentielle.

## Limites (à lire)

- **Isolation par consigne, pas par sandbox.** Les agents de la room B
  tournaient dans le même conteneur que les sources ; l'isolation reposait sur
  leurs instructions et sur des dossiers séparés. Pour une vraie barrière,
  lancer la room B dans un conteneur/session distinct qui ne reçoit que
  `SPEC.md`.
- **Contamination par l'entraînement.** Odoo est open source : les modèles ont
  pu le voir pendant leur entraînement. La consigne interdit de reproduire de
  mémoire, mais cela ne peut pas être prouvé.
- **Noms d'API.** `normalize_iban`, `validate_iban`, `pretty_iban`,
  `get_bban` reprennent des noms publics de l'original (choix assumé pour la
  compatibilité ; aucun comportement n'en dépend).
- **Juridique.** Une clean room réduit le risque, elle ne l'annule pas. Ici le
  code source est LGPLv3 ; pour un logiciel propriétaire, vérifier licence et
  CGU avant toute analyse.
- Points déclarés **non spécifiés** (non testés) : modification en place de la
  liste des types, doublons `iban`, entrées non textuelles (R18, informatif).
