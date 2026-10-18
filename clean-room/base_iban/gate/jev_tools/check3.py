import sys, importlib.util
S=sys.argv[1]
sys.path.insert(0, S+'/jev_replay2/evidence/harness/stubs_rev2')
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
I=load('i',S+'/room_a/odoo/addons/base_iban/models/res_partner_bank.py')
B=load('b',S+'/room_a/odoo/odoo/addons/base/models/res_bank.py')
def v(s):
    try: I.validate_iban(s); return 'OK'
    except Exception as e: return str(e)[:45]
for s in ['ıE68539007547034','Sſ'+'0'*22,'ſK'+'0'*22,'ßE68539007547034','Iı'+'0'*20, 'DK5000400440116243']:
    print(ascii(s), v(s))
class Env:
    def _(self,s): return s
class R(type('X',(I.ResPartnerBank,B.ResPartnerBank),{})):
    def __init__(self): self.env=Env()
print(R().create([{'acc_number':'no93-8601-1117-947'},{'acc_number':'123 456'},{}]))
print(I.ResPartnerBank.create.__name__)
class P(I.ResPartnerBank.__mro__[1]):
    pass
