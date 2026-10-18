# SPEC: IBAN / BBAN behavior (gated handoff for room B, Revision 2.1)

## Revision 2.1 — changelog
- **R4a (clarified):** U+212A in position 1 or 2 whose pair, read with `K`, is not a
  table code gives the R4 country message (new consequence 1a).

## Revision 2 — changelog (behavior changes only)
- **R4a (new):** the country check accepts exactly one non-ASCII character,
  U+212A KELVIN SIGN, as the letter K. Such a value then always fails with the R7
  format message. Every other non-ASCII character in the first two positions gives
  the R4 country message. R4's "unspecified" note is replaced by R4a.
- **R15 (completed):** the non-IBAN result is now specified: `'bank'`, for every
  `str`/`None` input. Supported types are `[('bank', 'Normal'), ('iban', 'IBAN')]`.
  `account_type` keeps its optional `fallback` (default `'bank'`).
- **API names fixed** for R14 (`account_bban`), R15 list append
  (`add_iban_account_type`), R15 list (`supported_account_types`), R16 record/batch
  (`sanitize_account_vals`, key `'acc_number'`), R17 (`check_iban_account`).
- **R16 (clarified):** only the account-number key is read or changed; a valid IBAN
  under any other key is left as it is.
- **R8 (clarified):** the "exactly 10" letter check-digit pairs are counted over the
  alphabet `0-9A-Z`. All 10 are listed.
- **R18 (new, informative):** observed behavior for non-`str` inputs. Outside the
  contract. Do not test.
- **Host notes (new, informative):** what the host does after R16 runs. Not part of
  this contract. Do not test.

Scope: pure IBAN functions, the account-type decision, and how a stored account
number is cleaned up. Out of scope: UI widget, views, translations, demo data,
persistence plumbing. Every rule below was gated as proven observed behavior.
Where a rule says "unspecified", do not guess and do not test it.

---

## 1. Target public API

| Function | Signature | Behavior |
|---|---|---|
| `normalize_iban` | `(value: str \| None) -> str` | R1 |
| `validate_iban` | `(value: str \| None) -> None`, raises `IbanValidationError(message: str)` | R2–R10 |
| `is_iban` | `(value: str \| None = '') -> bool` | R11 (True iff `validate_iban` raises nothing, False iff it raises `IbanValidationError`) |
| `pretty_iban` | `(value: str \| None) -> str \| None` | R12 |
| `get_bban` | `(value: str \| None) -> str` | R13 |
| `iban_template` | `(country_code: str) -> str \| None` | R5 table: the display template. The code must be exactly one table code, ASCII letters in either case; anything else (other lengths, non-ASCII characters including U+212A) gives `None` |
| `account_bban` | `(acc_type: str, acc_number: str \| None) -> str`, raises `NotAnIbanError` | R14 |
| `account_type` | `(acc_number: str \| None, fallback: str = 'bank') -> str` | R15: `'iban'`, otherwise `fallback` (default `'bank'`) |
| `supported_account_types` | `() -> list[tuple[str, str]]` | R15: `[('bank', 'Normal'), ('iban', 'IBAN')]` |
| `add_iban_account_type` | `(types: list[tuple[str, str]]) -> list[tuple[str, str]]` | R15: the entries of `types` in order, then `('iban', 'IBAN')` |
| `sanitize_account_number_for_storage` | `(value: str \| None) -> str \| None` | R16, one value |
| `sanitize_account_vals` | `(vals: dict \| list[dict], key: str = 'acc_number') -> dict \| list[dict]` | R16, one record (dict) or a batch (list of dicts) |
| `check_iban_account` | `(acc_type: str, acc_number: str \| None) -> None`, raises `IbanValidationError` | R17, one account |

Error kinds: `IbanValidationError` (validation failure, carries the message) and
`NotAnIbanError` (user error, needed only for R14).
The contract input domain is `str` or `None` for every value argument. Behavior
for other input types is outside the contract (R18 records what was observed, as
information only). Do not test non-`str` inputs.

---

## 2. Rules

