import sys, re, importlib.util
S=sys.argv[1]
sys.path.insert(0, S+'/jev_replay/evidence/harness/stubs')
spec=importlib.util.spec_from_file_location('o', S+'/room_a/odoo/addons/base_iban/models/res_partner_bank.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# table check
txt=open(S+'/room_a/out/SPEC.md',encoding='utf-8').read()
rows=re.findall(r'^\| ([A-Z]{2}) \| (\d+) \| ([^|]+?) \|$', txt, re.M)
t=m._map_iban_template
print('rows',len(rows),'src',len(t))
bad=[r for r in rows if t.get(r[0].lower())!=r[2] or len(r[2].replace(' ',''))!=int(r[1])]
print('bad rows',bad, 'missing', set(t)-{r[0].lower() for r in rows})
# isalnum equivalence of [\W_]
diff=[c for c in map(chr,range(0x110000)) if (re.sub(r'[\W_]','',c)==c) != c.isalnum()]
print('isalnum mismatches',len(diff),diff[:10])
# Kelvin edge
for s in ['KW'+'0'*28, 'AZ'+'0'*26]:
    try: m.validate_iban(s); print(repr(s),'VALID')
    except Exception as e: print(repr(s), str(e)[:60])
print(m.pretty_iban('BE68 5390 0754 7034'))
