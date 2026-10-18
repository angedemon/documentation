# Answers to room B questions (JEV, round 2)

All answers refer to `SPEC.md` Revision 2 in this room. Where an answer says
"unspecified", do not test it.

## Rebuilder

**1. R4, non-ASCII characters that case-fold to ASCII.**
Now specified by **R4a**. Your ASCII-only matching is right for every non-ASCII
character except one: **U+212A KELVIN SIGN** must be accepted as `K` in the two
country positions. When the pair (reading it as `K`) is a table code (`DK`, `KW`,
`KZ`, `MK`, `PK`, `SK`, `XK`), validation must then fail with the **R7 format
message** using that country's template, at any length. It must not fail with the
country message, and must never reach the checksum. All other non-ASCII characters
(`ı`, `ſ`, `ß`, `İ`, fullwidth, titlecase, ...) give the R4 country message, as your
rebuild does now. Generic Unicode upper-casing would be wrong: it would accept `ı`
and `ſ`. The R4a examples are test vectors. `iban_template` is a separate function:
it matches ASCII letters only, and returns `None` for U+212A (API table).

**2. R14 name and signature.**
Confirmed: `account_bban(acc_type: str, acc_number: str | None) -> str`, raising
`NotAnIbanError` (API table, R14). The comparison is exact and case-sensitive:
`'IBAN'`, `''` and `None` are "other type" (R14). The number is not re-checked
(R14).

**3. R17 name and shape.**
Confirmed: `check_iban_account(acc_type: str, acc_number: str | None) -> None`, one
account per call. Callers loop over their accounts. It raises the `validate_iban`
error only when `acc_type == 'iban'`, and does nothing for other types (API table,
R17).

**4. R15 list append.**
Confirmed: `add_iban_account_type(types) -> list`, which returns the entries of
`types` in order with `('iban', 'IBAN')` as the last entry (R15). Returning a new
list is allowed. **Unspecified:** whether the argument is modified, and duplicates
when `'iban'` is already present. This has been sent to room A. Until it comes back
as a rule, keep your choice and do not test either point. Also fixed:
`supported_account_types()` returns exactly `[('bank', 'Normal'), ('iban', 'IBAN')]`
(R15).

**5. R16 record and batch handling, key name.**
Confirmed: `sanitize_account_vals(vals: dict | list[dict], key: str = 'acc_number')`,
with the default key `'acc_number'` (API table, R16). It returns a dict for a dict,
and a list of the same length and order for a list. Each record is handled
independently. Only `key` is read or changed. Other keys are left as they are, even
if they hold a valid IBAN (R16). **Unspecified:** whether input dicts are modified
in place. Returning copies is allowed. Only the return value is tested.

**6. Non-`str` inputs.**
Outside the contract. The input domain is `str | None` (API table). **R18** records
the observed behavior as information: falsy values act like `None`, and truthy
non-strings raise `TypeError` from every function. Your rebuild matches R18 for the
functions R18 lists. Reproducing it is allowed, not required. `iban_template` with a
non-`str` argument is unspecified. None of this is tested.

**7. `iban_template` with inputs that are not two characters long.**
Your behavior is right: `None` (API table, `iban_template` row: the code must be
exactly one table code, so `'BEL'` and `''` → `None`).

## Tester

**8. R14 and R17 API names.**
Fixed in the API table: `account_bban` (R14) and `check_iban_account` (R17), with
the signatures above. Un-skip both. Use the R14 and R17 examples and the exact
type comparison from R14. Note on R17 (informative): an R17 failure needs a type
set independently of R15, so test it by passing `'iban'` explicitly.

**9. R15 list append API name.**
Fixed: `add_iban_account_type` (API table, R15). Test it with
`add_iban_account_type([('bank', 'Normal')]) == supported_account_types()`, `[]` →
`[('iban', 'IBAN')]`, and "last entry, order of the input entries kept". Do not test
mutation of the argument or duplicates (unspecified). You can now also assert
`account_type(x) == 'bank'` for non-IBANs, and the exact `supported_account_types()`
list (R15).

**10. R16 record and batch key name.**
Fixed: the key is `'acc_number'` by default (API table). Un-skip, using the R16
examples: a single dict, the batch example, the absent-key and other-key cases, and
the empty and `False` values. Assert only on the returned value.

**11. R8 letter check-digit count: which alphabet.**
The alphabet is `0-9A-Z` (uppercase letters and digits). The count over that
alphabet is exactly 10 non-all-digit pairs: `I6`, `OX`, `PU`, `QR`, `RO`, `S3`,
`SL`, `TI`, `UF`, `VC`. The only all-digit pair is `68` (R8). Your test counts the
right thing. Lowercase spellings are the same pairs and are also accepted (R9 is
case-insensitive). Counting over `0-9A-Za-z` gives 36 (R8).

## Round 3

### Tester

**12. R4a: U+212A in a country position whose pair with `K` is not a table code.**
Confirmed: the R4 country message (`The IBAN is invalid, it should begin with the
country code`). Your test is right. This is now stated in R4a, consequence 1a
(SPEC Revision 2.1): the check fails like any other unsupported code, whatever the
other character is (either case, digit, or a second U+212A) and at any length.
`'KE68539007547034'` and `'BK68539007547034'` → country message. The R4a
"Downstream" line applies too: `is_iban` → False, `pretty_iban` unchanged,
`account_type` → `'bank'`. You may add the other 1a examples.
