"""Revision-2 runtime traces (Odoo 18.0 @1f2b50a).
Loads, unmodified:
  BASE = odoo/odoo/addons/base/models/res_bank.py   (base res.partner.bank)
  IBAN = odoo/addons/base_iban/models/res_partner_bank.py
with the fake package in stubs_rev2/. The model as installed is simulated by a
class whose bases are (IBAN model, BASE model): base_iban's super() then reaches
the base model, and the base model's super() reaches a plain recorder (the
stubbed ORM root) that returns the vals it receives.
Usage: python3 -I -B trace_rev2.py   -> writes ../trace_*_rev2.txt
"""
import sys, os, importlib.util, copy, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'stubs_rev2'))
ROOT = os.environ['ODOO_SRC']  # Odoo 18.0 checkout (commit 1f2b50a)
def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(s); s.loader.exec_module(mod); return mod
B = load('orig_base_res_bank', ROOT + '/odoo/addons/base/models/res_bank.py')
I = load('orig_base_iban_rpb', ROOT + '/addons/base_iban/models/res_partner_bank.py')
from odoo.exceptions import ValidationError
EVID = os.path.dirname(HERE)

R = repr   # switched to ascii() for the Unicode trace so U+212A is visible
def call(fn, *arg):
    try: return 'OK  -> %s' % R(fn(*arg))
    except Exception as e: return 'EXC %s: %s' % (type(e).__name__, R(str(e)))
class Log:
    def __init__(self, name): self.f = open(os.path.join(EVID, name), 'w', encoding='utf-8')
    def __call__(self, *a): print(*a, file=self.f)
class Env:
    def _(self, s): return s
def mk(cls):
    class Rec(cls):
        def __init__(self, acc_number=None, acc_type=None):
            self.env = Env(); self.acc_number = acc_number; self.acc_type = acc_type
        def __iter__(self): return iter([self])
    return Rec
BaseRec = mk(B.ResPartnerBank)
Installed = mk(type('Installed', (I.ResPartnerBank, B.ResPartnerBank), {}))

# ------------------------------------------------------------ account types
L = Log('trace_acc_type_rev2.txt')
L('# python %s' % sys.version.split()[0])
L('# MRO of simulated installed model: %r' % [c.__qualname__ + '@' + c.__module__ for c in Installed.__mro__])
b, x = BaseRec(), Installed()
L('\n## BASE alone')
L('_get_supported_account_types() -> %r' % (b._get_supported_account_types(),))
L('get_supported_account_types()  -> %r' % (b.get_supported_account_types(),))
INPUTS = ['BE68539007547034', 'be68 5390 0754 7034', 'BE68539007547035', 'US1234', '123-456-789',
          'KW' + '0' * 28, '', None, False, 0, 12]
for s in INPUTS: L('retrieve_acc_type(%r) %s' % (s, call(b.retrieve_acc_type, s)))
L('\n## INSTALLED (base_iban over base)')
L('_get_supported_account_types() -> %r' % (x._get_supported_account_types(),))
L('get_supported_account_types()  -> %r' % (x.get_supported_account_types(),))
for s in INPUTS: L('retrieve_acc_type(%r) %s' % (s, call(x.retrieve_acc_type, s)))
L('\n## acc_type compute (BASE compute method, run on INSTALLED record)')
for s in ['be68 5390 0754 7034', 'BE68539007547035', '123456', False]:
    r = Installed(s); r._compute_acc_type(); L('acc_number=%r -> acc_type=%r' % (s, r.acc_type))

# ------------------------------------------------------------ sanitization
L = Log('trace_sanitize_rev2.txt')
L('## BASE sanitize function (feeds the stored "sanitized account number")')
for s in ['BE68 5390 0754 7034', 'be68-5390.0754/7034', 'BE68_5390_0754_7034', 'be68 5390 0754 7034',
          'é ß ٣', 'KW00', '123 456', '', None, False, 0]:
    L('%-32r %s' % (s, call(B.sanitize_account_number, s)))
VL = [{'acc_number': 'be68 5390 0754 7034'}, {'acc_number': 'BE68_5390_0754_7034'},
      {'acc_number': 'BE68539007547034'}, {'acc_number': 'no93-8601-1117-947'},
      {'acc_number': 'BE68539007547035'}, {'acc_number': '123 456'}, {'acc_number': 'abc_def'},
      {'acc_number': ''}, {'acc_number': False}, {}, {'sanitized_acc_number': 'be68 5390 0754 7034'},
      {'acc_number': 'be68 5390 0754 7034', 'sanitized_acc_number': 'XYZ'},
      {'sanitized_acc_number': 'BE68539007547034'}, {'acc_number': 'BE68539007547034'}]
L('\n## create(vals_list): vals reaching the ORM root')
L('#   BASE alone | INSTALLED')
for v in VL:
    L('%r\n    base     : %r\n    installed: %r' % (v, BaseRec().create([dict(v)])[0], Installed().create([dict(v)])[0]))
L('\n## write(vals): vals reaching the ORM root (INSTALLED)')
for v in VL: L('%r -> %r' % (v, Installed().write(dict(v))))
L('\n## Search condition on account number (BASE, unchanged by base_iban)')
for v in ['be68 5390 0754 7034', 'BE68 5390 0754 7034', 'BE68_5390_0754_7034', ['be68-5390', 'x y']]:
    L('acc_number = %r -> %r' % (v, Installed()._condition_to_sql('t', 'acc_number', '=', v, None)))
