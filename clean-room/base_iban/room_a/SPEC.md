# SPEC: IBAN / BBAN behavior (base_iban, Odoo 18.0)

## Revision 2 — changelog (answers to JEV gate report)

| Item | Change | Evidence |
|---|---|---|
| R15b (failed) | **Re-proven from the real base model.** Fallback for any number that is not an IBAN is `'bank'` (base returns it unconditionally). Base type list is exactly `[('bank', 'Normal')]`; with base_iban: `[('bank', 'Normal'), ('iban', 'IBAN')]`. R15 rewritten; the stub-only claim is gone. | base:68-74, base:112-116; `trace_acc_type_rev2.txt` |
| R15 (new facts) | Record type is computed from the account number via the R15 decision; the selection offered is the R15 list. | base:77, base:102-105; `trace_acc_type_rev2.txt` (compute) |
| R16a (new) | Interaction of R16 with the base "sanitized account number": base sanitizes the value **after** R16. Proven consequences listed. | base:10-13, 79, 91-95, 123-146; `trace_sanitize_rev2.txt` |
| R4 (fixed) | Wording error fixed: `US`, `LC`, `EG`, `SC`, `ZZ` are just "codes not in the table" (US and ZZ do not use IBAN). R4 now scoped to ASCII; non-ASCII handled by R4a. | — |
| R4a (new) | Unicode case-folding gap made a rule: U+212A KELVIN SIGN is the only non-ASCII character that can pass the country check; it then always fails with the R7 format message. Exhaustive scan over all code points. | src:36-43; `trace_unicode_case_rev2.txt` |
| R18 (new) / API table | Contract input domain is `str \| None`. Behavior for other types traced per type and recorded in R18 (falsy → treated as empty; truthy → `TypeError` from every function, including the boolean check). API row for `is_iban` corrected. | src:12-13, 99-104; `trace_nonstr_rev2.txt` |
| R14 / R17 limits | Updated with what the base model now proves (type is computed, not set by hand). | base:77, 102-105 |
| Dropped | Nothing dropped. R15's stub-derived values are replaced by proven values. | — |

Rev-2 traces come from `evidence/harness/trace_rev2.py` (`python3 -I -B trace_rev2.py`,
Python 3.13.16) with a second fake package `evidence/harness/stubs_rev2/odoo/`.
It loads **both** original files unmodified and simulates the installed model as a
class whose bases are (base_iban model, base model), so base_iban's parent calls
reach the real base code, and the base code's parent calls reach a plain recorder
(stubbed ORM root that returns the vals it receives). No DB, no real ORM compute.
Rev-1 traces (`evidence/harness/trace.py`, stubbed parent) are kept unchanged;
their stubbed parent values (`'bank'`, `[('bank','Normal')]`) are now confirmed
equal to the real base by rev-2 traces.

---

Sources analysed (read-only), Odoo 18.0, commit 1f2b50ade7a11e11cbcd792b5b6df439525c54d0:
- `odoo/addons/base_iban/models/res_partner_bank.py` — `src:N` means this file at line N.
- `odoo/odoo/addons/base/models/res_bank.py` (base `res.partner.bank`) — `base:N`
  means this file at line N.

Evidence: `evidence/trace_*.txt`, produced by `evidence/harness/trace.py`
(`python3 -I trace.py`). The harness loads the original file unmodified, with a
fake `odoo` package (`evidence/harness/stubs/odoo/`): translation returns the
source string %-formatted with its arguments, `ValidationError`/`UserError` are
plain exceptions, and the parent `res.partner.bank` behavior is stubbed (see R15;
superseded by the rev-2 traces `evidence/trace_*_rev2.txt`, see above).

Scope: pure IBAN functions plus the observable account-type decision and how the
stored account number is cleaned up. Out of scope: JS widget, views, i18n, demo
data, ORM plumbing.

---

## 1. Target public API (neutral names for the rebuild)

