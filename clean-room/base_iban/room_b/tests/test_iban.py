"""Tests for iban.py, derived from SPEC.md Revision 2 (rules R1-R17, R4a).

Only the public API named in SPEC section 1 is used. R18 (non-str inputs) and
anything SPEC or ANSWERS marks unspecified are not tested. There are no skipped
tests.
"""
import unittest

from iban import (
    IbanValidationError,
    NotAnIbanError,
    account_bban,
    account_type,
    add_iban_account_type,
    check_iban_account,
    get_bban,
    is_iban,
    iban_template,
    normalize_iban,
    pretty_iban,
    sanitize_account_number_for_storage,
    sanitize_account_vals,
    supported_account_types,
    validate_iban,
)

MSG_EMPTY = 'There is no IBAN code.'
MSG_COUNTRY = 'The IBAN is invalid, it should begin with the country code'
MSG_CHECKSUM = 'This IBAN does not pass the validation check, please verify it.'


def msg_format(template):
    """R7 message for a given display template (SPEC R7, exact text)."""
    return ('The IBAN does not seem to be correct. You should have entered '
            'something like this ' + template + '\nWhere B = National bank code, '
            'S = Branch code, C = Account No, k = Check digit')


# SPEC R5 table: country code | compact length | display template (verbatim).
SPEC_TABLE = """
AD|24|ADkk BBBB SSSS CCCC CCCC CCCC
AE|23|AEkk BBBC CCCC CCCC CCCC CCC
AL|28|ALkk BBBS SSSK CCCC CCCC CCCC CCCC
AT|20|ATkk BBBB BCCC CCCC CCCC
AZ|28|AZkk BBBB CCCC CCCC CCCC CCCC CCCC
BA|20|BAkk BBBS SSCC CCCC CCKK
BE|16|BEkk BBBC CCCC CCXX
BG|22|BGkk BBBB SSSS DDCC CCCC CC
BH|22|BHkk BBBB CCCC CCCC CCCC CC
BR|29|BRkk BBBB BBBB SSSS SCCC CCCC CCCT N
BY|28|BYkk BBBB AAAA CCCC CCCC CCCC CCCC
CH|21|CHkk BBBB BCCC CCCC CCCC C
CR|22|CRkk BBBC CCCC CCCC CCCC CC
CY|28|CYkk BBBS SSSS CCCC CCCC CCCC CCCC
CZ|24|CZkk BBBB SSSS SSCC CCCC CCCC
DE|22|DEkk BBBB BBBB CCCC CCCC CC
DK|18|DKkk BBBB CCCC CCCC CC
DO|28|DOkk BBBB CCCC CCCC CCCC CCCC CCCC
EE|20|EEkk BBSS CCCC CCCC CCCK
ES|24|ESkk BBBB SSSS KKCC CCCC CCCC
FI|18|FIkk BBBB BBCC CCCC CK
FO|18|FOkk CCCC CCCC CCCC CC
FR|27|FRkk BBBB BGGG GGCC CCCC CCCC CKK
GB|22|GBkk BBBB SSSS SSCC CCCC CC
GE|22|GEkk BBCC CCCC CCCC CCCC CC
GI|23|GIkk BBBB CCCC CCCC CCCC CCC
GL|18|GLkk BBBB CCCC CCCC CC
GR|27|GRkk BBBS SSSC CCCC CCCC CCCC CCC
GT|28|GTkk BBBB MMTT CCCC CCCC CCCC CCCC
HR|21|HRkk BBBB BBBC CCCC CCCC C
HU|28|HUkk BBBS SSSC CCCC CCCC CCCC CCCC
IE|22|IEkk BBBB SSSS SSCC CCCC CC
IL|23|ILkk BBBS SSCC CCCC CCCC CCC
IS|26|ISkk BBBB SSCC CCCC XXXX XXXX XX
IT|27|ITkk KBBB BBSS SSSC CCCC CCCC CCC
JO|30|JOkk BBBB NNNN CCCC CCCC CCCC CCCC CC
KW|30|KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC
KZ|20|KZkk BBBC CCCC CCCC CCCC
LB|28|LBkk BBBB CCCC CCCC CCCC CCCC CCCC
LI|21|LIkk BBBB BCCC CCCC CCCC C
LT|20|LTkk BBBB BCCC CCCC CCCC
LU|20|LUkk BBBC CCCC CCCC CCCC
LV|21|LVkk BBBB CCCC CCCC CCCC C
MC|27|MCkk BBBB BGGG GGCC CCCC CCCC CKK
MD|24|MDkk BBCC CCCC CCCC CCCC CCCC
ME|22|MEkk BBBC CCCC CCCC CCCC KK
MK|19|MKkk BBBC CCCC CCCC CKK
MR|27|MRkk BBBB BSSS SSCC CCCC CCCC CKK
MT|31|MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC
MU|30|MUkk BBBB BBSS CCCC CCCC CCCC CCCC CC
NL|18|NLkk BBBB CCCC CCCC CC
NO|15|NOkk BBBB CCCC CCK
OM|23|OMkk BBBC CCCC CCCC CCCC CCC
PK|24|PKkk BBBB CCCC CCCC CCCC CCCC
PL|28|PLkk BBBS SSSK CCCC CCCC CCCC CCCC
PS|29|PSkk BBBB XXXX XXXX XCCC CCCC CCCC C
PT|25|PTkk BBBB SSSS CCCC CCCC CCCK K
QA|29|QAkk BBBB CCCC CCCC CCCC CCCC CCCC C
RO|24|ROkk BBBB CCCC CCCC CCCC CCCC
RS|22|RSkk BBBC CCCC CCCC CCCC KK
SA|24|SAkk BBCC CCCC CCCC CCCC CCCC
SE|24|SEkk BBBB CCCC CCCC CCCC CCCC
SI|19|SIkk BBSS SCCC CCCC CKK
SK|24|SKkk BBBB SSSS SSCC CCCC CCCC
SM|27|SMkk KBBB BBSS SSSC CCCC CCCC CCC
TN|24|TNkk BBSS SCCC CCCC CCCC CCCC
TR|26|TRkk BBBB BRCC CCCC CCCC CCCC CC
UA|29|UAkk BBBB BBCC CCCC CCCC CCCC CCCC C
VG|24|VGkk BBBB CCCC CCCC CCCC CCCC
XK|20|XKkk BBBB CCCC CCCC CCCC
"""

