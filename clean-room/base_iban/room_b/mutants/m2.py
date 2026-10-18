"""IBAN / BBAN helpers rebuilt from SPEC.md Revision 2 (rules R1-R17, R4a).

Stdlib only.
"""

__all__ = [
    'IbanValidationError', 'NotAnIbanError',
    'normalize_iban', 'validate_iban', 'is_iban', 'pretty_iban', 'get_bban',
    'iban_template', 'account_type', 'supported_account_types',
    'sanitize_account_number_for_storage',
    'account_bban', 'check_iban_account', 'add_iban_account_type',
    'sanitize_account_vals',
]


class IbanValidationError(Exception):
    """Validation failure; carries the exact message (R3, R4, R7, R9)."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NotAnIbanError(Exception):
    """User error raised when a BBAN is requested for a non-IBAN account (R14)."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


# R5 table: country code -> display template (verbatim).
_TEMPLATES = {
    'AD': 'ADkk BBBB SSSS CCCC CCCC CCCC',
    'AE': 'AEkk BBBC CCCC CCCC CCCC CCC',
    'AL': 'ALkk BBBS SSSK CCCC CCCC CCCC CCCC',
    'AT': 'ATkk BBBB BCCC CCCC CCCC',
    'AZ': 'AZkk BBBB CCCC CCCC CCCC CCCC CCCC',
    'BA': 'BAkk BBBS SSCC CCCC CCKK',
    'BE': 'BEkk BBBC CCCC CCXX',
    'BG': 'BGkk BBBB SSSS DDCC CCCC CC',
    'BH': 'BHkk BBBB CCCC CCCC CCCC CC',
    'BR': 'BRkk BBBB BBBB SSSS SCCC CCCC CCCT N',
    'BY': 'BYkk BBBB AAAA CCCC CCCC CCCC CCCC',
    'CH': 'CHkk BBBB BCCC CCCC CCCC C',
    'CR': 'CRkk BBBC CCCC CCCC CCCC CC',
    'CY': 'CYkk BBBS SSSS CCCC CCCC CCCC CCCC',
    'CZ': 'CZkk BBBB SSSS SSCC CCCC CCCC',
    'DE': 'DEkk BBBB BBBB CCCC CCCC CC',
    'DK': 'DKkk BBBB CCCC CCCC CC',
    'DO': 'DOkk BBBB CCCC CCCC CCCC CCCC CCCC',
    'EE': 'EEkk BBSS CCCC CCCC CCCK',
    'ES': 'ESkk BBBB SSSS KKCC CCCC CCCC',
    'FI': 'FIkk BBBB BBCC CCCC CK',
    'FO': 'FOkk CCCC CCCC CCCC CC',
    'FR': 'FRkk BBBB BGGG GGCC CCCC CCCC CKK',
    'GB': 'GBkk BBBB SSSS SSCC CCCC CC',
    'GE': 'GEkk BBCC CCCC CCCC CCCC CC',
    'GI': 'GIkk BBBB CCCC CCCC CCCC CCC',
    'GL': 'GLkk BBBB CCCC CCCC CC',
    'GR': 'GRkk BBBS SSSC CCCC CCCC CCCC CCC',
    'GT': 'GTkk BBBB MMTT CCCC CCCC CCCC CCCC',
    'HR': 'HRkk BBBB BBBC CCCC CCCC C',
    'HU': 'HUkk BBBS SSSC CCCC CCCC CCCC CCCC',
    'IE': 'IEkk BBBB SSSS SSCC CCCC CC',
    'IL': 'ILkk BBBS SSCC CCCC CCCC CCC',
    'IS': 'ISkk BBBB SSCC CCCC XXXX XXXX XX',
    'IT': 'ITkk KBBB BBSS SSSC CCCC CCCC CCC',
    'JO': 'JOkk BBBB NNNN CCCC CCCC CCCC CCCC CC',
    'KW': 'KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC',
    'KZ': 'KZkk BBBC CCCC CCCC CCCC',
    'LB': 'LBkk BBBB CCCC CCCC CCCC CCCC CCCC',
    'LI': 'LIkk BBBB BCCC CCCC CCCC C',
    'LT': 'LTkk BBBB BCCC CCCC CCCC',
    'LU': 'LUkk BBBC CCCC CCCC CCCC',
    'LV': 'LVkk BBBB CCCC CCCC CCCC C',
    'MC': 'MCkk BBBB BGGG GGCC CCCC CCCC CKK',
    'MD': 'MDkk BBCC CCCC CCCC CCCC CCCC',
    'ME': 'MEkk BBBC CCCC CCCC CCCC KK',
    'MK': 'MKkk BBBC CCCC CCCC CKK',
    'MR': 'MRkk BBBB BSSS SSCC CCCC CCCC CKK',
    'MT': 'MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC',
    'MU': 'MUkk BBBB BBSS CCCC CCCC CCCC CCCC CC',
    'NL': 'NLkk BBBB CCCC CCCC CC',
    'NO': 'NOkk BBBB CCCC CCK',
    'OM': 'OMkk BBBC CCCC CCCC CCCC CCC',
    'PK': 'PKkk BBBB CCCC CCCC CCCC CCCC',
    'PL': 'PLkk BBBS SSSK CCCC CCCC CCCC CCCC',
    'PS': 'PSkk BBBB XXXX XXXX XCCC CCCC CCCC C',
    'PT': 'PTkk BBBB SSSS CCCC CCCC CCCK K',
    'QA': 'QAkk BBBB CCCC CCCC CCCC CCCC CCCC C',
    'RO': 'ROkk BBBB CCCC CCCC CCCC CCCC',
    'RS': 'RSkk BBBC CCCC CCCC CCCC KK',
    'SA': 'SAkk BBCC CCCC CCCC CCCC CCCC',
    'SE': 'SEkk BBBB CCCC CCCC CCCC CCCC',
    'SI': 'SIkk BBSS SCCC CCCC CKK',
    'SK': 'SKkk BBBB SSSS SSCC CCCC CCCC',
    'SM': 'SMkk KBBB BBSS SSSC CCCC CCCC CCC',
    'TN': 'TNkk BBSS SCCC CCCC CCCC CCCC',
    'TR': 'TRkk BBBB BRCC CCCC CCCC CCCC CC',
    'UA': 'UAkk BBBB BBCC CCCC CCCC CCCC CCCC C',
    'VG': 'VGkk BBBB CCCC CCCC CCCC CCCC',
    'XK': 'XKkk BBBB CCCC CCCC CCCC',
}