### R1 — Normalization
Keeps exactly the characters that are Unicode alphanumeric (Python `str.isalnum()`
semantics) and removes every other character, underscore included. So ASCII and
non-ASCII letters and digits are kept (`é`, `ß`, `٣`, `²`). Case is **not** changed.
`None` and any falsy value (e.g. `''`, `0`) give `''`. A truthy non-string
value (e.g. the int `12`) raises `TypeError`. The message text is not part of the
contract.
Examples: `'BE68 5390 0754 7034'` → `'BE68539007547034'`;
`'be68-5390.0754/7034'` → `'be68539007547034'`; `'a_b c\td\ne'` → `'abcde'`;
`'é ß ٣ ²'` → `'éß٣²'`; `'!!!'` → `''`; `None` → `''`;
`'DE89 3704 0044 0532 0130 00'` → `'DE89370400440532013000'`.

### R2 — Validation input is normalized first
`validate_iban` applies R1 before every check. So spaces, tabs, newlines,
non-breaking spaces (` `) and `- . / ( ) ! _` anywhere in the input are
ignored, and lowercase or mixed-case input is accepted.
Accepted: `'BE68 5390 0754 7034'`, `'be68 5390 0754 7034'`, `'be68539007547034'`,
`'Be68-5390-0754-7034'`, `'BE68.5390.0754.7034'`, `'BE68_5390_0754_7034'`,
`' BE68\t5390\n0754 7034 '`, `'BE68 5390 0754 7034'`,
`'BE68/5390(0754)7034!'`, `'gb82 west 1234 5698 7654 32'`.
A prefix word is not stripped: `'IBAN BE68 5390 0754 7034'` → country error (R4).

### R3 — Empty input
If the normalized value is empty, raises `IbanValidationError` with exactly
`There is no IBAN code.`
Inputs: `None`, `''`, `'   '`, `'---'`, `'_'`, `' '`.

### R4 — Country support
The first two normalized characters, ignoring ASCII case, must be one of the 70
country codes in the R5 table. If not, raises `IbanValidationError` with exactly
`The IBAN is invalid, it should begin with the country code`
This also happens for a 1-character input (`'B'`), inputs that start with digits
(`'12345678901234'`, `'1E68539007547034'`), and codes not in the table
(`'US12345678901234567890'`, `'LC55HEMM000100010012001200023015'`,
`'EG380019000500000000263180002'`, `'SC18SSCB11010000000000001497USD'`, `'ZZ00'`).
ASCII letters match in either case. For non-ASCII characters in these two
positions, see R4a.

### R4a — Non-ASCII characters in the country-code positions
Over the whole Unicode range, exactly one non-ASCII character is accepted in the
first two positions of the normalized value: **U+212A KELVIN SIGN**, which matches
as the letter `K`. Consequences:
1. If position 1 or 2 is U+212A and, reading it as `K`, the pair is a table code
   (only `DK`, `KW`, `KZ`, `MK`, `PK`, `SK`, `XK` contain a K), the country check
   passes. Validation then **always** fails with the R7 format message, using the
   matched country's template exactly as in the R5 table. This holds at any length
   (correct length, and length −1/+1), and even when the same value with an ASCII
   `K` would be a valid IBAN. The checksum message never appears.
1a. If position 1 or 2 is U+212A and, reading it as `K`, the pair is **not** a table
   code, the country check fails like any other unsupported code: R4 country
   message. This holds whatever the other character is (letter of either case, digit,
   or a second U+212A) and at any length, including a 1- or 2-character input.
   Examples: `'\u212aE68539007547034'`, `'B\u212a68539007547034'`,
   `'\u212ae68539007547034'`, `'\u212aA00'`, `'A\u212a00'`, `'\u212a\u212a00'`,
   `'\u212a1' + 14 × '0'`, `'1\u212a' + 14 × '0'`, `'\u212aE'`, `'B\u212a'`,
   `'\u212a'` → country message.
2. Any other non-ASCII character in position 1 or 2 gives the R4 country message.
   This includes characters whose uppercase or case-folded form is ASCII, such as
   U+0131 `ı`, U+017F `ſ`, U+00DF `ß`, U+0130 `İ`, fullwidth U+FF22 `Ｂ` and
   titlecase U+01C5 `ǅ`.