| Function | Signature | Observed behavior it must reproduce |
|---|---|---|
| `normalize_iban` | `(value: str \| None) -> str` | R1 |
| `validate_iban` | `(value: str \| None) -> None`, raises `IbanValidationError(message: str)` | R2–R10 |
| `is_iban` | `(value: str \| None) -> bool` | R11 (for `str \| None`: True iff `validate_iban` raises nothing, False iff it raises `IbanValidationError`) |
| `pretty_iban` | `(value: str \| None) -> str \| None` | R12 |
| `get_bban` | `(value: str \| None) -> str` | R13 |
| `iban_template` | `(country_code: str) -> str \| None` | R5 table (the display template; matching ignores ASCII case, see R4/R4a) |
| `account_type` | `(acc_number: str \| None) -> 'iban' \| 'bank'` | R15 |
| `supported_account_types` | `() -> list[tuple[str, str]]` | R15 |
| `sanitize_account_number_for_storage` | `(value) -> value` | R16 |

**Input domain.** The contract for every function above is `str | None`. The
original was also traced with other types (R18): falsy non-strings behave like
empty input, truthy non-strings raise `TypeError` from every function, including
`is_iban` (it then returns neither True nor False). R18 is informative; a rebuild
need not reproduce it unless the product decides so.

`IbanValidationError` corresponds to the host framework's validation error; a
second error kind (`NotAnIbanError`, the host's user error) is needed only for
R14.

---

## 2. Rules

### R1 — Normalization
- **Behavior:** Removes every character that is not a Unicode "word" character, and
  also removes underscores. Letters, digits (including non-ASCII ones such as `é`,
  `ß`, `٣`, `²`) are kept. Case is **not** changed. `None` (and any falsy value such
  as `0` or `''`) gives `''`. A non-string truthy value (e.g. the int `12`) raises a
  `TypeError`.
  Examples: `'BE68 5390 0754 7034'` → `'BE68539007547034'`;
  `'be68-5390.0754/7034'` → `'be68539007547034'`; `'a_b c\td\ne'` → `'abcde'`;
  `'é ß ٣ ²'` → `'éß٣²'`; `'!!!'` → `''`; `None` → `''`.
- **Evidence:** src:12-13; `evidence/trace_normalize_pretty_bban.txt` (section normalize_iban).
- **Limits:** Only the listed separators/characters were traced; "word character" is
  Python's Unicode `\w` definition. The `TypeError` text is the Python runtime's,
  not part of the module's contract.

### R2 — Validation input is normalized first
- **Behavior:** `validate_iban` applies R1 before every check. So spaces, tabs,
  newlines, non-breaking spaces, `- . / ( ) ! _` anywhere in the input are ignored,
  and lowercase input is accepted.
  Accepted: `'BE68 5390 0754 7034'`, `'be68 5390 0754 7034'`, `'Be68-5390-0754-7034'`,
  `'BE68_5390_0754_7034'`, `' BE68\t5390\n0754 7034 '`, `'BE68 5390 0754 7034'`,
  `'BE68/5390(0754)7034!'`, `'gb82 west 1234 5698 7654 32'`.
  A prefix word is not stripped: `'IBAN BE68 5390 0754 7034'` → country error (R4).
- **Evidence:** src:32; `evidence/trace_validate.txt` (Input variants).
- **Limits:** none known beyond R1's.

### R3 — Empty input
- **Behavior:** If the normalized value is empty, raises `IbanValidationError` with
  the exact message `There is no IBAN code.`
  Inputs traced: `None`, `''`, `'   '`, `'---'`, `'_'`, `' '`.
- **Evidence:** src:33-34; `evidence/trace_validate.txt` (Empty / missing); `evidence/trace_errors.txt`.
- **Limits:** none.

### R4 — Country support
- **Behavior:** The first two normalized characters, ignoring ASCII case, must be one
  of the 70 country codes in the R5 table. If not, raises with the exact message
  `The IBAN is invalid, it should begin with the country code`.
  This also happens for a 1-character input (`'B'`), inputs that start with digits
  (`'12345678901234'`, `'1E68539007547034'`), and codes not in the table
  (`US`, `LC`, `EG`, `SC`, `ZZ`).
- **Evidence:** src:36-38; `evidence/trace_validate.txt` (Unsupported / bad country code).
- **Limits:** All 70 supported codes were exercised (trace_templates). Unsupported
  codes were only sampled. Non-ASCII characters in the first two positions: see R4a.

### R4a — Non-ASCII characters in the country-code position
- **Behavior:** The country check compares the Unicode lowercase form of the first
  two normalized characters with the table. Over the whole Unicode range, the only
  non-ASCII character whose lowercase is a single ASCII letter is **U+212A KELVIN
  SIGN** (lowercase `k`). Therefore:
  1. If one of the first two characters is U+212A and, read as `k`, the pair is a
     supported code (only `DK`, `KW`, `KZ`, `MK`, `PK`, `SK`, `XK` contain a K), the
     country check **passes**, and validation then **always** fails with the R7
     format message showing the matched country's template (uppercase ASCII),
     whatever the length (correct length traced for all 7 codes; length −1 and +1
     traced for KW). The checksum is never reached,
     even when the value would be a valid IBAN with an ASCII K.
  2. Any other non-ASCII character in position 1 or 2 gives the R4 country message.
     Traced: U+0130 `İ` (its lowercase is two characters), fullwidth U+FF22 `Ｂ`,
     titlecase U+01C5 `ǅ`.
  3. U+212A after position 2 fails R6 (format message), like any non-ASCII character.
  Downstream (all traced on the case-1 inputs): `is_iban` → False; `pretty_iban`
  returns the input unchanged; `account_type` → `'bank'`; `get_bban` still strips
  the first 4 characters (R13, no validation).
  Examples (U+212A written `K`):
  `'KW' + 28×'0'` (30 chars) → format message with `KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC`;
  `'Kw' + 28×'0'` → same; `'DK' + 16×'0'` → format message with `DKkk BBBB CCCC CCCC CC`;
  ASCII control `'KW' + 28×'0'` → checksum message;
  valid `'KW81CBKU0000000000001234560101'` with its first `K` replaced by U+212A → format message;
  `'İE68539007547034'` → country message.
- **Evidence:** src:36-43; `evidence/trace_unicode_case_rev2.txt` (exhaustive scan of
  all code points except surrogates: 1 single-ASCII-letter lowercase hit, U+212A;
  1 multi-character lowercase hit, U+0130; crafted inputs for all 7 codes; K→U+212A
  substitutions in valid KW, KZ, SK, DK IBANs).
- **Limits:** The scan is per character. It relies on the lowercase of a 2-character
  window being the concatenation of each character's lowercase; the only
  context-dependent lowercasing in Python (Greek final sigma) yields non-ASCII, so it
  cannot create a match. Python 3.13 Unicode data; another Unicode version could
  change the hit list.

### R5 — Per-country length (template table)
- **Behavior:** Each supported country has a display template. The normalized IBAN
  length must equal the template length with spaces removed. This check runs
  together with R6, and either failure raises the R7 format message. Only **length**
  is enforced. The letters in the template (B, S, C, k, K, X, ...) are **not** checked
  against the content (see R8).
  Table (country → required compact length → display template, exactly as it
  appears in the error message):

| CC | Len | Template |
|---|---|---|
| AD | 24 | ADkk BBBB SSSS CCCC CCCC CCCC |
| AE | 23 | AEkk BBBC CCCC CCCC CCCC CCC |
| AL | 28 | ALkk BBBS SSSK CCCC CCCC CCCC CCCC |
| AT | 20 | ATkk BBBB BCCC CCCC CCCC |
| AZ | 28 | AZkk BBBB CCCC CCCC CCCC CCCC CCCC |
| BA | 20 | BAkk BBBS SSCC CCCC CCKK |
| BE | 16 | BEkk BBBC CCCC CCXX |
| BG | 22 | BGkk BBBB SSSS DDCC CCCC CC |
| BH | 22 | BHkk BBBB CCCC CCCC CCCC CC |
| BR | 29 | BRkk BBBB BBBB SSSS SCCC CCCC CCCT N |
| BY | 28 | BYkk BBBB AAAA CCCC CCCC CCCC CCCC |
| CH | 21 | CHkk BBBB BCCC CCCC CCCC C |
| CR | 22 | CRkk BBBC CCCC CCCC CCCC CC |
| CY | 28 | CYkk BBBS SSSS CCCC CCCC CCCC CCCC |
| CZ | 24 | CZkk BBBB SSSS SSCC CCCC CCCC |
| DE | 22 | DEkk BBBB BBBB CCCC CCCC CC |
| DK | 18 | DKkk BBBB CCCC CCCC CC |
| DO | 28 | DOkk BBBB CCCC CCCC CCCC CCCC CCCC |
| EE | 20 | EEkk BBSS CCCC CCCC CCCK |
| ES | 24 | ESkk BBBB SSSS KKCC CCCC CCCC |
| FI | 18 | FIkk BBBB BBCC CCCC CK |
| FO | 18 | FOkk CCCC CCCC CCCC CC |
| FR | 27 | FRkk BBBB BGGG GGCC CCCC CCCC CKK |
| GB | 22 | GBkk BBBB SSSS SSCC CCCC CC |
| GE | 22 | GEkk BBCC CCCC CCCC CCCC CC |
| GI | 23 | GIkk BBBB CCCC CCCC CCCC CCC |
| GL | 18 | GLkk BBBB CCCC CCCC CC |
| GR | 27 | GRkk BBBS SSSC CCCC CCCC CCCC CCC |
| GT | 28 | GTkk BBBB MMTT CCCC CCCC CCCC CCCC |
| HR | 21 | HRkk BBBB BBBC CCCC CCCC C |
| HU | 28 | HUkk BBBS SSSC CCCC CCCC CCCC CCCC |
| IE | 22 | IEkk BBBB SSSS SSCC CCCC CC |
| IL | 23 | ILkk BBBS SSCC CCCC CCCC CCC |
| IS | 26 | ISkk BBBB SSCC CCCC XXXX XXXX XX |
| IT | 27 | ITkk KBBB BBSS SSSC CCCC CCCC CCC |
| JO | 30 | JOkk BBBB NNNN CCCC CCCC CCCC CCCC CC |
| KW | 30 | KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC |
| KZ | 20 | KZkk BBBC CCCC CCCC CCCC |
| LB | 28 | LBkk BBBB CCCC CCCC CCCC CCCC CCCC |
| LI | 21 | LIkk BBBB BCCC CCCC CCCC C |
| LT | 20 | LTkk BBBB BCCC CCCC CCCC |
| LU | 20 | LUkk BBBC CCCC CCCC CCCC |
| LV | 21 | LVkk BBBB CCCC CCCC CCCC C |
| MC | 27 | MCkk BBBB BGGG GGCC CCCC CCCC CKK |
| MD | 24 | MDkk BBCC CCCC CCCC CCCC CCCC |
| ME | 22 | MEkk BBBC CCCC CCCC CCCC KK |
| MK | 19 | MKkk BBBC CCCC CCCC CKK |
| MR | 27 | MRkk BBBB BSSS SSCC CCCC CCCC CKK |
| MT | 31 | MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC |
| MU | 30 | MUkk BBBB BBSS CCCC CCCC CCCC CCCC CC |
| NL | 18 | NLkk BBBB CCCC CCCC CC |
| NO | 15 | NOkk BBBB CCCC CCK |
| OM | 23 | OMkk BBBC CCCC CCCC CCCC CCC |
| PK | 24 | PKkk BBBB CCCC CCCC CCCC CCCC |
| PL | 28 | PLkk BBBS SSSK CCCC CCCC CCCC CCCC |
| PS | 29 | PSkk BBBB XXXX XXXX XCCC CCCC CCCC C |
| PT | 25 | PTkk BBBB SSSS CCCC CCCC CCCK K |
| QA | 29 | QAkk BBBB CCCC CCCC CCCC CCCC CCCC C |
| RO | 24 | ROkk BBBB CCCC CCCC CCCC CCCC |
| RS | 22 | RSkk BBBC CCCC CCCC CCCC KK |
| SA | 24 | SAkk BBCC CCCC CCCC CCCC CCCC |
| SE | 24 | SEkk BBBB CCCC CCCC CCCC CCCC |
| SI | 19 | SIkk BBSS SCCC CCCC CKK |
| SK | 24 | SKkk BBBB SSSS SSCC CCCC CCCC |
| SM | 27 | SMkk KBBB BBSS SSSC CCCC CCCC CCC |
| TN | 24 | TNkk BBSS SCCC CCCC CCCC CCCC |
| TR | 26 | TRkk BBBB BRCC CCCC CCCC CCCC CC |
| UA | 29 | UAkk BBBB BBCC CCCC CCCC CCCC CCCC C |
| VG | 24 | VGkk BBBB CCCC CCCC CCCC CCCC |
| XK | 20 | XKkk BBBB CCCC CCCC CCCC |

  Templates with unusual groupings are reproduced verbatim, for example BR (ends
  with `T N`, a single trailing character group), PT (ends `CCCK K`), BY (`AAAA`),
  GT (`MMTT`), JO (`NNNN`), FR/MC (`GGG GG`), IS/PS (`XXXX`).
- **Evidence:** src:108-179, src:40-41; `evidence/trace_templates.txt`. For every
  country, lengths n−1 and n+1 raise the R7 format error, while length n passes the
  length check (CHECKSUM, or VALID for AZ with an all-zero body, which happens to
  satisfy the checksum).
- **Limits:** The trace only uses all-zero bodies. That template letters are not
  enforced is shown in R8 for BE, DE and NO only.

### R6 — Character set after normalization
- **Behavior:** The normalized value must contain only ASCII letters and digits. A
  non-ASCII word character that survived R1 (`é`, `ß`, Arabic-Indic digits,
  superscripts) raises the R7 format message, even when the length is correct.
- **Evidence:** src:41; `evidence/trace_validate.txt` (Non-ASCII section);
  `evidence/trace_errors.txt` (`'BE0000000000000é'`).
- **Limits:** A sample of non-ASCII characters was traced.

### R7 — Format/length error message
- **Behavior:** When R5 or R6 fails, raises `IbanValidationError` with exactly:
  `The IBAN does not seem to be correct. You should have entered something like this <TEMPLATE>\nWhere B = National bank code, S = Branch code, C = Account No, k = Check digit`
  where `<TEMPLATE>` is the country's display template from R5 (uppercase country
  code, spaces kept), and `\n` is a real newline. Example for `'BE68'`:
  `...something like this BEkk BBBC CCCC CCXX\nWhere B = ...`.