_MSG_EMPTY = 'There is no IBAN code.'
_MSG_COUNTRY = 'The IBAN is invalid, it should begin with the country code'
_MSG_FORMAT = ('The IBAN does not seem to be correct. You should have entered '
               'something like this %s\nWhere B = National bank code, '
               'S = Branch code, C = Account No, k = Check digit')
_MSG_CHECKSUM = 'This IBAN does not pass the validation check, please verify it.'
_MSG_NOT_IBAN = 'Cannot compute the BBAN because the account number is not an IBAN.'

_ASCII_LOWER = 'abcdefghijklmnopqrstuvwxyz'
_ASCII_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_ASCII_ALNUM = frozenset('0123456789' + _ASCII_LOWER + _ASCII_UPPER)
# Upper-case ASCII letters only; non-ASCII characters are left untouched (R4 limit).
_ASCII_UPCASE = str.maketrans(_ASCII_LOWER, _ASCII_UPPER)


# R4a: the only non-ASCII character accepted in the country-code positions.
_KELVIN_SIGN = '\u212a'


def _ascii_upper(text):
    return text.translate(_ASCII_UPCASE)


def _country_template(compact):
    """Template for the country code at the start of ``compact`` (R4, R4a).

    The first two characters must form an R5 table code, ASCII case ignored
    (R4). U+212A KELVIN SIGN in position 1 or 2 is read as ``K`` (R4a.1); every
    other non-ASCII character makes the lookup fail (R4a.2). Returns ``None``
    when the country check fails.
    """
    if len(compact) < 2:
        return None
    pair = compact[:2].replace(_KELVIN_SIGN, 'K')
    return iban_template(pair)


def normalize_iban(value):
    """Return ``value`` with every non-alphanumeric character removed (R1).

    Keeps exactly the characters for which ``str.isalnum()`` is true (ASCII and
    non-ASCII letters/digits), drops everything else including ``_``; case is
    unchanged. ``None`` or any falsy value gives ``''``; a truthy non-string
    value raises ``TypeError``.
    """
    if not value:
        return ''
    if not isinstance(value, str):
        raise TypeError('normalize_iban expects a str or None, got %s'
                        % type(value).__name__)
    return ''.join(ch for ch in value if ch.isalnum())


def iban_template(country_code):
    """Return the R5 display template for ``country_code`` (ASCII case ignored).

    The code must be exactly one R5 table code in ASCII letters of either case;
    anything else (other lengths, non-ASCII characters including U+212A, which
    is accepted only by ``validate_iban`` per R4a) gives ``None``.
    """
    if not isinstance(country_code, str):
        return None
    return _TEMPLATES.get(_ascii_upper(country_code))


def _checksum_ok(compact):
    """ISO 7064 MOD 97-10 condition (R9); ``compact`` is ASCII alphanumeric."""
    rearranged = _ascii_upper(compact[4:] + compact[:4])
    remainder = 0
    for ch in rearranged:
        if ch.isdigit():
            digits = ch
        else:
            digits = str(ord(ch) - ord('A') + 10)
        for d in digits:
            remainder = (remainder * 10 + int(d)) % 97
    return remainder == 1