3. U+212A after position 2 is just a non-ASCII character: R6 (format message).
Downstream: `is_iban` → False, `pretty_iban` returns the input unchanged,
`account_type` → `'bank'`, `get_bban` still drops the first 4 characters (R13).
Examples (U+212A is written as the Python escape `'\u212a'`):
`'\u212aW' + 28 × '0'` (30 chars) → R7 message with `KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC`;
`'\u212aw' + 28 × '0'` → same; `'\u212aW' + 27 × '0'` and `'\u212aW' + 29 × '0'` → same;
`'D\u212a' + 16 × '0'` → R7 message with `DKkk BBBB CCCC CCCC CC`;
`'\u212aZ' + 18 × '0'` → `KZkk BBBC CCCC CCCC CCCC`; `'M\u212a' + 17 × '0'` → `MKkk BBBC CCCC CCCC CKK`;
`'P\u212a' + 22 × '0'` → `PKkk BBBB CCCC CCCC CCCC CCCC`; `'S\u212a' + 22 × '0'` → `SKkk BBBB SSSS SSCC CCCC CCCC`;
`'X\u212a' + 18 × '0'` → `XKkk BBBB CCCC CCCC CCCC`;
ASCII control `'KW' + 28 × '0'` → checksum message;
`'KW81CBKU0000000000001234560101'` (valid) with its first `K` replaced by U+212A → R7
message; `'D\u212a5000400440116243'` → R7 message (`'DK5000400440116243'` is valid);
`'\u0130E68539007547034'`, `'\uff22E68539007547034'`, `'\u01c5E00'` → country message.
Limits: established with Python 3.13 Unicode data. Another Unicode version could
change the list.

### R5 — Per-country length (template table)
Each supported country has a display template. The normalized IBAN length must
equal the template length with spaces removed. This check is combined with R6, and
either failure raises the R7 message. Only **length** is enforced. The letters in
the template (B, S, C, k, K, X, ...) are **not** checked against the content (R8).
For every country, lengths n−1 and n+1 raise the R7 message, and length n passes
this check.
Table (country → required compact length → display template, verbatim as it
appears in the R7 message):

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

### R6 — Character set after normalization
The normalized value must contain only ASCII letters (either case) and ASCII
digits. A non-ASCII alphanumeric character that survived R1 raises the R7 message,
even when the length is right. Examples (all → R7 message with the BE template):
`'BE6853900754703é'`, `'BE68539007547٣٤'`, `'BE6853900754703ß'`,
`'BE685390075470²³'`, `'BE0000000000000é'`.

### R7 — Format/length error message
When R5 or R6 fails, raises `IbanValidationError` with exactly:
`The IBAN does not seem to be correct. You should have entered something like this <TEMPLATE>\nWhere B = National bank code, S = Branch code, C = Account No, k = Check digit`
where `<TEMPLATE>` is the country's display template from R5 (as in the table,
spaces kept) and `\n` is a real newline character. Examples: `'BE68'`, `'BE'`,
`'BE1'`, `'BE00'`, `'BE6853900754703'`, `'BE685390075470344'` → template
`BEkk BBBC CCCC CCXX`; `'DE8937040044053201300'` → `DEkk BBBB BBBB CCCC CCCC CC`;
`'NO938601111794'` → `NOkk BBBB CCCC CCK`;
`'MT84MALT011000012345MTLCAST001S0'` → `MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC`.
Limits: only the untranslated English text is specified.

