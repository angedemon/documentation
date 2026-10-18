import sys, importlib.util, string, itertools
S=sys.argv[1]
sys.path.insert(0, S+'/jev_replay2/evidence/harness/stubs_rev2')
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
I=load('i',S+'/room_a/odoo/addons/base_iban/models/res_partner_bank.py')
B=load('b',S+'/room_a/odoo/odoo/addons/base/models/res_bank.py')
asc=set(string.ascii_lowercase)
one=[];two=[];other=[]
for cp in range(0x110000):
    if 0xD800<=cp<=0xDFFF: continue
    c=chr(cp)
    if c.isascii() or not c.isalnum(): continue
    l=c.lower()
    if l and all(ch in asc for ch in l):
        (one if len(l)==1 else two).append(hex(cp))
    elif l and l[0] in asc: other.append(hex(cp))
print('nonascii alnum lowering to 1 ascii letter:',one)
print('lowering to >=2 all-ascii letters:',two)
print('lowering to multi starting ascii:',other)
# R8 counts
def ok(s):
    try: I.validate_iban(s); return True
    except Exception: return False
U=string.digits+string.ascii_uppercase; M=string.digits+string.ascii_letters
cu=[a+b for a in U for b in U if not (a+b).isdigit() and ok('BE'+a+b+'539007547034')]
cm=[a+b for a in M for b in M if not (a+b).isdigit() and ok('BE'+a+b+'539007547034')]
cd=[a+b for a in string.digits for b in string.digits if ok('BE'+a+b+'539007547034')]
print('upper-alphabet letter pairs',len(cu),cu); print('mixed-case pairs',len(cm)); print('digit pairs',cd)
# 1-char input lowering to 2-char code
print('1-char validations passing country:', [hex(cp) for cp in range(0x110000) if not 0xD800<=cp<=0xDFFF and chr(cp).isalnum() and chr(cp).lower() in I._map_iban_template])
# sanitize equivalence spot
print(B.sanitize_account_number('ß_x y'))
# R15 append: does base_iban mutate base list? new list each call?
