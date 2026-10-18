"""Differential check (after the rebuild is frozen): original base_iban vs room-B rebuild.

Usage: ODOO_SRC=/path/to/odoo-18.0 python3 -I -B diff_fuzz.py
"""
import os, sys, random, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'room_a', 'evidence', 'harness', 'stubs_rev2'))
def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
O = load('orig', os.environ['ODOO_SRC'] + '/addons/base_iban/models/res_partner_bank.py')
N = load('iban', os.path.join(HERE, '..', 'room_b', 'iban.py'))

def outcome(fn, x):
    try:
        return ('ok', fn(x))
    except TypeError as e:
        return ('TypeError',)
    except Exception as e:
        msg = getattr(e, 'message', None) or (e.args[0] if e.args else str(e))
        return ('err', str(msg))

def mod97_fix(s):
    """Turn country+'00'+bban into a valid-checksum IBAN."""
    cc, bban = s[:2], s[4:]
    num = int(''.join(str(int(c, 36)) for c in (bban + cc + '00').upper()))
    return cc + '%02d' % (98 - num % 97) + bban

random.seed(1234)
tmpl = O._map_iban_template
ALPH = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
NOISE = ' -./_() \tKéÉ٣ıßＢ'
cases = ['', 'B', 'BE', 'BE6', 'hello world', 'KW' + '0' * 28]
for _ in range(60000):
    cc = random.choice(list(tmpl) + ['us', 'zz', 'Xk', 'de', 'KK'[random.randrange(2)] + 'W'])
    n = len(tmpl.get(cc.lower(), 'x' * 20).replace(' ', '')) + random.choice([0, 0, 0, -1, 1, -4])
    s = cc[:2] + '00' + ''.join(random.choice(ALPH) for _ in range(max(0, n - 4)))
    if random.random() < 0.6:
        try: s = mod97_fix(s)
        except ValueError: pass
    if random.random() < 0.3:
        i = random.randrange(len(s) + 1); s = s[:i] + random.choice(NOISE) + s[i:]
    if random.random() < 0.2:
        s = s.lower()
    cases.append(s)

pairs = [('normalize', O.normalize_iban, N.normalize_iban), ('validate', O.validate_iban, N.validate_iban),
         ('pretty', O.pretty_iban, N.pretty_iban), ('bban', O.get_bban_from_iban, N.get_bban)]
mism = 0; nvalid = 0
for x in cases:
    for name, fo, fn in pairs:
        a, b = outcome(fo, x), outcome(fn, x)
        if name == 'validate' and a[0] == 'ok': a = ('ok', None); nvalid += 1
        if name == 'validate' and b[0] == 'ok': b = ('ok', None)
        if a != b:
            mism += 1
            if mism <= 10: print('MISMATCH', name, ascii(x), a, b)
print(f'{len(cases)} inputs x {len(pairs)} functions, {nvalid} valid IBANs, mismatches: {mism}')