- **Evidence:** src:42-43; `evidence/trace_validate.txt` (Wrong length), `evidence/trace_errors.txt`.
- **Limits:** In the real host the message goes through translation. The trace shows
  the untranslated (English) text only. Translations are out of scope.

### R8 — Internal structure is not enforced
- **Behavior:** Apart from the two-letter country code, the length and the ASCII
  alphanumeric set, positions are not type-checked. Letters may appear where the
  template says digits, the BBAN may be all zeros, and the check digits (positions
  3–4) may even be letters. Any such value passes as long as the checksum (R9)
  holds. Accepted examples (check digits found by using the original validator as
  an oracle): `'BE57ABCDEFGHIJKL'`, `'be57abcdefghijkl'`, `'DE51XXXXXXXXXXXXXXXXXX'`,
  `'NO1300000000000'`, `'BE54000000000000'`. Letter check digits accepted:
  `'BEI6539007547034'`, `'BEOX539007547034'`, `'BEPU539007547034'` (10 such pairs for
  that BBAN).
- **Evidence:** src:41, src:45-47; `evidence/trace_validate.txt` (Structure / Check digits sections).
- **Limits:** Observed for BE, DE and NO only. Other countries are inferred from the
  same uniform behavior across the R5 trace.

### R9 — Checksum (ISO 7064 mod 97-10)
- **Behavior:** Once R3–R6 pass, the value is checked with the standard IBAN check.
  Move the first four characters to the end, replace each character by its base-36
  value (0–9 → 0–9, A/a–Z/z → 10–35, case-insensitive), read the result as a decimal
  integer. It must be ≡ 1 (mod 97). Otherwise raises exactly
  `This IBAN does not pass the validation check, please verify it.`
  On success `validate_iban` returns `None`.
  Valid published examples accepted: BE68539007547034, DE89370400440532013000,
  FR1420041010050500013M02606, GB82WEST12345698765432, NL91ABNA0417164300,
  CH9300762011623852957, NO9386011117947, MT84MALT011000012345MTLCAST001S,
  BR1800360305000010009795493C1, ES9121000418450200051332, IT60X0542811101000000123456,
  MU17BOMM0101101030300200000MUR, SA0380000000608010167519, PL61109010140000071219812874,
  AT611904300234573201, XK051212012345678906, PS92PALS000000000400123456702,
  JO94CBJO0010000000000131000302, QA58DOHB00001234567890ABCDEFG,
  KW81CBKU0000000000001234560101, UA213223130000026007233566001, IS140159260076545510730339.
  Rejected (checksum message): BE68539007547035, BE00539007547034, BE01539007547034,
  BE99539007547034, DE88370400440532013000, GB82WEST12345698765433, `'BE68 5390 0754 703X'`.
  No special rule for check digits `00`, `01` or `99`: they simply fail or pass the
  checksum.
