"""Runtime trace harness for base_iban (Odoo 18.0 @1f2b50a).
Loads the ORIGINAL models/res_partner_bank.py unmodified, with a fake `odoo`
package (stubs/) on sys.path. Writes evidence/trace_*.txt.
Usage: python3 -I trace.py
"""
import sys, os, importlib.util, itertools, string
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'stubs'))
SRC = os.environ['ODOO_SRC'] + '/addons/base_iban/models/res_partner_bank.py'  # ODOO_SRC: Odoo 18.0 checkout (commit 1f2b50a)
spec = importlib.util.spec_from_file_location('base_iban_rpb', SRC)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from odoo.exceptions import ValidationError, UserError
EVID = os.path.dirname(HERE)

def call(fn, arg):
    try:
        r = fn(arg)
        return 'OK  -> %r' % (r,)
    except Exception as e:
        return 'EXC %s: %r' % (type(e).__name__, str(e))

class Log:
    def __init__(self, name): self.f = open(os.path.join(EVID, name), 'w', encoding='utf-8')
    def __call__(self, *a): print(*a, file=self.f)

def find_valid(prefix_cc, body):
    """Use the original validator as an oracle to find check digits making cc+kk+body valid."""
    for k in range(100):
        s = '%s%02d%s' % (prefix_cc, k, body)
        try:
            m.validate_iban(s); return s
        except ValidationError:
            pass
    return None

# ---------------------------------------------------------------- validate
L = Log('trace_validate.txt')
L('# validate_iban(input) -> OK (returns None) or exception')
VALID = [
 'BE68539007547034', 'DE89370400440532013000', 'FR1420041010050500013M02606',
 'GB82WEST12345698765432', 'NL91ABNA0417164300', 'CH9300762011623852957',
 'NO9386011117947', 'MT84MALT011000012345MTLCAST001S', 'BR1800360305000010009795493C1',
 'ES9121000418450200051332', 'IT60X0542811101000000123456', 'MU17BOMM0101101030300200000MUR',
 'SA0380000000608010167519', 'PL61109010140000071219812874', 'AT611904300234573201',
 'XK051212012345678906', 'PS92PALS000000000400123456702', 'JO94CBJO0010000000000131000302',
 'QA58DOHB00001234567890ABCDEFG', 'KW81CBKU0000000000001234560101', 'UA213223130000026007233566001',
 'IS140159260076545510730339',
]
L('\n## Published example IBANs (compact)')
for s in VALID: L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Input variants (normalization before validation)')
for s in ['BE68 5390 0754 7034', 'be68 5390 0754 7034', 'be68539007547034', 'Be68-5390-0754-7034',
          'BE68.5390.0754.7034', 'BE68_5390_0754_7034', ' BE68\t5390\n0754 7034 ', 'BE68 5390 0754 7034',
          'BE68/5390(0754)7034!', 'IBAN BE68 5390 0754 7034', 'gb82 west 1234 5698 7654 32']:
    L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Empty / missing')
for s in [None, '', '   ', '---', '_', ' ']: L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Unsupported / bad country code')
for s in ['US12345678901234567890', 'LC55HEMM000100010012001200023015', 'EG380019000500000000263180002',
          'SC18SSCB11010000000000001497USD', '12345678901234', 'B', 'BE', '1E68539007547034', 'ZZ00']:
    L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Wrong checksum (right length)')
for s in ['BE68539007547035', 'BE00539007547034', 'BE01539007547034', 'BE99539007547034', 'DE88370400440532013000',
          'GB82WEST12345698765433']:
    L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Wrong length')
for s in ['BE6853900754703', 'BE685390075470344', 'BE68', 'DE8937040044053201300', 'NO938601111794', 'MT84MALT011000012345MTLCAST001S0']:
    L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Non-ASCII word characters survive normalization and are rejected by the format check')
for s in ['BE6853900754703é', 'BE68539007547٣٤', 'BE6853900754703ß', 'BE685390075470²³']:
    L('%-40r %s' % (s, call(m.validate_iban, s)))
L('\n## Structure inside the BBAN is NOT enforced: letters where the template says digits; check digits found via the validator itself')
for cc, body in [('BE', 'ABCDEFGHIJKL'), ('DE', 'XXXXXXXXXXXXXXXXXX'), ('NO', '00000000000'), ('BE', '000000000000'), ('be', 'abcdefghijkl')]:
    v = find_valid(cc, body); L('%s + kk + %s -> first valid: %r' % (cc, body, v))
    if v: L('   validate(%r) %s ; lowercase %s' % (v, call(m.validate_iban, v), call(m.validate_iban, v.lower())))
L('\n## Check digits that are letters (base-36 conversion applies to all positions)')
hits = []
for a, b in itertools.product(string.ascii_uppercase + string.digits, repeat=2):
    if (a + b).isdigit(): continue
    s = 'BE' + a + b + '539007547034'
    try: m.validate_iban(s); hits.append(s)
    except ValidationError: pass
L('non-digit check-digit pairs accepted for BE..539007547034: %d, first few: %r' % (len(hits), hits[:5]))
L('\n## Return value of validate_iban on success: %r' % (m.validate_iban('BE68539007547034'),))

# ---------------------------------------------------------------- template table
L = Log('trace_templates.txt')
L('# Per-country: compact length expected; lengths n-1, n, n+1 of an all-zero BBAN -> outcome category')
L('# cc | expected_len | len-1 | len | len+1 | display template (from error message)')
def cat(s):
    try: m.validate_iban(s); return 'VALID'
    except ValidationError as e:
        t = str(e)
        if t.startswith('The IBAN does not seem'): return 'FORMAT'
        if t.startswith('This IBAN does not pass'): return 'CHECKSUM'
        if t.startswith('The IBAN is invalid'): return 'COUNTRY'
        return 'OTHER:' + t
