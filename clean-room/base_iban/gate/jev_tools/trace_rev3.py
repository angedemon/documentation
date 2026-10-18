"""JEV round 3: U+212A in a country position, pair-with-K NOT a table code.
Adapted copy of REA's trace_rev2.py (same loading of the unmodified originals,
same stubs_rev2). Writes ../trace_kelvin_nontable_rev3.txt"""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'stubs_rev2'))
ROOT = os.environ['ODOO_SRC']  # Odoo 18.0 checkout (commit 1f2b50a)
def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(s); s.loader.exec_module(mod); return mod
B = load('orig_base_res_bank', ROOT + '/odoo/addons/base/models/res_bank.py')
I = load('orig_base_iban_rpb', ROOT + '/addons/base_iban/models/res_partner_bank.py')
EVID = os.path.dirname(HERE)
K = 'K'
def call(fn, *a):
    try: return 'OK  -> %a' % (fn(*a),)
    except Exception as e: return 'EXC %s: %a' % (type(e).__name__, str(e))
class Env:
    def _(self, s): return s
class Rec(type('Installed', (I.ResPartnerBank, B.ResPartnerBank), {})):
    def __init__(self): self.env = Env(); self.acc_number = None; self.acc_type = None
    def __iter__(self): return iter([self])
codes = sorted(I._map_iban_template)
f = open(os.path.join(EVID, 'trace_kelvin_nontable_rev3.txt'), 'w', encoding='utf-8')
L = lambda *a: print(*a, file=f)
L('# python %s ; strings printed with ascii(): \\u212a = KELVIN SIGN' % sys.version.split()[0])
cases = [K + 'E68539007547034', 'B' + K + '68539007547034',          # the two examples from Q12
         K + 'E', 'B' + K, K + 'A00', 'A' + K + '00', K + K + '00',  # short / other non-table pairs
         K + 'e68539007547034', 'b' + K + '68539007547034',         # lowercase partner letter
         K + '1' + '0' * 14, '1' + K + '0' * 14,                     # digit partner
         K, K + 'W' + '0' * 28, 'S' + K + '3112000000198742637541']  # 1-char; table-code controls
for s in cases:
    pair = s[:2].replace(K, 'K').lower()
    L('%a (len %d) pair-as-K=%r in_table=%s\n   validate  %s\n   is_iban   %s\n   pretty    %s\n   bban      %s\n   acc_type  %s' % (
        s, len(s), pair, pair in I._map_iban_template, call(I.validate_iban, s), call(Rec().check_iban, s),
        call(I.pretty_iban, s), call(I.get_bban_from_iban, s), call(Rec().retrieve_acc_type, s)))
L('\n## Exhaustive: every pair with U+212A in pos 1 or 2 and the other char in [0-9A-Za-z] or U+212A,')
L('## suffix "00" (len 4). Message counts split by whether the K-reading is a table code.')
from collections import Counter
cnt = Counter()
partners = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + K
for p in partners:
    for s in (K + p + '00', p + K + '00'):
        intab = s[:2].replace(K, 'K').lower() in I._map_iban_template
        r = call(I.validate_iban, s)
        msg = 'country' if 'country code' in r else 'format' if 'seem to be correct' in r else 'checksum' if 'validation check' in r else r
        cnt[(intab, msg)] += 1
for k in sorted(cnt): L('in_table=%s  message=%s  count=%d' % (k[0], k[1], cnt[k]))
print('done')