def validate_iban(value):
    """Validate an IBAN; return ``None`` or raise ``IbanValidationError``.

    Implements R2 (normalize with R1 first), R3 (empty), R4 (supported country,
    ASCII case-insensitive), R4a (U+212A KELVIN SIGN read as ``K`` in the
    country positions; such a value then always fails R6, giving the R7
    message, so the checksum is never reached), R5 (per-country length), R6 (ASCII alphanumeric
    only), R7 (format message with the country template), R8 (no positional
    structure checks), R9 (MOD 97-10 checksum, case-insensitive) and R10 (order:
    empty -> country -> length/charset -> checksum).
    """
    compact = (value or '').replace(' ', '')  # R2
    if not compact:  # R3
        raise IbanValidationError(_MSG_EMPTY)
    template = _country_template(compact)  # R4, R4a
    if template is None:  # R4
        raise IbanValidationError(_MSG_COUNTRY)
    if (len(compact) != len(template.replace(' ', ''))  # R5
            or not all(ch in _ASCII_ALNUM for ch in compact)):  # R6
        raise IbanValidationError(_MSG_FORMAT % template)  # R7
    if not _checksum_ok(compact):  # R9
        raise IbanValidationError(_MSG_CHECKSUM)
    return None


def is_iban(value=''):
    """Return ``True`` if ``validate_iban`` succeeds, ``False`` if it raises
    ``IbanValidationError`` (R11). No argument -> ``False``.
    """
    try:
        validate_iban(value)
    except IbanValidationError:
        return False
    return True


def pretty_iban(value):
    """Group a valid IBAN into blocks of 4 characters (R12).

    A valid input (R2-R9) is returned *as given* (not normalized), cut into
    consecutive 4-character groups joined by single spaces; existing
    separators count as characters (R12 quirk). Invalid input, ``None`` and
    ``''`` are returned unchanged. Never raises for ``str``/``None``.
    """
    if not is_iban(value):
        return value
    return ' '.join(value[i:i + 4] for i in range(0, len(value), 4))


def get_bban(value):
    """Return the normalized value (R1) without its first 4 characters (R13).

    Does not validate; case is kept; never raises for ``str``/``None``.
    """
    return normalize_iban(value)[4:]


def account_bban(acc_type, acc_number):
    """BBAN of a bank account record (R14).

    For ``acc_type == 'iban'`` returns ``get_bban(acc_number)`` (R13) without
    re-checking the number; for any other type raises ``NotAnIbanError``.
    """
    if acc_type != 'iban':
        raise NotAnIbanError(_MSG_NOT_IBAN)
    return get_bban(acc_number)


def account_type(acc_number, fallback='bank'):
    """Account-type decision (R15).

    Returns ``'iban'`` when ``acc_number`` passes ``validate_iban`` (R2-R9),
    otherwise ``fallback`` returned unchanged (default ``'bank'``).
    """
    if is_iban(acc_number):
        return 'iban'
    return fallback


def supported_account_types():
    """Supported account types as (value, label) pairs (R15).

    Returns exactly ``[('bank', 'Normal'), ('iban', 'IBAN')]``, a new list on
    each call.
    """
    return add_iban_account_type([('bank', 'Normal')])


def add_iban_account_type(types):
    """Return the entries of ``types`` in order, then ``('iban', 'IBAN')`` (R15).

    Returns a new list; the argument is not mutated and an existing ``'iban'``
    entry is not de-duplicated (both points unspecified by R15).
    """
    return list(types) + [('iban', 'IBAN')]


def sanitize_account_number_for_storage(value):
    """Value to store for an account number on create/update (R16).

    A truthy valid IBAN (R2-R9) becomes ``pretty_iban(normalize_iban(value))``
    (case preserved); anything else is returned untouched.
    """
    if value and is_iban(value):
        return pretty_iban(normalize_iban(value))
    return value


def sanitize_account_vals(vals, key='acc_number'):
    """Apply R16 to one record's values (dict) or a batch (list of dicts).

    Only ``key`` (default ``'acc_number'``) is read or changed, and only when
    present; other keys are left as they are even if they hold a valid IBAN,
    and records without the key are unchanged (R16). Each batch record is handled independently.
    Returns new dict(s); inputs are not mutated.
    """
    if isinstance(vals, (list, tuple)):
        return [sanitize_account_vals(v, key) for v in vals]
    out = dict(vals)
    if key in out:
        out[key] = sanitize_account_number_for_storage(out[key])
    return out


def check_iban_account(acc_type, acc_number):
    """Constraint on IBAN-typed accounts (R17).

    For ``acc_type == 'iban'`` runs ``validate_iban(acc_number)`` and lets its
    ``IbanValidationError`` propagate; other types are not checked.
    """
    if acc_type == 'iban':
        validate_iban(acc_number)