TABLE = []
for _line in SPEC_TABLE.strip().splitlines():
    _cc, _length, _template = _line.split('|')
    TABLE.append((_cc, int(_length), _template))


def mod97(text):
    """Mod-97 of an alphanumeric string, A=10 .. Z=35 (test-side helper)."""
    remainder = 0
    for ch in text.upper():
        for d in str(int(ch, 36)):
            remainder = (remainder * 10 + int(d)) % 97
    return remainder


def make_iban(cc, length):
    """IBAN of the given compact length with an all-zero BBAN and a correct
    check digit (ISO 7064 MOD 97-10). Used to build length-correct inputs."""
    body = '0' * (length - 4)
    check = 98 - mod97(body + cc + '00')
    return '%s%02d%s' % (cc, check, body)


class IbanTestCase(unittest.TestCase):
    def assertValid(self, value):
        self.assertIsNone(validate_iban(value), repr(value))

    def assertInvalid(self, value, message):
        with self.assertRaises(IbanValidationError, msg=repr(value)) as cm:
            validate_iban(value)
        self.assertEqual(cm.exception.message, message, repr(value))


class TestR1Normalize(unittest.TestCase):
    def test_R1_removes_separators_keeps_letters_and_digits(self):
        self.assertEqual(normalize_iban('BE68 5390 0754 7034'), 'BE68539007547034')
        self.assertEqual(normalize_iban('be68-5390.0754/7034'), 'be68539007547034')
        self.assertEqual(normalize_iban('DE89 3704 0044 0532 0130 00'),
                         'DE89370400440532013000')

    def test_R1_removes_underscore_whitespace_and_punctuation(self):
        self.assertEqual(normalize_iban('a_b c\td\ne'), 'abcde')
        self.assertEqual(normalize_iban('!!!'), '')

    def test_R1_keeps_unicode_alphanumerics(self):
        # 'é ß ٣ ²' -> 'éß٣²'  (é, ß, Arabic-Indic digit three, superscript two)
        self.assertEqual(normalize_iban('é ß ٣ ²'),
                         'éß٣²')

    def test_R1_does_not_change_case(self):
        self.assertEqual(normalize_iban('bE'), 'bE')

    def test_R1_none_and_falsy_give_empty(self):
        self.assertEqual(normalize_iban(None), '')
        self.assertEqual(normalize_iban(''), '')
        self.assertEqual(normalize_iban(0), '')

    def test_R1_truthy_non_string_raises_typeerror(self):
        with self.assertRaises(TypeError):
            normalize_iban(12)