- **Evidence:** src:45-48; `evidence/trace_validate.txt` (Published examples, Wrong checksum), `evidence/trace_errors.txt`.
- **Limits:** The description of the check is the standard IBAN algorithm, and it
  matches every traced case.

### R10 — Order of checks
- **Behavior:** Checks run in this order, and the first failure decides the message:
  empty (R3) → country (R4) → length/charset (R5/R6, one message R7) → checksum (R9).
  Examples: `'US'` and `'XX0'` → country message; `'BE'` and `'BE1'` → format message
  (country supported, length wrong); `'BE00000000000000'` → checksum message.
- **Evidence:** src:31-48; `evidence/trace_errors.txt` (Order of checks), `evidence/trace_validate.txt` (`'BE'`).
- **Limits:** none.

### R11 — Boolean check
- **Behavior:** A boolean wrapper returns `True` when validation succeeds and
  `False` when it raises the validation error. Its argument defaults to empty, so
  calling it with no argument gives `False`. Examples: `'BE68539007547034'` → True;
  `'be68 5390 0754 7034'` → True; `'BE68539007547035'`, `''`, `None` → False.
- **Evidence:** src:99-104; `evidence/trace_model.txt` (check_iban).
- **Limits:** In the original this is a model method. The rebuild exposes it as `is_iban`.

