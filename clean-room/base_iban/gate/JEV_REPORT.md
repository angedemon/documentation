# JEV gate report — Role 1 (SPEC gate), base_iban SPEC

Judged: `room_a/out/SPEC.md`. Original checked: `room_a/odoo/addons/base_iban/models/res_partner_bank.py`.
Handoff written: `room_b/SPEC.md` (passing rules only; no Evidence fields, paths, line refs or original identifiers).

## Method
1. Replayed the harness on a **copy** of the evidence dir (`scratchpad/jev_replay/`, `python3 -I trace.py`) so REA's files were not overwritten. All 5 trace files are byte-identical to REA's.
2. Opened every cited `src:N` range and checked it says what the rule claims.
3. Independent checks (`scratchpad/jev_tools/check.py`, against the original module loaded via the stubs):
   - R5 table: all 70 rows match the original template map exactly (code, template text, compact length). No missing or extra codes.
   - R1: the "remove non-word chars and underscore" behavior equals "keep exactly the chars where `str.isalnum()` is true" over **all** 0x110000 code points (0 mismatches). Used for the leakage rewrite.
   - `'AZ' + 26 zeros` → valid (confirms REA's AZ note).
   - Pretty quirk `'BE68 5390 0754 7034'` → `'BE68  539 0 07 54 7 034'` re-confirmed.

## Verdicts

| Rule | Evidence | Verdict | → Destination |
|---|---|---|---|
| R1 Normalization | src:12-13; trace_normalize_pretty_bban (normalize) | pass (rewritten: leakage) | room B |
| R2 Normalize before validate | src:32; trace_validate (Input variants) | pass | room B |
| R3 Empty input | src:33-34; trace_validate, trace_errors | pass | room B |
| R4 Country support | src:36-38; trace_validate (bad country) | pass (wording fixed) | room B |
| R5 Per-country length / table | src:108-179, 40-41; trace_templates (70/70, n±1) | pass | room B |
| R6 ASCII charset | src:41; trace_validate (Non-ASCII), trace_errors | pass (regex not carried) | room B |
| R7 Format message | src:42-43; trace_validate, trace_errors | pass | room B |
| R8 Structure not enforced | src:41,45-47; trace_validate (Structure, Check digits) | pass (oracle remark removed) | room B |
| R9 Checksum | src:45-48; trace_validate, trace_errors | pass (rewritten: leakage) | room B |
| R10 Order of checks | src:31-48; trace_errors, trace_validate | pass | room B |
| R11 Boolean check | src:99-104; trace_model (check_iban) | pass (API note corrected) | room B |
| R12 Pretty formatting + quirk | src:15-22; trace_normalize_pretty_bban (pretty) | pass | room B |
| R13 BBAN extraction, no validation | src:24-29; trace_normalize_pretty_bban (bban) | pass | room B |
| R14 BBAN for account record | src:68-71; trace_model (get_bban) | pass (unproven host claim dropped) | room B |
| R15a 'iban' iff validation succeeds; else delegate unmodified number to host classification; ('iban','IBAN') appended at end of host list | src:54-66; trace_model | pass (rewritten as scoped behavior) | room B |
| R15b fallback value `'bank'`; host list `[('bank','Normal')]` | **stub only** (stubs/odoo/models.py) | **fail** — invented by stub, not in SOURCE | **back to REA** |
| R16 Storage cleanup on create/update | src:73-91; trace_model (create, write) | pass (speculative host note dropped) | room B |
| R17 Constraint on IBAN-typed accounts | src:93-97; trace_model (_check_iban) | pass (speculative host note dropped) | room B |

## R15 decision
Split. The part proven by base_iban itself passes: a valid IBAN (R2–R9) is classified `'iban'`; any other number is handed **unchanged** to the host's default classification and that result is returned as-is; the module appends `('iban', 'IBAN')` to the end of the host's supported-type list. REA's examples only say "→ fallback", which is fine.
The stub-derived facts fail and go back to REA: the fallback value `'bank'` and the base list `[('bank','Normal')]` appear only in `stubs/odoo/models.py`; nothing in SOURCE proves them. In the handoff I rewrote R15 as an explicit, clearly-scoped behavior: `fallback` is supplied by the caller and returned unchanged, the spec states no value for it, and tests must not assume `'bank'` or any particular host list.

## Sent back to REA
1. **R15b (fail):** real host fallback classification value(s) and the base supported-type list. Needs the base `res.partner.bank` source, or must stay out of scope. Nothing about these was sent to room B.
2. **Gap found by JEV, affects R4 (R4 still passes for what is proven):** "case-insensitive" country matching was traced only for ASCII. The original lowercases with Unicode rules, so the Kelvin sign U+212A + `W` + 28 zeros (30 chars) passes the country check as `KW` and then fails with the **format** message (R7), not the country message. REA should trace this and decide whether it belongs in the spec as a rule. For now the handoff scopes R4 to ASCII letters and says non-ASCII case-folding is unspecified.
3. **Minor factual error (fixed in handoff):** R4 called US, LC, EG, SC, ZZ "countries that use IBAN but are not in the table". US and ZZ do not use IBAN. The handoff now says "codes not in the table".
4. **API/rule mismatch (fixed in handoff):** the API table says `is_iban` is "True iff validate_iban raises nothing". For a non-string truthy input (int `12`) the original raises `TypeError`, so it neither returns False nor True. The handoff scopes `is_iban` and `pretty_iban` to `str | None` and leaves non-string behavior unspecified. REA may trace it if needed.

## Implementation leakage found and rewritten
| Where | Leak | Rewrite in handoff |
|---|---|---|
| Header | source path, Odoo commit hash, `src:N` scheme, harness/stub description | removed |
| All rules | Evidence fields with file:line and trace section names that carry original method names (`get_bban_from_iban`, `check_iban`, `retrieve_acc_type`, `_get_supported_account_types`, `_check_iban`, `create`, `write`) | removed |
| R1 | "non-word characters plus underscore" / "Python's Unicode `\w`" mirrors the original regex | stated as behavior: keep exactly the characters that are Unicode alphanumeric (Python `str.isalnum()` semantics), drop everything else, underscore included. Equivalence checked over all code points |
| R9 | step list (move 4 chars, base-36 per char, concatenate, int, mod 97) mirrors the original's expression and its "BASE 36" comment | stated as the public ISO 13616 / ISO 7064 MOD 97-10 condition (A/a=10 … Z/z=35, rearranged value mod 97 = 1), not as a step-by-step algorithm |
| R8 | "check digits found by using the original validator as an oracle" | removed; examples kept as plain data |
| R11 | "In the original this is a model method"; default-argument wording mirrors the signature | removed; kept only the observed result (no argument → False) |
| R14/R16/R17 limits | claims about unseen host code ("an 'iban' type implies…", "sanitized number field in base", "type usually computed through R15") | removed as unproven; scope stated instead |
| R2/R3 | invisible U+00A0 characters in examples | written as explicit ` ` escapes |

Not treated as leakage (allowed): the R5 country/template table (data), exact user-facing messages, the account-type values `'iban'`/`'IBAN'` (observable data).
**Flag for the orchestrator:** the "neutral" target API names `normalize_iban`, `validate_iban`, `pretty_iban` match the original module's public function names, and `get_bban` matches a public method. I kept them because they are an interface contract and I was told to keep the target API. If the room needs names that differ from the original, rename them in the API table only; no rule depends on the names.

## Notes on quirks (kept, proven)
- R12: pretty formatting groups the **raw** input, so separators count as characters. Proven by trace and re-confirmed independently.
- R13: BBAN extraction does no validation (`'US12345678'` → `'345678'`, `'hello world'` → `'oworld'`). Proven.

---

# Round 2 — gate of SPEC Revision 2 + routing of room B questions

Judged: `room_a/out/SPEC.md` Rev 2. Originals checked: `room_a/odoo/addons/base_iban/models/res_partner_bank.py` (src) and `room_a/odoo/odoo/addons/base/models/res_bank.py` (base).
Handoff written: `room_b/SPEC.md` (Rev 2, gated, no Evidence/paths/line refs/original identifiers), `room_b/ANSWERS.md`.

## Method
1. Copied `evidence/` to `scratchpad/jev_replay2/` and ran `python3 -I -B trace_rev2.py` there. All 4 rev-2 traces are **byte-identical** to REA's (`trace_acc_type_rev2`, `trace_nonstr_rev2`, `trace_sanitize_rev2`, `trace_unicode_case_rev2`).
2. Read `stubs_rev2/odoo/*`: only decorators as identity, field placeholders, a recorder ORM root (create/write return vals, condition returns a tuple), and a translation stub. No base behavior is injected. The values `'bank'` and `[('bank','Normal')]` now come from the real base file (base:74, base:116), not from a stub. **The round-1 R15b objection is cleared.**
3. Opened every new `base:N` citation: 10-13 (sanitize: removes `\W+`, keeps `_`, `.upper()`, falsy → False), 68-74 (accessor + list), 77 (type is a computed Selection whose choices come from the accessor), 79 / 97-100 (stored derived field), 91-95 (unique (derived, partner) + message), 102-105 (compute calls the classifier), 112-116 (classifier returns `'bank'` unconditionally), 123-130 (search rewrite), 132-146 (moves the derived key into the number, then recomputes; runs after base_iban in the MRO). All match the rules.
4. Independent checks (`scratchpad/jev_tools/check2.py`, `check3.py`, against the originals):
   - Unicode scan over all code points: non-ASCII alphanumerics whose lowercase is one ASCII letter = {U+212A} only; lowercase made only of ≥2 ASCII letters = none; multi-character lowercase starting with ASCII = {U+0130}; no single character passes the country check alone. This confirms R4a, including the 1-character window case REA did not state.
   - Extra R4a vectors: `ı`, `ſ` (both positions), `ß`, and `Iı` → country message (these characters' **uppercase** is ASCII, so a rebuild using upper-casing would differ; added to the handoff as test vectors); `D` + U+212A + `5000400440116243` → format message.
   - R8 alphabet: REA's harness counts over `A-Z0-9`. Replayed: 10 pairs `I6 OX PU QR RO S3 SL TI UF VC`; the only all-digit pair is `68`; over `0-9A-Za-z` the count is 36.
   - The R16 batch example in the handoff (`[no93-…, '123 456', {}]`) was replayed on the composed model.

## Verdicts (Rev 2, new or changed items only; the other rules are unchanged from round 1 and stay `pass`)

| Rule | Evidence | Verdict | → Destination |
|---|---|---|---|
| R4 (wording fixed, ASCII scope) | src:36-38; trace_validate | pass | room B (already corrected in round-1 handoff; "unspecified" note replaced by R4a) |
| R4a Kelvin sign / non-ASCII country positions | src:36-43; trace_unicode_case_rev2 (replayed, identical) + JEV exhaustive scan | pass (rewritten: leakage) | room B, **contract** |
| R15 fallback `'bank'`, base list, installed list | src:54-66; base:68-74, 112-116; trace_acc_type_rev2 | pass | room B, **contract** (values fixed in API) |
| R15 type computed from number, offered as choices | base:77, 102-105; trace_acc_type_rev2 (compute) | pass (field declaration read; ORM recompute not run, as REA states) | room B, **informative host note** |
| R14 / R17 updated limits | base:77, 102-105; compute trace | pass (derived reasoning sound: an `'iban'` type implies validation passed; `pretty(normalize(valid))` is still valid) | room B, informative note under R17 |
| R16a points 1-3 (derived value) | base:10-13, 79, 97-100, 132-146; trace_sanitize_rev2 (create/write BASE vs INSTALLED, property check, exhaustive isalnum-or-`_`) | pass | room B, **informative host note** |
| R16a point 4 (derived key moved after R16) | base:132-136 + MRO; trace_sanitize_rev2 | pass | contract part: "R16 reads/changes only the account-number key" added to R16; host consequence → host note |
| R16a point 5 (search) | base:123-130; trace (condition only) | pass | informative host note |
| R16a point 6 (uniqueness) | base:91-95; not executed (no DB), only derived values traced | pass as stated (declaration + inputs it would compare) | informative host note |
| R18 non-str inputs | src:12-13, 15-22, 31-32, 60-66, 99-104; base:10-13, 112-116; trace_nonstr_rev2 | pass | room B, **informative**, explicitly outside contract |
| API table: `is_iban` row, input domain `str \| None` | src:99-104; trace_nonstr_rev2 | pass | room B |

No `fail` in Rev 2.

## Scope decisions
The rebuild targets base_iban. Test for each base-module fact: does it fix a value that a base_iban-level contract function **returns**? If yes, it goes into the contract. If it is something the host does with that value afterwards, it is an informative note.
- **R15 `'bank'` and the type lists → contract.** The rebuild exposes `account_type` and `supported_account_types` as standalone functions with no host behind them. Their return values in the minimal installation (base + base_iban) are now proven, so tests must be able to assert them. To keep the round-1 proven delegation semantics, `account_type` keeps an optional `fallback` that defaults to `'bank'`. `add_iban_account_type(types)` is the extension point for other hosts.
- **R16a (derived sanitized number), search, uniqueness → informative host notes, not contract.** They are computed, declared and enforced entirely by the base model, and base_iban neither calls nor changes them. A rebuild of base_iban cannot and should not reimplement them: they belong to whatever host it plugs into. Including them in the contract would make room B rebuild base. One consequence does belong to base_iban's own contract and is added to R16: the cleanup reads and changes **only** the account-number key (a valid IBAN under any other key, including the host's derived key, is left as it is). This is proven by the installed-vs-base trace, where a derived-key-only input reaches the host unformatted. The underscore consequence (point 2) follows from R16 + R1, which are already in the contract.
- **Type computed from the number / choices → informative.** This is host field wiring (base:77, 102-105). The rebuild's R14/R17 functions take the type as an argument.
- **R18 → informative, outside the contract.** REA labels it so. It is passed on so that the rebuild's TypeError choice is known to be consistent with observation. Tests must not cover it.

## Leakage found in Rev 2 and rewritten in handoff
| Where | Leak | Rewrite |
|---|---|---|
| Changelog, header, every Evidence | `base:N`, `src:N`, file paths, commit, harness/stub description, trace section names | removed |
| R1, R9 (still in REA's text) | `\w` / underscore regex wording; step list mirroring the original expression | round-1 behavioral rewrites kept |
| R4a | "compares the Unicode **lowercase** form" (mirrors the original's case operation) | stated as an outcome: exactly one non-ASCII char (U+212A) is accepted, as K; full consequence list + vectors. No case-mapping method named |
| R15 | "public accessor returns the same list" (mirrors accessor/private pair) | `supported_account_types()` returns the list |
| R16a | derived-field identifier (as `sanitized:` key), "base model" | "host's derived form", no identifiers; in the host-notes section |
| R18 | "base sanitize" column | dropped (host internals) |
| R8 | "check digits found by using the original validator as an oracle" (still in REA text) | removed; full list of 10 pairs given as data |

**Flag (names, carried over from round 1):** the contract names `acc_type`/`acc_number` (parameter names, dict key default `'acc_number'`) match the host's public field names, and `check_iban_account` has the original boolean method's name as a prefix, though it means something different (the constraint). These are interface choices, and no rule depends on them. The key `'acc_number'` was kept because it is the rebuild's existing choice and matches the R15 parameter. If the orchestrator wants zero name overlap, rename them in the API table only.

## Routing of room B questions (`room_b/QUESTIONS.md`)
| # | From | Answer (all in `room_b/ANSWERS.md`) | Source |
|---|---|---|---|
| 1 | rebuilder | Now specified: U+212A must pass the country check as K and then give R7; every other non-ASCII char → country message. The rebuild's ASCII-only approach must change for U+212A only. Warned that generic upper-casing is wrong (`ı`, `ſ`) | R4a |
| 2 | rebuilder | `account_bban(acc_type, acc_number)` confirmed; exact type comparison | API, R14 |
| 3 | rebuilder | `check_iban_account(acc_type, acc_number)` confirmed; one account, callers loop | API, R17 |
| 4 | rebuilder | `add_iban_account_type(types)` confirmed; returning a new list is allowed. Mutation and duplicates unspecified (returned to REA) | API, R15 |
| 5 | rebuilder | `sanitize_account_vals(vals, key='acc_number')` confirmed; same shape, order kept, only the key touched; in-place mutation unspecified | API, R16 |
| 6 | rebuilder | Outside the contract; R18 informative; the rebuild is consistent; not tested; `iban_template` non-str unspecified | API note, R18 |
| 7 | rebuilder | `None`, correct | API (`iban_template` row) |
| 8 | tester | Names fixed; un-skip R14/R17 | API, R14, R17 |
| 9 | tester | Name fixed; test vectors given; `account_type` → `'bank'` and the exact list are now assertable | API, R15 |
| 10 | tester | Key `'acc_number'` fixed; un-skip; assert on the return value only | API, R16 |
| 11 | tester | Alphabet `0-9A-Z`; the 10 pairs listed; 36 over mixed case | R8 |

## Sent back to REA (round 2)
1. **R15 list append, optional:** does the module's append modify the host list in place, and does it append again when `'iban'` is already present? (Code reading suggests an unconditional in-place append; not traced, and the host returns a fresh list per call, so it may be unobservable.) Room B was told these are unspecified and must not be tested. Answer only if a product decision needs it.
2. Nothing else. No Rev-2 rule failed.

# Round 3 — routing of room B question 12

**Q12 (tester):** R4a does not say which message applies when U+212A is in position 1 or 2 and the pair read with `K` is not a table code. Tester assumed the R4 country message.

**Method:** copied REA's Rev-2 harness to `jev_replay3/evidence/harness/` (REA's files and the originals untouched). Added `trace_rev3.py`, which loads the unmodified originals the same way as `trace_rev2.py` (same `stubs_rev2`, same installed-model simulation). Ran it with `python3 -I -B` (Python 3.13.16). Output: `jev_replay3/evidence/trace_kelvin_nontable_rev3.txt`.

**Evidence:**
| Input (`K` = U+212A) | pair as K | in table | validate | is_iban | pretty | acc_type |
|---|---|---|---|---|---|---|
| `KE68539007547034`, `BK68539007547034` (the Q12 examples) | ke / bk | no | country msg | False | unchanged | bank |
| `Ke6853…`, `bK6853…` (lowercase partner) | ke / bk | no | country msg | False | unchanged | bank |
| `KA00`, `AK00`, `KK00` | ka / ak / kk | no | country msg | False | unchanged | bank |
| `K1`+14×0, `1K`+14×0 (digit partner) | k1 / 1k | no | country msg | False | unchanged | bank |
| `KE`, `BK` (len 2), `K` (len 1) | — | no | country msg | False | unchanged | bank |
| controls: `KW`+28×0, `SK3112000000198742637541` | kw / sk | yes | R7 format msg (KW / SK template) | False | unchanged | bank |

Exhaustive check: U+212A in pos 1 or 2, other char in `[0-9A-Za-z]` or U+212A, suffix `00`, giving 126 inputs. Not in table → country message, 112/112. In table → format message, 14/14. bban still drops the first 4 characters (R13).

**Verdict:** the tester's assumption is **proven**. The original raises the plain country error, because the failure is the normal unsupported-code path. Added to SPEC (room B) as R4a consequence 1a, with a "Revision 2.1" changelog line. Behavior only: no case-mapping method named and no references to the original. Answer 12 is appended to `room_b/ANSWERS.md` and cites R4a/1a. Nothing was sent back to REA.

| # | From | Answer | Source |
|---|---|---|---|
| 12 | tester | Country message confirmed; test is correct | R4a (1a), R4 |
