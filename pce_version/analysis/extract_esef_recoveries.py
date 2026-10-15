"""Extract exactly the XHTML report requested in the frozen inventory from its ESEF ZIP.
No archive member is executed or unpacked onto disk. Raw package is retained.
"""
import hashlib,json,re,zipfile
from pathlib import Path,PurePosixPath
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'sources_first_followup'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    rows=json.loads((BASE/'retrieval_manifest.json').read_text())
    output=BASE/'esef_recovery_manifest.json'
    old=json.loads(output.read_text()) if output.exists() else []
    done={(r['file'],r['archive_sha256']):r for r in old}
    for r in rows:
        if r.get('country')!='NL' or not r.get('required_report_member_basename') or r.get('status')!='unsupported_archive':continue
        if (r['file'],r['source_sha256']) in done:continue
        raw=ROOT/r['raw_path'];assert sha(raw.read_bytes())==r['source_sha256']
        item=dict(file=r['file'],archive_sha256=r['source_sha256'],archive_path=r['raw_path'],source_url=r['url'],original_report_url=r['recovery_of_url'])
        try:
            with zipfile.ZipFile(raw) as z:
                inventory=z.infolist()
                candidates=[i for i in inventory if PurePosixPath(i.filename).name==r['required_report_member_basename']]
                # Match exact frozen XHTML filename, never a financial statement selected by size.
                assert len(candidates)==1, [i.filename for i in candidates]
                member=candidates[0];parts=PurePosixPath(member.filename)
                assert not parts.is_absolute() and '..' not in parts.parts and member.file_size<=512*1024*1024
                data=z.read(member)
                item.update(selected_member_path=member.filename,selected_member_sha256=sha(data),selected_member_bytes=len(data),archive_member_inventory=[dict(path=i.filename,bytes=i.file_size,crc32=f'{i.CRC:08x}') for i in inventory])
            # Discard only embedded image payloads from the parser input; retain original bytes/hash above.
            parse_data=re.sub(rb'data:image/[^;"\s]+;base64,[A-Za-z0-9+/=\r\n]+',b'data:image/omitted-base64',data)
            soup=BeautifulSoup(parse_data,'lxml')
            item['html_title']=soup.title.get_text(' ',strip=True) if soup.title else ''
            for tag in list(soup.find_all(['script','style','head'])):tag.decompose()
            for tag in list(soup.find_all(lambda t:t.name and t.name.lower() in ['ix:hidden','ix:header'])):tag.decompose()
            text=soup.get_text('\n',strip=True);assert len(text)>1000
            dest=BASE/'text'/r['file'];dest.write_text(text)
            item.update(status='recovered',output_path=str(dest.relative_to(ROOT)),output_sha256=sha(text.encode()),text_characters=len(text),source_caveat='Same ESEF package/revision as frozen report URL; exact report basename selected. Entity, period and outcome require independent source review.',extraction_method='BeautifulSoup lxml visible body; script/style/head and ix:hidden/header removed; embedded base64 images omitted only from parsing input')
        except Exception as error:item.update(status='recovery_failed',error=str(error))
        done[(r['file'],r['source_sha256'])]=item
        output.write_text(json.dumps(list(done.values()),ensure_ascii=False,indent=2))
        print(r['file'],item['status'],flush=True)
if __name__=='__main__':main()