### R12 — Pretty (display) formatting
- **Behavior:** If the input is a valid IBAN (R2–R9), returns the input **as given
  (not normalized)**, cut into groups of 4 characters joined by single spaces. The
  last group may be shorter, and case is preserved. If the input is invalid, returns
  it unchanged (including `None` → `None`, `''` → `''`). It never raises.
  Examples: `'BE68539007547034'` → `'BE68 5390 0754 7034'`; `'be68539007547034'` →
  `'be68 5390 0754 7034'`; `'NO9386011117947'` → `'NO93 8601 1117 947'`;
  `'BR1800360305000010009795493C1'` → `'BR18 0036 0305 0000 1000 9795 493C 1'`;
  `'BE68539007547035'` → unchanged; `'garbage text'` → unchanged.
  **Quirk (observable):** because grouping runs on the raw input, an already-spaced
  or punctuated valid input is regrouped with its separators counted as characters:
  `'BE68 5390 0754 7034'` → `'BE68  539 0 07 54 7 034'`;
  `'BE68-5390-0754-7034'` → `'BE68 -539 0-07 54-7 034'`;
  `'be 68539007547034'` → `'be 6 8539 0075 4703 4'`.
  Callers inside the module always normalize first (R16), which avoids the quirk.
- **Evidence:** src:15-22; `evidence/trace_normalize_pretty_bban.txt` (pretty_iban).
- **Limits:** Whether the rebuild keeps the quirk is a product decision. The spec
  records the observed behavior.

