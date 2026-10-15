"""Build source-only packets, without copying historical outcome labels."""
import csv
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'first_followup_packets'


def context(text, excerpt):
    # Search normalized text for long archived-excerpt anchors. This is retrieval,
    # never eligibility/outcome adjudication. Full texts remain available to coders.
    normal = re.sub(r'\s+', ' ', text)
    quote = re.sub(r'\s+', ' ', excerpt)
    positions = []
    for start in range(0, max(1, len(quote) - 45), 30):
        anchor = quote[start:start+60]
        pos = normal.casefold().find(anchor.casefold())
        if pos >= 0:
            positions.append(pos)
    if not positions:
        return '', 'archived_excerpt_anchor_not_found'
    pos = sorted(positions)[len(positions)//2]
    return normal[max(0, pos-2200):pos+3300], 'archived_excerpt_anchor_located'


def main():
    DEST.mkdir(exist_ok=True)
    work = list(csv.DictReader((ROOT / 'analysis/out/first_followup_worklist_183.csv').open()))
    urls = {r['promise_id']:r for r in csv.DictReader((ROOT / 'analysis/out/first_followup_source_urls.csv').open())}
    retrieved = json.loads((ROOT / 'sources_first_followup/retrieval_manifest.json').read_text())
    sources = {r['file']:r for r in retrieved}
    for recovery_name in ['archive_recovery_manifest.json','esef_recovery_manifest.json']:
        recovery = ROOT / 'sources_first_followup' / recovery_name
        if recovery.exists():
            for fixed in json.loads(recovery.read_text()):
                if fixed['status'] != 'recovered':
                    continue
                old = sources[fixed['file']]
                assert old['source_sha256'] == fixed['archive_sha256']
                sources[fixed['file']] = dict(old, status='extracted_unverified',
                    text_path=fixed['output_path'], text_sha256=fixed['output_sha256'],
                    archive_member_path=fixed['selected_member_path'],
                    source_caveat=fixed['source_caveat'])
    supplement_path = ROOT / 'sources_first_followup/source_supplements.json'
    supplements = json.loads(supplement_path.read_text()) if supplement_path.exists() else {}
    readability_path = ROOT / 'sources_first_followup/readability_manifest.json'
    readability = json.loads(readability_path.read_text()) if readability_path.exists() else {}
    manifest = []
    crosswalk = []
    for i, case in enumerate(work, 1):
        neutral = f'FF{i:04d}'
        mapped = urls[case['promise_id']]
        orig = sources.get(mapped['original_report_file'], {})
        follow = sources.get(mapped['first_available_report_file'], {})
        ready = all(r.get('status') == 'extracted_unverified' for r in [orig,follow])
        packet = dict(case_id=neutral, country=case['country'], company_identifier=case['firm'],
                      commitment_year=int(case['commitment_year']),
                      first_available_report_year=int(case['first_available_report_year']),
                      category=case['category'], original_excerpt=case['original_excerpt'],
                      ready_for_source_review=ready,
                      source_rule='First available subsequent report; no later reports or historical outcome labels may be used.',
                      original_source={k:orig.get(k) for k in ['file','url','final_url','text_path','raw_path','source_sha256','text_sha256','text_sha256_scope','text_file_sha256','status','archive_member_path','source_caveat']},
                      followup_source={k:follow.get(k) for k in ['file','url','final_url','text_path','raw_path','source_sha256','text_sha256','text_sha256_scope','text_file_sha256','status','archive_member_path','source_caveat']})
        for source_key, record in [('original_source', orig), ('followup_source', follow)]:
            if record.get('file') in supplements:
                packet[source_key]['supplementary_sources'] = [supplements[record['file']]]
            if record.get('file') in readability:
                packet[source_key].setdefault('supplementary_sources', []).append(readability[record['file']])
        if ready:
            original_text = (ROOT / orig['text_path']).read_text()
            followup_text = (ROOT / follow['text_path']).read_text()
            packet['original_cover_excerpt'] = original_text[:2500]
            packet['followup_cover_excerpt'] = followup_text[:2500]
            packet['original_context'],packet['original_context_retrieval'] = context(original_text, case['original_excerpt'])
            for supplement in packet['original_source'].get('supplementary_sources', []):
                extra_text = (ROOT / supplement['text_path']).read_text()
                extra_context, found = context(extra_text, case['original_excerpt'])
                if extra_context:
                    packet['original_supplementary_context'] = extra_context
                    packet['original_supplementary_context_source'] = supplement.get('archive_member') or supplement['text_path']
        (DEST / (neutral+'.json')).write_text(json.dumps(packet, ensure_ascii=False, indent=2))
        manifest.append(dict(case_id=neutral,country=case['country'],ready=ready,
                             packet_path=str((DEST/(neutral+'.json')).relative_to(ROOT))))
        crosswalk.append(dict(case_id=neutral,promise_id=case['promise_id']))
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2))
    with (ROOT/'analysis/out/first_followup_id_crosswalk.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['case_id','promise_id']);w.writeheader();w.writerows(crosswalk)
    print(json.dumps({'cases':len(manifest),'ready':sum(r['ready'] for r in manifest),
                      'ready_KZ_PL':sum(r['ready'] and r['country']!='NL' for r in manifest)}))


if __name__ == '__main__':
    main()