class TestR2NormalizeBeforeValidation(IbanTestCase):
    def test_R2_accepted_inputs(self):
        for value in [
            'BE68 5390 0754 7034',
            'be68 5390 0754 7034',
            'be68539007547034',
            'Be68-5390-0754-7034',
            'BE68.5390.0754.7034',
            'BE68_5390_0754_7034',
            ' BE68\t5390\n0754 7034 ',
            'BE68/5390(0754)7034!',
            'gb82 west 1234 5698 7654 32',
            'BE68 5390 0754 7034',  # non-breaking spaces
        ]:
            with self.subTest(value=value):
                self.assertValid(value)

    def test_R2_prefix_word_is_not_stripped(self):
        self.assertInvalid('IBAN BE68 5390 0754 7034', MSG_COUNTRY)


class TestR3Empty(IbanTestCase):
    def test_R3_empty_after_normalization(self):
        for value in [None, '', '   ', '---', '_', ' ']:
            with self.subTest(value=value):
                self.assertInvalid(value, MSG_EMPTY)


class TestR4Country(IbanTestCase):
    def test_R4_unsupported_or_short_country(self):
        for value in [
            'B',
            '12345678901234',
            '1E68539007547034',
            'US12345678901234567890',
            'LC55HEMM000100010012001200023015',
            'EG380019000500000000263180002',
            'SC18SSCB11010000000000001497USD',
            'ZZ00',
        ]:
            with self.subTest(value=value):
                self.assertInvalid(value, MSG_COUNTRY)

    def test_R4_country_code_ignores_ascii_case(self):
        self.assertValid('be68539007547034')
        self.assertValid('Be68539007547034')