### R13 — BBAN extraction (pure function)
- **Behavior:** Returns the normalized value (R1) with its first 4 characters
  removed. It does **not** validate, and never raises for strings/`None`. Case is
  kept. Examples: `'BE68 5390 0754 7034'` → `'539007547034'`;
  `'GB82 WEST 1234 5698 7654 32'` → `'WEST12345698765432'`; `'US12345678'` →
  `'345678'`; `'BE6'` → `''`; `None` → `''`; `'hello world'` → `'oworld'`.
- **Evidence:** src:24-29; `evidence/trace_normalize_pretty_bban.txt` (get_bban_from_iban).
- **Limits:** none.

### R14 — BBAN for a bank account record
- **Behavior:** For an account whose type is `'iban'`, returns R13 applied to its
  account number. For any other type, raises the user error with exactly
  `Cannot compute the BBAN because the account number is not an IBAN.` The type is
  not re-checked against the number, so a record already marked `'iban'` with
  number `'XX'` returns `''`.
- **Evidence:** src:68-71; `evidence/trace_model.txt` (get_bban() method).
- **Limits:** Record state was simulated. The record type is computed from the
  account number by the R15 decision (base:77, base:102-105; rev-2 compute trace), so
  with only base + base_iban installed an `'iban'` type comes from a number that
  passed validation. The `'XX'` example therefore only arises if the type is set by
  other means (not traced).