L('\n## Property check: for valid IBAN inputs, installed sanitized value == base sanitize(normalize(input))')
samples = ['be68 5390 0754 7034', 'BE68_5390_0754_7034', 'gb82 west 1234 5698 7654 32', 'Be68-5390-0754-7034',
           ' BE68\t5390\n0754 7034 ', 'NO93 8601 1117 947', 'BE68/5390(0754)7034!']
for s in samples:
    got = Installed().create([{'acc_number': s}])[0]['sanitized_acc_number']
    L('%-36r installed=%r  base_alone=%r  upper(normalize)=%r  equal=%s' % (
        s, got, B.sanitize_account_number(s), I.normalize_iban(s).upper(), got == I.normalize_iban(s).upper()))

L('\n## Exhaustive: base sanitize keeps char c  <=>  c.isalnum() or c == "_"   (all code points, surrogates skipped)')
mism = [cp for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF
        and ((B.sanitize_account_number('#' + chr(cp) + '#') or '') != '') != (chr(cp).isalnum() or chr(cp) == '_')]
L('mismatches: %d %r' % (len(mism), mism[:10]))

# ------------------------------------------------------------ unicode case folding
L = Log('trace_unicode_case_rev2.txt'); R = ascii
L('# all strings below are printed with ascii(): \\u212a = KELVIN SIGN')
L('## Exhaustive scan, all code points 0..0x10FFFF (surrogates skipped):')
L('## chars c that survive normalization (non-empty after R1) and whose lowercase is ONE ASCII letter, c not ASCII')
hits = []
for cp in range(0x110000):
    if 0xD800 <= cp <= 0xDFFF: continue
    c = chr(cp)
    if cp < 128: continue
    lo = c.lower()
    if len(lo) == 1 and lo.isascii() and lo.isalpha() and I.normalize_iban(c) == c:
        hits.append(cp)
for cp in hits: L('U+%04X %s -> lower %r' % (cp, unicodedata.name(chr(cp)), chr(cp).lower()))
L('total: %d' % len(hits))
L('\n## Non-ASCII chars whose lowercase is MULTI-char starting with ASCII (shift the 2-char window):')
multi = []
for cp in range(128, 0x110000):
    if 0xD800 <= cp <= 0xDFFF: continue
    c = chr(cp); lo = c.lower()
    if len(lo) > 1 and I.normalize_iban(c) == c: multi.append(cp)
for cp in multi: L('U+%04X %s -> lower %r' % (cp, unicodedata.name(chr(cp)), chr(cp).lower()))
L('total: %d' % len(multi))
codes = sorted(I._map_iban_template)
L('\n## Supported codes reachable with a non-ASCII char in pos 1 or 2: %r' % [
    cc for cc in codes if any(chr(cp).lower() in (cc[0], cc[1]) for cp in hits)])
def tlen(cc): return len(I._map_iban_template[cc].replace(' ', ''))
L('\n## validate / is_iban / pretty / bban / installed acc_type for crafted inputs (correct length for the matched code)')
cases = []
for cc in codes:
    for pos in (0, 1):
        if cc[pos] == 'k':
            pre = ('K' + cc[1].upper()) if pos == 0 else (cc[0].upper() + 'K')
            cases.append(pre + '0' * (tlen(cc) - 2))
cases += ['KW' + '0' * 27, 'KW' + '0' * 29, 'Kw' + '0' * 28, 'KW' + '0' * 28,
          'İE68539007547034', 'BE68539007547034'.replace('B', 'Ｂ'), 'ǅ' + 'E00']
for s in cases:
    L('%a (len %d)\n   validate  %s\n   is_iban   %s\n   pretty    %s\n   bban      %s\n   acc_type  %s' % (
        s, len(s), call(I.validate_iban, s), call(Installed().check_iban, s), call(I.pretty_iban, s),
        call(I.get_bban_from_iban, s), call(Installed().retrieve_acc_type, s)))
L('\n## Checksum is never reached for these: is there a K-substitute variant of a VALID IBAN that passes? ')
for s in ['KW81CBKU0000000000001234560101', 'KZ86125KZT5004100100', 'SK3112000000198742637541', 'DK5000400440116243']:
    for pos in range(len(s)):
        if s[pos] == 'K':
            t = s[:pos] + 'K' + s[pos + 1:]
            L('%r valid=%s  K->U+212A at %d: %s' % (s, call(I.validate_iban, s), pos, call(I.validate_iban, t)))

# ------------------------------------------------------------ non-str inputs
L = Log('trace_nonstr_rev2.txt'); R = repr
L('# Behaviour per input type. is_iban = boolean wrapper (check_iban); acc_type = INSTALLED retrieve_acc_type')
VALS = [None, False, True, 0, 12, 0.0, 1.5, b'', b'BE68539007547034', bytearray(b'BE68'), [], ['BE68539007547034'],
        (), {}, {'a': 1}, set(), object()]
FN = [('normalize', I.normalize_iban), ('validate', I.validate_iban), ('is_iban', Installed().check_iban),
      ('pretty', I.pretty_iban), ('bban', I.get_bban_from_iban), ('acc_type', Installed().retrieve_acc_type),
      ('base_sanitize', B.sanitize_account_number)]
for v in VALS:
    L('\n%s %r' % (type(v).__name__, v if not isinstance(v, object) or type(v) is not object else 'object()'))
    for n, f in FN: L('   %-13s %s' % (n, call(f, v)))
print('done')