### R8 — Internal structure is not enforced
Apart from the two-letter country code, the length and the ASCII alphanumeric set,
positions are not type-checked. Letters may appear where the template shows digits,
the BBAN may be all zeros, and the two check-digit positions (3–4) may even be
letters. Any such value passes when the checksum (R9) holds.
Accepted: `'BE57ABCDEFGHIJKL'`, `'be57abcdefghijkl'`, `'DE51XXXXXXXXXXXXXXXXXX'`,
`'NO1300000000000'`, `'BE54000000000000'`, `'AZ' + 26 × '0'`.
Letter check digits for BBAN `539007547034`: over the 36-symbol alphabet `0-9A-Z`
(uppercase letters and digits), exactly 10 pairs that are not all digits are
accepted: `I6`, `OX`, `PU`, `QR`, `RO`, `S3`, `SL`, `TI`, `UF`, `VC`
(e.g. `'BEI6539007547034'`). The only all-digit pair is `68`. Lowercase or
mixed-case spellings of these pairs are the same pairs (R9 is case-insensitive) and
are also accepted; count them separately only if you count over `0-9A-Za-z`, which
gives 36.
Limits: shown on BE, DE, NO, AZ. Other countries are assumed to behave the same.

### R9 — Checksum (ISO 13616 / ISO 7064 MOD 97-10)
Once R3–R6 pass, the value must satisfy the standard IBAN check digit condition:
with the first four characters moved to the end and each letter valued
A/a = 10 … Z/z = 35 (digits keep their value), the resulting number mod 97 equals 1.
This applies to every position, check digits included, case-insensitively.
Otherwise raises `IbanValidationError` with exactly
`This IBAN does not pass the validation check, please verify it.`
On success `validate_iban` returns `None`.
Accepted: BE68539007547034, DE89370400440532013000, FR1420041010050500013M02606,
GB82WEST12345698765432, NL91ABNA0417164300, CH9300762011623852957, NO9386011117947,
MT84MALT011000012345MTLCAST001S, BR1800360305000010009795493C1,
ES9121000418450200051332, IT60X0542811101000000123456, MU17BOMM0101101030300200000MUR,
SA0380000000608010167519, PL61109010140000071219812874, AT611904300234573201,
XK051212012345678906, PS92PALS000000000400123456702, JO94CBJO0010000000000131000302,
QA58DOHB00001234567890ABCDEFG, KW81CBKU0000000000001234560101,
UA213223130000026007233566001, IS140159260076545510730339.
Rejected (checksum message): BE68539007547035, BE00539007547034, BE01539007547034,
BE99539007547034, DE88370400440532013000, GB82WEST12345698765433,
`'BE68 5390 0754 703X'`, BE00000000000000.
There is no special rule for check digits `00`, `01` or `99`: they pass or fail the
checksum like any other value.

### R10 — Order of checks
The first failing check decides the message: empty (R3) → country (R4) →
length/charset (R5/R6, one R7 message) → checksum (R9).
Examples: `'US'`, `'XX0'`, `'US00'` → country message; `'BE'`, `'BE1'` → R7 message;
`'BE00000000000000'` → checksum message; `''` → empty message.

### R11 — Boolean check (`is_iban`)
Returns `True` when `validate_iban` succeeds and `False` when it raises
`IbanValidationError`. Calling it with no argument returns `False`.
Examples: `'BE68539007547034'` → True; `'be68 5390 0754 7034'` → True;
`'BE68539007547035'`, `''`, `None` → False.
Limits: only `str`/`None` inputs are specified.

### R12 — Pretty (display) formatting
If the input is a valid IBAN (R2–R9), returns the input **as given (not
normalized)**, cut into consecutive groups of 4 characters joined by single spaces.
The last group may be shorter, and case is preserved. If the input is invalid,
returns it unchanged (`None` → `None`, `''` → `''`). For `str`/`None` input it
never raises.
Examples: `'BE68539007547034'` → `'BE68 5390 0754 7034'`; `'be68539007547034'` →
`'be68 5390 0754 7034'`; `'DE89370400440532013000'` → `'DE89 3704 0044 0532 0130 00'`;
`'FR1420041010050500013M02606'` → `'FR14 2004 1010 0505 0001 3M02 606'`;
`'NO9386011117947'` → `'NO93 8601 1117 947'`;
`'BR1800360305000010009795493C1'` → `'BR18 0036 0305 0000 1000 9795 493C 1'`;
`'BE68539007547035'`, `'US12345678'`, `'garbage text'` → unchanged.
**Quirk (required observed behavior):** grouping runs on the raw input, so in a
valid input that already has separators, each separator counts as a character:
`'BE68 5390 0754 7034'` → `'BE68  539 0 07 54 7 034'`;
`'BE68-5390-0754-7034'` → `'BE68 -539 0-07 54-7 034'`;
`'be 68539007547034'` → `'be 6 8539 0075 4703 4'`.
Formatting a normalized value avoids the quirk (R16):
`pretty_iban(normalize_iban(x))` gives `'be68 5390 0754 7034'` for
`'be68 5390 0754 7034'`, `'BE68 5390 0754 7034'` for `'BE68-5390-0754-7034'`,
`'DE89 3704 0044 0532 0130 00'` for `'DE89 3704 0044 0532 0130 00'`, and
`'NO93 8601 1117 947'` for `'NO93 8601 1117 947'`.

