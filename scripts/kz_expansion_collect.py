#!/usr/bin/env python3
"""Read-only curl verification; append each completed probe immediately using echo >>."""
import csv, io, json, re, shlex, subprocess, sys, threading, tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/kz_expansion_urls.csv'
LOG=ROOT/'data/kz_expansion_checks.jsonl'
LOCK=threading.Lock()
FIELDS='country company ticker sector year language doc_type url status note'.split()
def append(row):
    stream=io.StringIO();csv.writer(stream,delimiter=';',lineterminator='').writerow([row.get(k,'') for k in FIELDS])
    # The entire CSV line is shell-quoted, never interpolated as shell code.
    subprocess.run(['/bin/sh','-c','echo '+shlex.quote(stream.getvalue())+' >> '+shlex.quote(str(OUT))],check=True)
def probe(row):
    row=dict(row);url=row['url'];host=urlsplit(url).hostname or ''
    assert not host.endswith(('.ru','.su','.рф'))
    with tempfile.TemporaryDirectory(prefix='kz-probe-') as d:
        f=Path(d)/'body'
        p=subprocess.run(['curl','-sL','-A','Mozilla/5.0','-r','0-4','--connect-timeout','10','--max-time','30','--max-filesize','2000000','-o',str(f),'-w','%{http_code}\t%{url_effective}',url],capture_output=True)
        meta=p.stdout.decode(errors='replace').split('\t',1);data=f.read_bytes() if f.exists() else b''
    signature=data[:5].decode('ascii',errors='replace');http=meta[0]
    good=p.returncode==0 and http in ('200','206') and data.startswith(b'%PDF')
    record={'url':url,'ticker':row['ticker'],'year':str(row['year']),'checked_date':'2026-10-05','http':http,'curl_exit':p.returncode,'signature':signature,'bytes':len(data),'effective_url':meta[-1],'source':row.get('note',''),'stderr':p.stderr.decode(errors='replace')[:300]}
    row.update(country='Kazakhstan',status='FOUND' if good else 'NOT_FOUND')
    row['note']=row.get('note','')+f' | 2026-10-05 curl range=0-4 HTTP={http} exit={p.returncode} signature={signature!r}'
    with LOCK:
        append(row)
        with LOG.open('a') as log:log.write(json.dumps(record,ensure_ascii=False)+'\n')
        if good:print('FOUND',row['ticker'],row['year'],row['url'],flush=True)
    return good
if __name__=='__main__':
    jobs=json.loads(Path(sys.argv[1]).read_text())
    done=set()
    if LOG.exists():done={json.loads(x)['url'] for x in LOG.read_text().splitlines()}
    jobs=[r for r in jobs if r['url'] not in done]
    print('PROBES',len(jobs),flush=True)
    with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(probe,jobs))
    print('COMPLETE',len(results),'FOUND',sum(results),flush=True)