class TestR5Length(IbanTestCase):
    def test_R5_table_has_70_countries(self):
        self.assertEqual(len(TABLE), 70)

    def test_R5_template_without_spaces_has_table_length(self):
        for cc, length, template in TABLE:
            with self.subTest(country=cc):
                self.assertEqual(len(template.replace(' ', '')), length)

    def test_R5_iban_template_lookup_ignores_case(self):
        for cc, _length, template in TABLE:
            with self.subTest(country=cc):
                self.assertEqual(iban_template(cc), template)
                self.assertEqual(iban_template(cc.lower()), template)

    def test_R5_iban_template_unknown_code_is_none(self):
        self.assertIsNone(iban_template('US'))
        self.assertIsNone(iban_template('ZZ'))

    def test_R5_iban_template_wrong_length_or_non_ascii_is_none(self):
        for code in ['BEL', 'B', '', 'D\u212a', '\u212aW', 'B\u00e9', '\uff22E']:
            with self.subTest(code=code):
                self.assertIsNone(iban_template(code))

    def test_R5_exact_length_passes_and_off_by_one_fails_for_every_country(self):
        for cc, length, template in TABLE:
            with self.subTest(country=cc):
                self.assertValid(make_iban(cc, length))
                self.assertInvalid(make_iban(cc, length - 1), msg_format(template))
                self.assertInvalid(make_iban(cc, length + 1), msg_format(template))

    def test_R5_be_length_examples(self):
        self.assertInvalid('BE6853900754703', msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('BE685390075470344', msg_format('BEkk BBBC CCCC CCXX'))


class TestR6Charset(IbanTestCase):
    def test_R6_non_ascii_alnum_rejected_even_at_correct_length(self):
        template = 'BEkk BBBC CCCC CCXX'
        for value in [
            'BE6853900754703é',       # é
            'BE6853900754703ß',       # ß
            'BE' + '0' * 13 + 'é',    # é, length 16
            'BE685390075470²³',  # ², ³
        ]:
            with self.subTest(value=value):
                self.assertInvalid(value, msg_format(template))


class TestR7FormatMessage(IbanTestCase):
    def test_R7_message_text_is_exact(self):
        self.assertInvalid(
            'BE68',
            'The IBAN does not seem to be correct. You should have entered '
            'something like this BEkk BBBC CCCC CCXX\n'
            'Where B = National bank code, S = Branch code, C = Account No, '
            'k = Check digit')

    def test_R7_examples(self):
        self.assertInvalid('BE68', msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('BE', msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('BE1', msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('BE00', msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('BE685390075470344', msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('DE8937040044053201300',
                           msg_format('DEkk BBBB BBBB CCCC CCCC CC'))
        self.assertInvalid('NO938601111794', msg_format('NOkk BBBB CCCC CCK'))
        self.assertInvalid('MT84MALT011000012345MTLCAST001S0',
                           msg_format('MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC'))


class TestR8StructureNotEnforced(IbanTestCase):
    def test_R8_letters_and_zeros_where_digits_expected_are_accepted(self):
        for value in [
            'BE57ABCDEFGHIJKL',
            'be57abcdefghijkl',
            'DE51XXXXXXXXXXXXXXXXXX',
            'NO1300000000000',
            'BE54000000000000',
            'AZ' + '0' * 26,
        ]:
            with self.subTest(value=value):
                self.assertValid(value)

    def test_R8_letter_check_digits_accepted(self):
        for value in [
            'BEI6539007547034',
            'BEOX539007547034',
            'BEPU539007547034',
            'BEQR539007547034',
            'BERO539007547034',
        ]:
            with self.subTest(value=value):
                self.assertValid(value)

    def test_R8_check_digit_pairs_over_alphabet_0_to_9_A_to_Z(self):
        # SPEC R8: over the alphabet 0-9A-Z, for BBAN 539007547034, the accepted
        # pairs are the only all-digit pair '68' and exactly these 10 letter pairs.
        alnum = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        accepted = set()
        for c1 in alnum:
            for c2 in alnum:
                if is_iban('BE' + c1 + c2 + '539007547034'):
                    accepted.add(c1 + c2)
        listed_letter_pairs = {'I6', 'OX', 'PU', 'QR', 'RO', 'S3', 'SL', 'TI', 'UF', 'VC'}
        self.assertEqual(accepted, listed_letter_pairs | {'68'})

    def test_R8_letter_check_pairs_accepted_in_lowercase_and_mixed_case(self):
        for pair in ['I6', 'OX', 'PU', 'QR', 'RO', 'S3', 'SL', 'TI', 'UF', 'VC']:
            for spelling in [pair.lower(), pair[0] + pair[1].lower()]:
                with self.subTest(pair=spelling):
                    self.assertValid('BE' + spelling + '539007547034')


class TestR9Checksum(IbanTestCase):
    def test_R9_accepted_examples(self):
        for value in [
            'BE68539007547034',
            'DE89370400440532013000',
            'FR1420041010050500013M02606',
            'GB82WEST12345698765432',
            'NL91ABNA0417164300',
            'CH9300762011623852957',
            'NO9386011117947',
            'MT84MALT011000012345MTLCAST001S',
            'BR1800360305000010009795493C1',
            'ES9121000418450200051332',
            'IT60X0542811101000000123456',
            'MU17BOMM0101101030300200000MUR',
            'SA0380000000608010167519',
            'PL61109010140000071219812874',
            'AT611904300234573201',
            'XK051212012345678906',
            'PS92PALS000000000400123456702',
            'JO94CBJO0010000000000131000302',
            'QA58DOHB00001234567890ABCDEFG',
            'KW81CBKU0000000000001234560101',
            'UA213223130000026007233566001',
            'IS140159260076545510730339',
        ]:
            with self.subTest(value=value):
                self.assertValid(value)

    def test_R9_rejected_examples(self):
        for value in [
            'BE68539007547035',
            'BE00539007547034',
            'BE01539007547034',
            'BE99539007547034',
            'DE88370400440532013000',
            'GB82WEST12345698765433',
            'BE68 5390 0754 703X',
            'BE00000000000000',
        ]:
            with self.subTest(value=value):
                self.assertInvalid(value, MSG_CHECKSUM)

    def test_R9_checksum_is_case_insensitive(self):
        self.assertValid('be68539007547034')
        self.assertValid('Be68539007547034')
        self.assertValid('gb82west12345698765432')

    def test_R9_success_returns_none(self):
        self.assertIsNone(validate_iban('BE68539007547034'))

    def test_R9_check_digits_00_01_99_follow_the_checksum_only(self):
        # No special rule: for some BBANs a check pair of 00, 01 or 99 is the
        # valid one, and it must be accepted like any other valid pair.
        for check in ('00', '01', '99'):
            with self.subTest(check=check):
                found = None
                for n in range(5000):
                    bban = '%012d' % n
                    if is_iban('BE' + check + bban):
                        found = bban
                        break
                self.assertIsNotNone(found, 'no BBAN found for check ' + check)
                self.assertValid('BE' + check + found)


class TestR10Order(IbanTestCase):
    def test_R10_empty_before_country(self):
        self.assertInvalid('---', MSG_EMPTY)

    def test_R10_country_before_length_and_checksum(self):
        for value in ['US', 'XX0', 'US00']:
            with self.subTest(value=value):
                self.assertInvalid(value, MSG_COUNTRY)

    def test_R10_format_before_checksum(self):
        for value in ['BE', 'BE1', 'BE00']:
            with self.subTest(value=value):
                self.assertInvalid(value, msg_format('BEkk BBBC CCCC CCXX'))

    def test_R10_checksum_last(self):
        self.assertInvalid('BE00000000000000', MSG_CHECKSUM)

    def test_R10_empty_message_for_empty_string(self):
        self.assertInvalid('', MSG_EMPTY)


class TestR11IsIban(unittest.TestCase):
    def test_R11_true_for_valid(self):
        self.assertIs(is_iban('BE68539007547034'), True)
        self.assertIs(is_iban('be68 5390 0754 7034'), True)

    def test_R11_false_for_invalid(self):
        self.assertIs(is_iban('BE68539007547035'), False)
        self.assertIs(is_iban(''), False)
        self.assertIs(is_iban(None), False)

    def test_R11_no_argument_is_false(self):
        self.assertIs(is_iban(), False)


class TestR12Pretty(unittest.TestCase):
    def test_R12_groups_valid_input_in_fours(self):
        self.assertEqual(pretty_iban('BE68539007547034'), 'BE68 5390 0754 7034')
        self.assertEqual(pretty_iban('DE89370400440532013000'),
                         'DE89 3704 0044 0532 0130 00')
        self.assertEqual(pretty_iban('FR1420041010050500013M02606'),
                         'FR14 2004 1010 0505 0001 3M02 606')
        self.assertEqual(pretty_iban('NO9386011117947'), 'NO93 8601 1117 947')
        self.assertEqual(pretty_iban('BR1800360305000010009795493C1'),
                         'BR18 0036 0305 0000 1000 9795 493C 1')

    def test_R12_preserves_case(self):
        self.assertEqual(pretty_iban('be68539007547034'), 'be68 5390 0754 7034')

    def test_R12_invalid_input_returned_unchanged(self):
        for value in ['BE68539007547035', 'US12345678', 'garbage text']:
            with self.subTest(value=value):
                self.assertEqual(pretty_iban(value), value)
        self.assertIsNone(pretty_iban(None))
        self.assertEqual(pretty_iban(''), '')

    def test_R12_quirk_existing_separators_count_as_characters(self):
        self.assertEqual(pretty_iban('BE68 5390 0754 7034'), 'BE68  539 0 07 54 7 034')
        self.assertEqual(pretty_iban('BE68-5390-0754-7034'), 'BE68 -539 0-07 54-7 034')
        self.assertEqual(pretty_iban('be 68539007547034'), 'be 6 8539 0075 4703 4')

    def test_R12_formatting_normalized_value_avoids_quirk(self):
        self.assertEqual(pretty_iban(normalize_iban('be68 5390 0754 7034')),
                         'be68 5390 0754 7034')
        self.assertEqual(pretty_iban(normalize_iban('BE68-5390-0754-7034')),
                         'BE68 5390 0754 7034')
        self.assertEqual(pretty_iban(normalize_iban('DE89 3704 0044 0532 0130 00')),
                         'DE89 3704 0044 0532 0130 00')
        self.assertEqual(pretty_iban(normalize_iban('NO93 8601 1117 947')),
                         'NO93 8601 1117 947')


class TestR13Bban(unittest.TestCase):
    def test_R13_examples(self):
        self.assertEqual(get_bban('BE68539007547034'), '539007547034')
        self.assertEqual(get_bban('BE68 5390 0754 7034'), '539007547034')
        self.assertEqual(get_bban('be68-5390-0754-7034'), '539007547034')
        self.assertEqual(get_bban('GB82 WEST 1234 5698 7654 32'), 'WEST12345698765432')

    def test_R13_does_not_validate(self):
        self.assertEqual(get_bban('US12345678'), '345678')
        self.assertEqual(get_bban('hello world'), 'oworld')

    def test_R13_short_and_empty(self):
        self.assertEqual(get_bban('BE6'), '')
        self.assertEqual(get_bban(''), '')
        self.assertEqual(get_bban(None), '')


class TestR14BbanForAccountRecord(unittest.TestCase):
    def test_R14_iban_type_returns_bban(self):
        self.assertEqual(account_bban('iban', 'BE68 5390 0754 7034'), '539007547034')
        self.assertEqual(account_bban('iban', 'XX'), '')

    def test_R14_iban_type_does_not_recheck_the_number(self):
        self.assertEqual(account_bban('iban', 'BE68539007547035'), '539007547035')

    def test_R14_other_types_raise_not_an_iban(self):
        message = ('Cannot compute the BBAN because the account number is not '
                   'an IBAN.')
        for acc_type in ['bank', 'IBAN', '', None]:
            for number in ['BE68 5390 0754 7034', '123456']:
                with self.subTest(acc_type=acc_type, number=number):
                    with self.assertRaises(NotAnIbanError) as cm:
                        account_bban(acc_type, number)
                    self.assertEqual(cm.exception.message, message)


class TestR15AccountType(IbanTestCase):
    def test_R15_valid_iban_gives_iban(self):
        self.assertEqual(account_type('BE68539007547034', object()), 'iban')
        self.assertEqual(account_type('be68 5390 0754 7034', object()), 'iban')
        self.assertEqual(account_type('BE68539007547034'), 'iban')

    def test_R15_otherwise_returns_fallback_unchanged(self):
        fallback = object()
        for value in ['BE68539007547035', 'US1234', '123-456-789', '', None]:
            with self.subTest(value=value):
                self.assertIs(account_type(value, fallback), fallback)

    def test_R15_default_fallback_is_bank(self):
        for value in ['BE68539007547035', 'US1234', '123-456-789', '', None,
                      'KW' + '0' * 28, '\u212aW' + '0' * 28, 'D\u212a' + '0' * 16]:
            with self.subTest(value=value):
                self.assertEqual(account_type(value), 'bank')

    def test_R15_explicit_fallback_argument(self):
        self.assertEqual(account_type('US1234', fallback='X'), 'X')
        self.assertEqual(account_type('BE68539007547034', fallback='X'), 'iban')

    def test_R15_supported_account_types_exact_list(self):
        self.assertEqual(supported_account_types(),
                         [('bank', 'Normal'), ('iban', 'IBAN')])

    def test_R15_add_iban_type_appends_iban_last(self):
        self.assertEqual(add_iban_account_type([('bank', 'Normal')]),
                         supported_account_types())
        self.assertEqual(add_iban_account_type([]), [('iban', 'IBAN')])
        self.assertEqual(add_iban_account_type([('a', 'A'), ('b', 'B')]),
                         [('a', 'A'), ('b', 'B'), ('iban', 'IBAN')])


class TestR16StorageCleanup(unittest.TestCase):
    def test_R16_valid_iban_stored_as_pretty_normalized(self):
        self.assertEqual(sanitize_account_number_for_storage('no93-8601-1117-947'),
                         'no93 8601 1117 947')
        self.assertEqual(sanitize_account_number_for_storage('be68 5390 0754 7034'),
                         'be68 5390 0754 7034')
        self.assertEqual(sanitize_account_number_for_storage('de89370400440532013000'),
                         'de89 3704 0044 0532 0130 00')

    def test_R16_invalid_or_falsy_values_unchanged(self):
        for value in ['BE68539007547035', 'DE89370400440532013001', '123 456', '']:
            with self.subTest(value=value):
                self.assertEqual(sanitize_account_number_for_storage(value), value)
        self.assertIs(sanitize_account_number_for_storage(False), False)

    def test_R16_single_record_dict(self):
        self.assertEqual(sanitize_account_vals({'acc_number': 'no93-8601-1117-947'}),
                         {'acc_number': 'no93 8601 1117 947'})
        self.assertEqual(sanitize_account_vals({'acc_number': 'BE68539007547035'}),
                         {'acc_number': 'BE68539007547035'})
        self.assertEqual(sanitize_account_vals({'acc_number': ''}),
                         {'acc_number': ''})
        self.assertEqual(sanitize_account_vals({'acc_number': False}),
                         {'acc_number': False})

    def test_R16_record_without_account_number_unchanged(self):
        self.assertEqual(sanitize_account_vals({'name': 'Alice'}), {'name': 'Alice'})

    def test_R16_other_keys_are_not_touched_even_for_valid_iban(self):
        self.assertEqual(sanitize_account_vals({'other': 'be68539007547034'}),
                         {'other': 'be68539007547034'})
        self.assertEqual(
            sanitize_account_vals({'other': 'be68539007547034',
                                   'acc_number': 'be68539007547034'}),
            {'other': 'be68539007547034', 'acc_number': 'be68 5390 0754 7034'})

    def test_R16_key_argument_selects_the_field(self):
        self.assertEqual(
            sanitize_account_vals({'iban_no': 'be68539007547034'}, key='iban_no'),
            {'iban_no': 'be68 5390 0754 7034'})

    def test_R16_batch_list_handled_per_record_in_order(self):
        batch = [{'acc_number': 'no93-8601-1117-947'},
                 {'acc_number': '123 456'},
                 {}]
        self.assertEqual(sanitize_account_vals(batch),
                         [{'acc_number': 'no93 8601 1117 947'},
                          {'acc_number': '123 456'},
                          {}])

    def test_R16_empty_batch_gives_empty_list(self):
        self.assertEqual(sanitize_account_vals([]), [])


class TestR17IbanAccountConstraint(IbanTestCase):
    def test_R17_iban_type_valid_number_passes(self):
        self.assertIsNone(check_iban_account('iban', 'BE68 5390 0754 7034'))

    def test_R17_iban_type_invalid_number_raises_validation_message(self):
        with self.assertRaises(IbanValidationError) as cm:
            check_iban_account('iban', 'BE68539007547035')
        self.assertEqual(cm.exception.message, MSG_CHECKSUM)

    def test_R17_iban_type_propagates_format_message(self):
        with self.assertRaises(IbanValidationError) as cm:
            check_iban_account('iban', 'XX')
        self.assertEqual(cm.exception.message, MSG_COUNTRY)

    def test_R17_other_types_are_not_checked(self):
        for acc_type in ['bank', 'IBAN', '', None]:
            for number in ['BE68539007547035', 'garbage']:
                with self.subTest(acc_type=acc_type, number=number):
                    self.assertIsNone(check_iban_account(acc_type, number))


class TestR4aKelvinSign(IbanTestCase):
    K = '\u212a'  # KELVIN SIGN

    def test_R4a_kelvin_in_country_position_gives_format_message(self):
        cases = [
            (self.K + 'W' + '0' * 28, msg_format('KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC')),
            (self.K + 'w' + '0' * 28, msg_format('KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC')),
            (self.K + 'W' + '0' * 27, msg_format('KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC')),
            (self.K + 'W' + '0' * 29, msg_format('KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC')),
            ('D' + self.K + '0' * 16, msg_format('DKkk BBBB CCCC CCCC CC')),
            (self.K + 'Z' + '0' * 18, msg_format('KZkk BBBC CCCC CCCC CCCC')),
            ('M' + self.K + '0' * 17, msg_format('MKkk BBBC CCCC CCCC CKK')),
            ('P' + self.K + '0' * 22, msg_format('PKkk BBBB CCCC CCCC CCCC CCCC')),
            ('S' + self.K + '0' * 22, msg_format('SKkk BBBB SSSS SSCC CCCC CCCC')),
            ('X' + self.K + '0' * 18, msg_format('XKkk BBBB CCCC CCCC CCCC')),
            ('D' + self.K + '5000400440116243', msg_format('DKkk BBBB CCCC CCCC CC')),
            (self.K + 'W81CBKU0000000000001234560101',
             msg_format('KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC')),
        ]
        for value, message in cases:
            with self.subTest(value=value):
                self.assertInvalid(value, message)

    def test_R4a_kelvin_replaces_first_k_of_valid_iban_gives_format_message(self):
        self.assertValid('KW81CBKU0000000000001234560101')
        self.assertInvalid(self.K + 'W81CBKU0000000000001234560101',
                           msg_format('KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC'))
        self.assertValid('DK5000400440116243')
        self.assertInvalid('D' + self.K + '5000400440116243',
                           msg_format('DKkk BBBB CCCC CCCC CC'))

    def test_R4a_ascii_k_pair_with_checksum_failure_gives_checksum_message(self):
        self.assertInvalid('KW' + '0' * 28, MSG_CHECKSUM)

    def test_R4a_kelvin_with_non_table_pair_gives_country_message(self):
        self.assertInvalid(self.K + 'E68539007547034', MSG_COUNTRY)
        self.assertInvalid('B' + self.K + '68539007547034', MSG_COUNTRY)

    def test_R4a_other_non_ascii_in_country_positions_gives_country_message(self):
        for ch in ['\u0131', '\u017f', '\u00df', '\u0130', '\uff22', '\u01c5']:
            with self.subTest(ch=ch):
                self.assertInvalid(ch + 'E68539007547034', MSG_COUNTRY)
                self.assertInvalid('B' + ch + '68539007547034', MSG_COUNTRY)
        self.assertInvalid('\u0130E68539007547034', MSG_COUNTRY)
        self.assertInvalid('\uff22E68539007547034', MSG_COUNTRY)
        self.assertInvalid('\u01c5E00', MSG_COUNTRY)

    def test_R4a_kelvin_after_position_two_is_format_error(self):
        self.assertInvalid('BE' + '0' * 13 + self.K, msg_format('BEkk BBBC CCCC CCXX'))
        self.assertInvalid('BE' + self.K + '0' * 13, msg_format('BEkk BBBC CCCC CCXX'))

    def test_R4a_downstream_helpers(self):
        value = self.K + 'W' + '0' * 28
        self.assertIs(is_iban(value), False)
        self.assertEqual(pretty_iban(value), value)
        self.assertEqual(account_type(value), 'bank')
        self.assertEqual(get_bban(value), '0' * 26)


if __name__ == '__main__':
    unittest.main()