### R13 — BBAN extraction (`get_bban`, pure)
Returns the normalized value (R1) without its first 4 characters. It does **not**
validate and never raises for `str`/`None`. Case is kept.
Examples: `'BE68539007547034'`, `'BE68 5390 0754 7034'`, `'be68-5390-0754-7034'` →
`'539007547034'`; `'GB82 WEST 1234 5698 7654 32'` → `'WEST12345698765432'`;
`'US12345678'` → `'345678'`; `'BE6'` → `''`; `''` → `''`; `None` → `''`;
`'hello world'` → `'oworld'`.

### R14 — BBAN for a bank account record (`account_bban`)
For an account whose type is `'iban'`, returns R13 applied to its account number.
For any other type, raises `NotAnIbanError` with exactly
`Cannot compute the BBAN because the account number is not an IBAN.`
The type is not re-checked against the number.
Examples: type `'iban'`, number `'BE68 5390 0754 7034'` → `'539007547034'`;
type `'iban'`, number `'XX'` → `''`; any non-`'iban'` type (whatever the number,
e.g. `'BE68 5390 0754 7034'` or `'123456'`) → `NotAnIbanError`. The type comparison
is exact: `'bank'`, `'IBAN'`, `''` and `None` are all "other type".

### R15 — Account-type decision and supported types
- `account_type(acc_number)`: `'iban'` exactly when `acc_number` passes
  `validate_iban` (R2–R9), so spaced or lowercase input qualifies. Otherwise
  `'bank'`, for every `str`/`None` input.
- With the optional `fallback` argument, the non-IBAN result is `fallback`,
  returned unchanged (for hosts that classify non-IBAN numbers differently). The
  default `fallback` is `'bank'`.
- Examples: `'BE68539007547034'`, `'be68 5390 0754 7034'` → `'iban'`;
  `'BE68539007547035'`, `'US1234'`, `'123-456-789'`, `'KW' + 28 × '0'`, the R4a
  inputs, `''`, `None` → `'bank'`; `account_type('US1234', fallback='X')` → `'X'`;
  `account_type('BE68539007547034', fallback='X')` → `'iban'`.
- `supported_account_types()` returns exactly `[('bank', 'Normal'), ('iban', 'IBAN')]`
  (value, label), in that order. Only the untranslated labels are specified.
- `add_iban_account_type(types)` returns the entries of `types` in their order,
  followed by `('iban', 'IBAN')` as the last entry. So
  `add_iban_account_type([('bank', 'Normal')]) == supported_account_types()`, and
  `add_iban_account_type([])` → `[('iban', 'IBAN')]`. Unspecified (do not test):
  whether the argument list is modified, and what happens if `types` already
  contains an `'iban'` entry.

