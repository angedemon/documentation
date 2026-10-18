# Open questions (room B)

1. **R4: non-ASCII characters that case-fold to ASCII.** The SPEC says this is unspecified (e.g. `'ı'.upper() == 'I'`, `'ß'.upper() == 'SS'`, the Kelvin sign `K`).
   *What I did (conservative):* only ASCII `a-z` is upper-cased before the table lookup (`str.translate`, not `str.upper`). Any other character in the first two positions makes the lookup fail, so the R4 country message is raised.

2. **R14: no function name or signature in the API table.**
   *What I did:* added `account_bban(acc_type, acc_number)`. It raises `NotAnIbanError` when `acc_type != 'iban'` and otherwise returns `get_bban(acc_number)`. It compares the type exactly (case-sensitive) and does not re-check the number.

3. **R17: no function name or signature, and no shape for "accounts".**
   *What I did:* added `check_iban_account(acc_type, acc_number)`, which checks one account. Callers loop over their accounts. For type `'iban'` it calls `validate_iban`; it does nothing for any other type.

4. **R15: how "appends to the host's list" is done is not specified.**
   *What I did:* added `add_iban_account_type(supported_types)`. It returns a new list with `('iban', 'IBAN')` at the end and does not change the input list. It does not remove duplicates if `'iban'` is already in the list (unspecified).

5. **R16: record and batch handling has no API, and the key name is not specified.**
   *What I did:* `sanitize_account_number_for_storage(value)` is the specified per-value function. I also added `sanitize_account_vals(vals, key='acc_number')`, which takes a dict or a list of dicts and returns copies. The default key name `acc_number` is my assumption, taken from the parameter name in R15.

6. **Non-`str` inputs** (unspecified apart from R1).
   *What I did:* a truthy non-string `TypeError` raised by `normalize_iban` propagates through `validate_iban`, `is_iban`, `pretty_iban`, `get_bban`, `account_type` and `sanitize_account_number_for_storage`, so none of them hide it. Falsy non-strings (`0`, `False`) are treated as empty. `iban_template` returns `None` for any non-`str` code.

7. **`iban_template` with inputs that are not two characters long** (e.g. `'BEL'`, `''`).
   *What I did:* the input must match a table key exactly after ASCII upper-casing, so these return `None`.

## Tester (room B)

8. **R14 and R17 have no API name.** SPEC gives the behavior (BBAN for an
   account record; per-account IBAN constraint on set/change) but no function
   name or signature. The tests for both are skipped placeholders, so they are
   not checked. Please name the functions, or confirm that the rebuild's
   `account_bban` and `check_iban_account` are the intended names. Neither is
   tested yet.
9. **R15 list append has no API name.** The rule "append `('iban', 'IBAN')` to
   the end of the host list" is untested (skipped) for the same reason. The
   rebuild's `add_iban_account_type` is not covered by the tests.
10. **R16 record and batch handling has no key name.** The per-value function
    `sanitize_account_number_for_storage` is tested. The record/batch wrapper
    depends on the key name (`acc_number` is the rebuild's assumption, not in
    SPEC), so that part is a skipped placeholder.
11. **R8 letter check-digit count, case.** The SPEC says "exactly 10" letter
    check-digit pairs for BBAN `539007547034`. The test counts pairs over the
    uppercase alphabet, since the checksum is case-insensitive and counting
    lowercase too would double-count. The count of 10 passes against the rebuild.
    The SPEC should say which alphabet it means.

## Tester (room B, round 2)

12. **R4a: U+212A in a country position whose pair with `K` is not a table code.**
    R4a says the country check passes only when reading U+212A as `K` gives a
    table code. It does not say which message applies otherwise. I read it as
    the R4 country message, since the check fails the same way as any other
    unsupported code (e.g. `'KE68539007547034'`, `'BK68539007547034'`).
    The test asserts the country message. Please confirm, or say if another
    message is intended.