### R15 — Account-type decision (`'iban'`)
- **Behavior:** An account number is classified as `'iban'` exactly when R2–R9
  validation succeeds on it (so spaced/lowercase input qualifies). Otherwise it is
  classified `'bank'`. The base classification alone returns `'bank'` for every
  input, whatever it is (valid IBAN, garbage, `''`, `None`, `False`, `0`, even `12`),
  and base_iban hands it the number unchanged.
  Supported account types (value, label), in this order:
  base alone `[('bank', 'Normal')]`; with base_iban `[('bank', 'Normal'), ('iban', 'IBAN')]`.
  Both labels go through translation. A public accessor returns the same list.
  A bank account record's type is computed from its account number with this
  decision (recomputed when the number changes), and the type field offers this list
  as its choices.
  Examples (installed): `'BE68539007547034'`, `'be68 5390 0754 7034'` → `'iban'`;
  `'BE68539007547035'`, `'US1234'`, `'123-456-789'`, `'KW'+28×'0'` (R4a), `''`,
  `None`, `False`, `0` → `'bank'`. Record with number `'be68 5390 0754 7034'` → type
  `'iban'`; `'123456'` or `False` → `'bank'`.
- **Evidence:** src:54-66; base:68-74 (type list, accessor), base:112-116 (base
  classification), base:77 and base:102-105 (type computed from number);
  `evidence/trace_acc_type_rev2.txt` (BASE alone, INSTALLED, compute);
  `evidence/trace_model.txt` (rev 1, now consistent with the real base).
- **Limits:** Translated labels were not traced (stub returns the English source).
  Other modules that also override the classification or the list are out of scope.
  Truthy non-string numbers: see R18 (`TypeError`, not `'bank'`). The "recomputed
  when the number changes" part is read from the field declaration
  (base:77, 102); the ORM recompute itself was not run.

### R16 — Stored account number cleanup on create/update
- **Behavior:** When an account number is supplied (truthy) on create or update and
  it is a valid IBAN, the stored value becomes `pretty_iban(normalize_iban(value))`:
  separators removed, then groups of 4 with single spaces, **case preserved**.
  Invalid or non-IBAN numbers, empty/False values and missing keys are passed through
  untouched. Create applies this to each record of a batch independently.
  Examples: `'no93-8601-1117-947'` → `'no93 8601 1117 947'`;
  `'be68 5390 0754 7034'` → `'be68 5390 0754 7034'`; `'de89370400440532013000'` →
  `'de89 3704 0044 0532 0130 00'`; `'BE68539007547035'`, `'123 456'`, `''`, `False`
  → unchanged.
- **Evidence:** src:73-91; `evidence/trace_model.txt` (create, write).
- **Limits:** Only the values handed to the parent create/write were observed
  (stubbed parent in rev 1; real base parent in rev 2, see R16a). The base model
  changes nothing in `acc_number` itself except in the case of R16a point 4.