### R16 — Stored account number cleanup on create/update
`sanitize_account_number_for_storage(value)` applies the rule to one value.
`sanitize_account_vals(vals, key='acc_number')` applies it to the value stored
under `key` in one record (`vals` is a dict) or in each record of a batch (`vals` is
a list of dicts). It returns the same shape: a dict for a dict, a list of the same
length and order for a list. Only the return value is specified. Whether the input
dicts are modified in place is unspecified (do not test).
When an account number is supplied and truthy, and it is a valid IBAN (R2–R9), the
value to store becomes `pretty_iban(normalize_iban(value))`: separators removed,
then groups of 4 joined by single spaces, **case preserved**. Invalid or non-IBAN
numbers, empty/`False` values and absent account-number keys pass through
untouched, and other fields are untouched. On a batch create each record is handled
independently.
Examples: `'no93-8601-1117-947'` → `'no93 8601 1117 947'`;
`'be68 5390 0754 7034'` → `'be68 5390 0754 7034'`;
`'de89370400440532013000'` → `'de89 3704 0044 0532 0130 00'`;
`'BE68539007547035'`, `'DE89370400440532013001'`, `'123 456'`, `''`, `False` →
unchanged; a record with no account number (e.g. only `name`) → unchanged.
Only the account-number key is read or changed. A value under any other key is left
as it is, even a valid IBAN: `{'other': 'be68539007547034'}` → unchanged.
Batch example: `[{'acc_number': 'no93-8601-1117-947'}, {'acc_number': '123 456'}, {}]`
→ `[{'acc_number': 'no93 8601 1117 947'}, {'acc_number': '123 456'}, {}]`.
Limits: only the value handed on for storage is specified. Any further host-side
processing is unspecified.

### R17 — Constraint on IBAN-typed accounts (`check_iban_account`)
When the account number of accounts is set or changed, each account whose type is
`'iban'` is validated with `validate_iban`, and its `IbanValidationError` (same
message) propagates. Accounts of any other type are not checked.
`check_iban_account(acc_type, acc_number)` checks one account: it returns `None`,
or raises the `validate_iban` error when `acc_type == 'iban'` (exact comparison, as
in R14). Callers check several accounts by calling it for each one.
Examples: type `'iban'`, `'BE68 5390 0754 7034'` → ok; type `'iban'`,
`'BE68539007547035'` → `This IBAN does not pass the validation check, please verify it.`;
non-`'iban'` type with `'BE68539007547035'` or `'garbage'` → ok.
Note: when the account type is always obtained from `account_type` (R15), an
`'iban'` type only comes with a number that passes validation, so R14's `'XX'` case
and an R17 failure only arise when the type is set by other means.

### R18 — Non-`str` inputs (informative, outside the contract, do not test)
Observed for normalization, validation, the boolean check, pretty formatting, BBAN
extraction and the account-type decision:
- Falsy values (`False`, `0`, `0.0`, `b''`, `[]`, `()`, `{}`, `set()`) behave like
  `None`: normalize → `''`; validate → `There is no IBAN code.`; boolean check →
  False; pretty → the input object unchanged; BBAN → `''`; account type → `'bank'`.
- Truthy non-strings (`True`, `12`, `1.5`, bytes, bytearray, non-empty lists or
  dicts, arbitrary objects) raise `TypeError` from every one of these functions,
  including the boolean check and pretty formatting. The message text is not
  specified.
A rebuild may reproduce this. It is not required.

---

## 3. Host notes (informative, not part of this contract, do not test)
These describe what a host bank-account model does with the value after R16. They
are given for integrators only.
- The host keeps a derived, search-oriented form of each stored account number:
  the number with every character removed that is neither Unicode alphanumeric nor
  underscore (underscores are kept), then uppercased with Unicode rules (`ß` →
  `SS`). An empty or false number gives `False`. It is computed from the value R16
  produced. So for a valid IBAN it equals the uppercase of the R1-normalized input
  (`'be68 5390 0754 7034'` → `'BE68539007547034'`), while a non-IBAN keeps its
  underscores (`'abc_def'` → `'ABC_DEF'`). Because R16 removes underscores from
  valid IBANs, `'BE68_5390_0754_7034'` and `'BE68 5390 0754 7034'` get the same
  derived form with this module, and different ones without it.
- A value supplied directly for the derived field is moved into the account number
  by the host after R16 has run, so it is not reformatted, and it overrides an
  account number given in the same call.
- Searching on the account number compares derived forms.
- The host requires (derived form, account holder) to be unique, with the message
  `The combination Account Number/Partner must be unique.`
- The host computes each record's account type from its number with R15 and offers
  the R15 list as the choices.
