# Mutants (room B, round 2)

Each file is a full copy of the round-2 `iban.py` with exactly one line changed.
`run_checks.py` must report each one as killed by `tests/test_iban.py`.

| File | Rule | Bug introduced | Changed line |
|---|---|---|---|
| `m1.py` | R5 (length), with R7 | The length check only rejects too-long values: `!=` became `>`, so a value one character too short is no longer rejected. | `validate_iban`, the R5 length condition |
| `m2.py` | R2 (normalize before validation) | Validation strips only spaces and skips the R1 normalization, so `-`, `.`, `/`, `(`, `)`, `!`, `_` and tabs or newlines are no longer ignored. | `validate_iban`, the `# R2` line |
| `m3.py` | R9 (MOD 97-10 checksum) | Letter values are off by one (A = 11 instead of 10), so every IBAN containing a letter in the rearranged value gets the wrong remainder. | `_checksum_ok`, the letter-to-digits line |

Kill results (round 2, `unittest` on the 74 tests, unique failing test ids): m1 fails 5 (R5, R7, R10). m2 fails 7 (R2, R3, R10, R12, R16). m3 fails 23 (R2, R4, R4a, R5, R8, R9, R11, R12, R15, R16, R17). All kills are behavioral, with no import errors.

Extra check, not part of `mutants/` or `run_checks.py`: an R4a mutant that
drops the KELVIN SIGN mapping (`pair = compact[:2]`) is killed by
`test_R4a_kelvin_in_country_position_gives_format_message` and
`test_R4a_kelvin_replaces_first_k_of_valid_iban_gives_format_message`.
