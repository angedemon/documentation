# Tests + 3 versions cassées (modèle : Haiku)

Tu es côté room B : tu n'as accès qu'à `SPEC.md` et à la reconstruction.

## 1. Tests
Écris `tests/test_*.py` (`unittest`, stdlib uniquement) dérivés de `SPEC.md` :
au moins un test par règle, nommé `test_R<n>_...`, avec les exemples du SPEC.
La reconstruction doit **passer** tous les tests.

## 2. Trois versions cassées
Crée `mutants/m1.py`, `m2.py`, `m3.py` : chacune est une copie de la
reconstruction avec **un seul** bug réaliste et ciblé (par exemple une borne
décalée, une étape de normalisation oubliée, une branche d'erreur inversée).
Documente chaque mutant dans `mutants/README.md` (règle visée, bug introduit).

## 3. Exécution
Lance `run_checks.py` : les tests doivent passer sur la reconstruction et
**échouer** sur chacun des 3 mutants. Si un mutant survit, c'est que les tests
sont trop faibles : renforce les tests (jamais en affaiblissant le mutant) et
relance.

Si un test révèle une ambiguïté du SPEC, ne tranche pas : note-la dans
`QUESTIONS.md` pour JEV.