def template_from_msg(cc):
    try: m.validate_iban(cc.upper() + '00')
    except ValidationError as e:
        t = str(e); return t.split('something like this ')[1].split('\n')[0]
for cc in sorted(getattr(m, '_map_iban_template')):
    tpl = template_from_msg(cc); n = len(tpl.replace(' ', ''))
    row = [cat(cc.upper() + '0' * (k - 2)) for k in (n - 1, n, n + 1)]
    L('%s | %d | %s | %s | %s | %s' % (cc.upper(), n, row[0], row[1], row[2], tpl))
L('# total supported countries: %d' % len(getattr(m, '_map_iban_template')))

# ---------------------------------------------------------------- errors
L = Log('trace_errors.txt')
L('# Exact exception type and message text (repr) per error class')
for s in ['', 'US00', 'BE00', 'BE0000000000000é', 'BE68539007547035']:
    L('%-30r %s' % (s, call(m.validate_iban, s)))
L('# Order of checks: unsupported country beats length; length beats checksum; empty first')
for s in ['US', 'XX0', 'BE1', 'BE68 5390 0754 703X', 'BE00000000000000']:
    L('%-30r %s' % (s, call(m.validate_iban, s)))

# ---------------------------------------------------------------- normalize / pretty / bban
L = Log('trace_normalize_pretty_bban.txt')
L('## normalize_iban')
for s in [None, '', 'BE68 5390 0754 7034', 'be68-5390.0754/7034', 'a_b c\td\ne', 'é ß ٣ ²', '!!!', 'DE89 3704 0044 0532 0130 00', 0, 12]:
    L('%-35r %s' % (s, call(m.normalize_iban, s)))
L('\n## pretty_iban')
for s in ['BE68539007547034', 'be68539007547034', 'DE89370400440532013000', 'FR1420041010050500013M02606',
          'NO9386011117947', 'BR1800360305000010009795493C1', 'BE68 5390 0754 7034', 'BE68-5390-0754-7034',
          'be 68539007547034', 'BE68539007547035', 'US12345678', '', None, 'garbage text']:
    L('%-35r %s' % (s, call(m.pretty_iban, s)))
L('\n## pretty_iban(normalize_iban(x))  (what create/write store)')
for s in ['be68 5390 0754 7034', 'BE68-5390-0754-7034', 'DE89 3704 0044 0532 0130 00', 'NO93 8601 1117 947']:
    L('%-35r %s' % (s, call(lambda x: m.pretty_iban(m.normalize_iban(x)), s)))
L('\n## get_bban_from_iban (no validation performed)')
for s in ['BE68539007547034', 'BE68 5390 0754 7034', 'be68-5390-0754-7034', 'GB82 WEST 1234 5698 7654 32',
          'US12345678', 'BE6', '', None, 'hello world']:
    L('%-35r %s' % (s, call(m.get_bban_from_iban, s)))

# ---------------------------------------------------------------- model-level behaviors
L = Log('trace_model.txt')
L('# Model methods exercised with stub ORM. Parent (base) behaviour is STUBBED: retrieve_acc_type -> "bank".')
Bank = m.ResPartnerBank
class Env:
    def _(self, s): return s
class Rec(Bank):
    def __init__(self, acc_number=None, acc_type=None):
        self.env = Env(); self.acc_number = acc_number; self.acc_type = acc_type
    def __iter__(self): return iter([self])
r = Rec()
L('\n## _get_supported_account_types: %r' % (r._get_supported_account_types(),))
L('\n## retrieve_acc_type')
for s in ['BE68539007547034', 'be68 5390 0754 7034', 'BE68539007547035', 'US1234', '123-456-789', '', None]:
    L('%-30r %s' % (s, call(r.retrieve_acc_type, s)))
L('\n## check_iban (bool)')
for s in ['BE68539007547034', 'be68 5390 0754 7034', 'BE68539007547035', '', None]:
    L('%-30r %s' % (s, call(r.check_iban, s)))
L('check_iban() no arg: %s' % call(lambda _: r.check_iban(), None))
L('\n## create(vals_list) -> vals passed to parent')
vl = [{'acc_number': 'be68 5390 0754 7034'}, {'acc_number': 'BE68539007547035'}, {'acc_number': '123 456'},
      {'acc_number': ''}, {'acc_number': False}, {}, {'acc_number': 'no93-8601-1117-947'}]
import copy
L('in : %r' % vl); L('out: %r' % r.create(copy.deepcopy(vl)))
L('\n## write(vals)')
for v in [{'acc_number': 'de89370400440532013000'}, {'acc_number': 'DE89370400440532013001'}, {'name': 'x'}]:
    L('%r -> %r' % (v, r.write(dict(v))))
L('\n## get_bban() method')
for an, at in [('BE68 5390 0754 7034', 'iban'), ('BE68 5390 0754 7034', 'bank'), ('123456', 'bank'), ('XX', 'iban')]:
    L('acc_number=%r acc_type=%r -> %s' % (an, at, call(lambda _: Rec(an, at).get_bban(), None)))
L('\n## _check_iban constraint')
for an, at in [('BE68 5390 0754 7034', 'iban'), ('BE68539007547035', 'iban'), ('BE68539007547035', 'bank'), ('garbage', 'bank')]:
    L('acc_number=%r acc_type=%r -> %s' % (an, at, call(lambda _: Rec(an, at)._check_iban(), None)))
print('done')