### R16a — Interaction with the base "sanitized account number"
- **Behavior:** The base model keeps a second, derived value next to each account
  number: the number with every character removed that is not Unicode alphanumeric
  **and** not underscore (underscore is **kept**), then uppercased (Unicode rules,
  e.g. `ß` → `SS`); an empty/falsy number gives `False`. It is computed on create and
  update from the value that reaches the base model, i.e. **after** R16. Proven
  consequences with base_iban installed:
  1. For a valid IBAN input, the derived value equals the uppercase of the R1
     normalized input (7/7 traced inputs, including spaced, tabbed, punctuated and
     lowercase ones). Example: `'be68 5390 0754 7034'` → stored number
     `'be68 5390 0754 7034'`, derived `'BE68539007547034'`.
  2. Underscores differ from base alone: `'BE68_5390_0754_7034'` → stored
     `'BE68 5390 0754 7034'`, derived `'BE68539007547034'` (installed) vs stored
     `'BE68_5390_0754_7034'`, derived `'BE68_5390_0754_7034'` (base alone).
  3. Numbers that are not valid IBANs are untouched by R16, so the derived value is
     the base one: `'123 456'` → `'123456'`; `'abc_def'` → `'ABC_DEF'`;
     `'BE68539007547035'` → `'BE68539007547035'`; `''`/`False` → `False`; no number
     key → no derived key.
  4. A number supplied only under the derived-value key is moved by the base model
     into the account number **after** R16 has run, so it is **not** reformatted:
     `{sanitized: 'BE68539007547034'}` → stored number `'BE68539007547034'` (compact),
     while `{number: 'BE68539007547034'}` → `'BE68 5390 0754 7034'`. If both keys are
     given, the derived-key value replaces the (already reformatted) number:
     `{number: 'be68 5390 0754 7034', sanitized: 'XYZ'}` → number `'XYZ'`, derived `'XYZ'`.
  5. Searching on the account number with a value compares the derived form of the
     searched value: `'be68 5390 0754 7034'` and `'BE68 5390 0754 7034'` both search
     `'BE68539007547034'`; a list of values is sanitized element-wise. (Base behavior,
     not changed by base_iban.)
  6. The base model declares uniqueness of (derived value, partner) with the message
     `The combination Account Number/Partner must be unique.` Combined with point 2,
     `'BE68_5390_0754_7034'` and `'BE68 5390 0754 7034'` for the same partner have the
     same derived value with base_iban installed, but different ones with base alone.
- **Evidence:** base:10-13 (sanitize), base:79, base:97-100 (derived field),
  base:91-95 (uniqueness), base:123-130 (search), base:132-146 (create/write);
  src:73-91; `evidence/trace_sanitize_rev2.txt` (sanitize function, create BASE vs
  INSTALLED, write, search condition, property check, exhaustive check that the base
  sanitize keeps exactly `isalnum()` or `_` characters: 0 mismatches).
- **Limits:** No database: the uniqueness constraint (point 6) was not executed; only
  the derived values it would compare were traced. Search was traced up to the
  rewritten condition, not run against data. Real ORM ordering of compute vs
  create overrides was simulated by the class composition described at the top.

### R17 — Constraint on IBAN-typed accounts
- **Behavior:** Whenever the account number changes, each account whose type is
  `'iban'` is validated (R2–R9), and the same validation error and message propagate
  (e.g. `This IBAN does not pass the validation check, please verify it.`). Accounts
  of other types are not checked.
- **Evidence:** src:93-97; `evidence/trace_model.txt` (_check_iban constraint).
- **Limits:** Record state and the trigger mechanism were simulated. With only base
  + base_iban, the type is computed from the number by R15 (base:77, 102-105), and
  R15 yields `'iban'` only for numbers that pass validation, so this constraint
  cannot fail through that path. This is derived from the code and the rev-2 compute
  trace, not from an end-to-end ORM run.

### R18 — Inputs that are not `str` / `None` (informative, outside contract)
- **Behavior:** Traced per type for normalization, validation, boolean check,
  pretty formatting, BBAN extraction, account-type decision (installed) and the base
  sanitize:
  - **Falsy** values (`False`, `0`, `0.0`, `b''`, `[]`, `()`, `{}`, `set()`) behave
    exactly like `None`: normalize → `''`; validate → `There is no IBAN code.`;
    boolean check → False; pretty → returns the input object unchanged (e.g. `0` → `0`,
    `[]` → `[]`); BBAN → `''`; account type → `'bank'`; base sanitize → `False`.
  - **Truthy** non-strings (`True`, `12`, `1.5`, `b'BE68539007547034'`,
    `bytearray(b'BE68')`, `['BE68539007547034']`, `{'a': 1}`, `object()`) raise
    `TypeError` from **every** function, including the boolean check and pretty
    formatting (which otherwise never raise) and the account-type decision (which
    otherwise falls back to `'bank'`). Base alone returns `'bank'` even for `12`.
- **Evidence:** src:12-13, 15-22, 31-32, 60-66, 99-104; base:10-13, 112-116;
  `evidence/trace_nonstr_rev2.txt`; `evidence/trace_acc_type_rev2.txt`.
- **Limits:** The `TypeError` texts are Python 3.13 runtime messages, not part of
  the contract. Only the listed types were traced. Whether the real ORM can hand a
  non-string to these functions was not traced.
