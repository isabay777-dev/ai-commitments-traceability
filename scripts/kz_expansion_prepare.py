import json,csv,re,collections,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
D=Path('data')
issuers={r['code']:r for r in json.loads((D/'kz_expansion_issuers_raw.json').read_text())}
bonds=json.loads((D/'kz_expansion_bonds_raw.json').read_text());shares=json.loads((D/'kz_expansion_shares_raw.json').read_text())
original=list(csv.DictReader(open(D/'kz_report_urls_full.txt'),delimiter=';'))
def norm(t):return {'INBNP':'INBN','IFDR':'TCIB'}.get(t.upper(),t.upper())
existing={norm(r['ticker']) for r in original}
catalog=json.loads((D/'kz_expansion_annual_catalog.json').read_text())
annual={}
for r in catalog:
 m=re.fullmatch(r'Годовой отчет за (202[1-5]) год',r['name'])
 if m and r['org_type']=='issuer' and (not r['date0'] or r['date0']<='2026-10-05'):
  annual.setdefault((r['org_code'],m[1]),[]).append(r)
eligible={r['org_code'] for r in bonds}-{r['org_code'] for r in shares}-existing
rank=sorted(eligible,key=lambda t:(-sum((t,str(y)) in annual for y in range(2021,2026)),t))
selected=rank[:75]
for t in ['EXLS','GLLK','SMTL']:
 if t not in selected:selected.append(t)
profiles={}
folder=D/'kz_expansion_profiles';folder.mkdir(exist_ok=True)
def fetch(t):
 path=folder/(t+'.json')
 if not path.exists():
  p=subprocess.run(['curl','-sSL','-A','Mozilla/5.0','--max-time','30','https://kase.kz/api/companies/issuers/'+t],capture_output=True)
  path.write_bytes(p.stdout)
 try:return t,json.loads(path.read_text())
 except Exception:return t,{}
with ThreadPoolExecutor(max_workers=5) as pool:profiles.update(pool.map(fetch,selected+['SNRG','KZPS']))
sector_map={
'AGKK':'Agricultural finance','AKMG':'Gas infrastructure','BCCI':'Investment services','BERK':'Banking','BRKZ':'Development banking','BTRK':'Development holding','EUBN':'Banking','FRMP':'SME development finance','HCBN':'Banking','IDFR':'Industrial leasing','JSBN':'Housing savings banking','KACM':'Investment funds','KAFI':'Agricultural leasing','KFUS':'Financial stability fund','KZTG':'Oil and gas','MFKM':'Microfinance / banking','MIAT':'Metal products manufacturing','NCOM':'Investment holding','PRKR':'Agriculture / grain trading','RGBK':'Food and beverages','SKKZ':'Sovereign holding','TCOM':'Telecom','TMJL':'Rail transport','FPST':'Gold mining','KZCR':'Metallurgy','SKEN':'Electricity and heat','ACAR':'Car rental','BIGD':'Real estate development','BKBT':'Biotechnology','BRBK':'Poultry farming','CLSG':'Leasing','DTJL':'Rail transport','EUCP':'Investment services','FATN':'Real estate rental','FFBN':'Banking','IKTT':'Space technology','INCA':'Gas transmission','KASA':'Aluminium production','KZTC':'Telecom','KZWE':'Wind energy','NITC':'Information technology','ORBS':'Leasing','ORPT':'Real estate / trade','PKDA':'Agriculture','RETM':'Commercial real estate','SCLB':'Passenger transport','SWPS':'Education','TERR':'Cattle farming','TSSP':'Equipment distribution','UZPA':'Industrial valves','EXLS':'Leasing','GLLK':'Leasing','SMTL':'Leasing','SNRG':'Electricity','KZPS':'Postal and financial services'}
records=[];jobs=[]
for t in selected+['SNRG','KZPS']:
 p=profiles[t];company=p.get('shortest_name_ru') or issuers.get(t,{}).get('shortest_name_ru') or {'SNRG':'Самрук-Энерго','KZPS':'Казпочта'}.get(t,t)
 sector=sector_map.get(t,'Microfinance / pawn lending' if t.startswith('MF') else 'Other')
 instruments=[r for r in bonds if r['org_code']==t]
 record={'ticker':t,'company':company,'sector':sector,'address':p.get('address_ru'),'primary_activity':p.get('primary_activity_ru'),'website':p.get('website_ru'),'issuer_url':'https://kase.kz/ru/listing/issuers/'+t,'bond_codes':[r['code'] for r in instruments],'share_codes':[r['code'] for r in shares if r['org_code']==t],'scope':'current_bond_only' if instruments else 'historical_bond_scope_to_verify'}
 records.append(record)
 for y in map(str,range(2021,2026)):
  docs=annual.get((t,y),[])
  # Prefer the first catalogue-listed (latest published) annual report per year.
  doc=docs[0] if docs else None
  url='https://kase.kz'+doc['link'] if doc and doc['link'].startswith('/') else doc['link'] if doc else f'https://kase.kz/files/emitters/{t}/{t.lower()}p_{y}_rus.pdf'
  jobs.append(dict(country='Kazakhstan',company=company,ticker=t,sector=sector,year=y,language='ru',doc_type='Annual report PDF',url=url,note=(f'KASE catalogue: {doc["name"]}, publication={doc["date0"]}' if doc else 'KASE annual report filename pattern')+' | '+record['scope']+' | '+record['issuer_url']))
(D/'kz_expansion_scope.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
(D/'kz_expansion_bond_jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2))
# More accurately named catalogue links for original NOT_FOUND rows (including renamed TCIB).
jobs2=[]
for r in original:
 if r['status']!='NOT_FOUND':continue
 t=norm(r['ticker']); y=r['year']
 for doc in annual.get((t,y),[]):
  jobs2.append(dict(country='Kazakhstan',company=r['company'],ticker=t,sector=r['sector'],year=y,language='ru',doc_type='Annual report PDF',url='https://kase.kz'+doc['link'],note=f'original_NOT_FOUND | KASE catalogue: {doc["name"]}, publication={doc["date0"]}'))
(D/'kz_expansion_original_catalog_jobs.json').write_text(json.dumps(jobs2,ensure_ascii=False,indent=2))
print('selected',len(selected),'historical',2,'jobs',len(jobs),'original catalogue jobs',len(jobs2))
for r in records:print(r['ticker'],r['company'],r['address'],r['primary_activity'])
