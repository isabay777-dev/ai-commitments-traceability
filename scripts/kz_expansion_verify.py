#!/usr/bin/env python3
"""Reconcile URL checks, issuer scope, original gaps and unique additions."""
import csv,json,re,sys
from pathlib import Path
from urllib.parse import urlsplit
D=Path(__file__).resolve().parents[1]/'data'
FIELDS='country company ticker sector year language doc_type url status note'.split()
def read(name):return json.loads((D/name).read_text())
ALIASES=read('kz_expansion_aliases.json')
def ticker(t):return ALIASES['ticker_to_canonical'].get(t.upper(),t.upper())
def company(s):return re.sub(r'[^\w]','',s).replace('_','').lower()
def load():
    raw=list(csv.reader((D/'kz_expansion_urls.csv').open(),delimiter=';'))
    assert raw[0]==FIELDS
    rows=[dict(zip(FIELDS,r)) for r in raw[1:] if r[0]!='SUMMARY']
    assert all(len(r)==10 for r in raw[1:] if r[0]!='SUMMARY')
    b=read('kz_expansion_baseline.json')
    lookup={company(r['company']):ticker(r['ticker']) for r in b['original_rows'] if r['ticker']}
    lookup.update({company(k):v for k,v in ALIASES['company_to_ticker'].items()})
    baseline={(ticker(r['ticker']),r['year']) for r in b['original_rows'] if r['ticker'] and r['status'].startswith('FOUND')}
    baseline|={(lookup[company(r['company'])],r['year']) for r in b['raw_rows'] if r['status'].startswith('FOUND')}
    text_pairs=set()
    for f in b['text_files']:
        c,y=f[3:-4].rsplit('_',1)
        assert company(c) in lookup, f
        text_pairs.add((lookup[company(c)],y))
    baseline|=text_pairs
    found={(ticker(r['ticker']),r['year']) for r in rows if r['status']=='FOUND'}
    original_missing={(ticker(r['ticker']),r['year']) for r in b['original_rows'] if r['status']=='NOT_FOUND'}
    scope={r['ticker']:r for r in read('kz_expansion_scope.json')}
    current={t for t,r in scope.items() if r['scope']=='current_bond_only'}
    fresh=found-baseline
    metrics={'url_checks':len(rows),'found_rows':sum(r['status']=='FOUND' for r in rows),
        'found_unique_urls':len({r['url'] for r in rows if r['status']=='FOUND'}),
        'verified_company_years':len(found),'baseline_company_years':len(baseline),'baseline_companies':len({t for t,y in baseline}),
        'baseline_text_files':len(b['text_files']),'baseline_text_company_years':len(text_pairs),
        'new_company_years':len(fresh),'new_companies':len({t for t,y in found}-{t for t,y in baseline}),
        'new_companies_vs_original_roster':len({t for t,y in found}-set(lookup.values())),
        'current_bond_only_new_companies':len({t for t,y in found}&current),
        'current_bond_only_company_years':len({(t,y) for t,y in found if t in current}),
        'historical_bond_company_years':len({(t,y) for t,y in found if t=='SNRG'}),
        'supplementary_unlisted_kazpost_company_years':len({(t,y) for t,y in found if t=='KZPS'}),
        'original_not_found':len(original_missing),'original_not_found_recovered':len(original_missing&found),
        'original_not_found_unresolved':len(original_missing-found),
        'new_company_years_by_year':{y:sum(yr==y for t,yr in fresh) for y in map(str,range(2021,2026))}}
    return rows,baseline,found,original_missing,scope,metrics,raw

def check(mode):
    rows,baseline,found,missing,scope,m,raw=load()
    if mode=='evidence':
        logs=[json.loads(s) for s in (D/'kz_expansion_checks.jsonl').read_text().splitlines()]
        good={r['url'] for r in logs if r['curl_exit']==0 and r['http'] in ('200','206') and r['signature'].startswith('%PDF')}
        provenance=read('kz_expansion_provenance.json')
        for r in rows:
            if r['status']!='FOUND':continue
            assert r['url'] in good and r['url'] in provenance,r['url']
            p=provenance[r['url']]
            if 'document' in p:
                d=p['document'];assert re.fullmatch(r'Годовой отчет за '+r['year']+r' год',d['name']),d
                assert ticker(d['org_code'])==ticker(r['ticker'])
                assert not d['date0'] or d['date0']<='2026-10-05'
        assert not any(r['status']=='FOUND' and r['url'].endswith('/SNRG/snrgp_2021_rus.pdf') for r in rows)
        print('EVIDENCE_OK',m['found_unique_urls'])
    elif mode=='coverage':
        attempted={(ticker(r['ticker']),r['year']) for r in rows}
        assert missing<=attempted,missing-attempted
        outcomes=list(csv.DictReader((D/'kz_expansion_original_outcomes.csv').open(),delimiter=';'))
        assert {(r['ticker'],r['year']) for r in outcomes}==missing
        for r in outcomes:assert (r['status']=='FOUND')==((r['ticker'],r['year']) in found)
        print('COVERAGE_OK',len(missing))
    elif mode=='target':
        b={r['org_code'] for r in read('kz_expansion_bonds_raw.json')}
        s={r['org_code'] for r in read('kz_expansion_shares_raw.json')}
        current={t for t,r in scope.items() if r['scope']=='current_bond_only' and any(ft==t for ft,y in found)}
        assert len(current)>=40
        assert current<=b-s
        for t in current:
            assert scope[t]['bond_codes'] and not scope[t]['share_codes']
            assert 'Казахстан' in scope[t]['address']
        print('TARGET_OK',len(current))
    elif mode=='format':
        def allowed(u):
            host=urlsplit(u).hostname or ''
            return bool(host) and not host.endswith(('.ru','.su','.рф'))
        assert not allowed('https://example.ru/test.pdf') and allowed('https://kase.kz/files/a.pdf')
        for r in rows:
            assert r['country']=='Kazakhstan' and r['year'] in map(str,range(2021,2026))
            assert allowed(r['url'])
            assert r['status'] in ('FOUND','NOT_FOUND')
        for log in (D/'kz_expansion_checks.jsonl').read_text().splitlines():
            e=json.loads(log);assert allowed(e['effective_url'])
        summary=['SUMMARY','новых компаний '+str(m['new_companies']),'новых компания-лет '+str(m['new_company_years'])]
        assert raw[-1]==summary,(raw[-1],summary)
        assert sum(r[0]=='SUMMARY' for r in raw)==1
        assert read('kz_expansion_metrics.json')==m
        clean=list(csv.DictReader((D/'kz_expansion_found_new.csv').open(),delimiter=';'))
        assert len(clean)==len({(ticker(r['ticker']),r['year']) for r in clean})==m['new_company_years']
        assert {(ticker(r['ticker']),r['year']) for r in clean}==found-baseline
        print('FORMAT_OK',summary)
    else:raise ValueError(mode)
if __name__=='__main__':check(sys.argv[1])
