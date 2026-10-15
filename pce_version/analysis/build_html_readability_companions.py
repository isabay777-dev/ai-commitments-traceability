"""Source-preserving alternative HTML extraction; original texts/locators unchanged.
Block boundaries retained, inline spans concatenated, preventing intra-word breaks.
"""
import hashlib,json,re,zipfile
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'sources_first_followup'
def main():
 rows=json.loads((BASE/'retrieval_manifest.json').read_text()); sources={r['file']:r for r in rows if r.get('status')=='extracted_unverified' and r.get('kind')=='html'}
 ep=BASE/'esef_recovery_manifest.json'
 if ep.exists():
  for r in json.loads(ep.read_text()):
   if r['status']=='recovered':sources[r['file']]=r
 output=BASE/'readability_manifest.json';done=json.loads(output.read_text()) if output.exists() else {}
 for file,r in sources.items():
  if file in done:continue
  raw=ROOT/r.get('raw_path',r.get('archive_path'))
  if raw.suffix=='.zip':
   with zipfile.ZipFile(raw) as z:data=z.read(r['selected_member_path'])
  else:data=raw.read_bytes()
  data=re.sub(rb'data:image/[^;"\s]+;base64,[A-Za-z0-9+/=\r\n]+',b'data:image/omitted-base64',data)
  soup=BeautifulSoup(data,'lxml')
  for tag in list(soup.find_all(['script','style','head'])):tag.decompose()
  for tag in list(soup.find_all(lambda t:t.name and t.name.lower() in ['ix:hidden','ix:header'])):tag.decompose()
  for tag in soup.find_all(['div','p','br','tr','td','th','li','h1','h2','h3','h4','section','table']):
   tag.insert_before('\n');tag.append('\n')
  text=soup.get_text('',strip=False);text=re.sub(r'\n[ \t]*\n+', '\n\n',text)
  dest=BASE/'text'/file.replace('.txt','__blocks.txt');dest.write_text(text)
  done[file]=dict(text_path=str(dest.relative_to(ROOT)),text_sha256=hashlib.sha256(text.encode()).hexdigest(),source_sha256=r.get('source_sha256',r.get('archive_sha256')),archive_member=r.get('selected_member_path'),role='Alternative full source extraction with block boundaries; inline spans concatenated. Original source and old extracted text retained. No semantic rewriting.',text_characters=len(text))
  output.write_text(json.dumps(done,ensure_ascii=False,indent=2));print(file,flush=True)
if __name__=='__main__':main()
