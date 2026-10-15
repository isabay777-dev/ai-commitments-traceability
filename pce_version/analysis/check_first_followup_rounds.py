"""Audit independent source-only rounds; this does not adjudicate disagreements."""
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def normal(text):
    text = unicodedata.normalize('NFKC', text).casefold()
    return re.sub(r'\s+', ' ', text).strip()


def present(quote, text):
    if not quote:
        return False
    chunks = re.split(r'\[?…\]?|\.\.\.|\[\.\.\.\]', str(quote))
    chunks = [normal(x) for x in chunks if len(normal(x)) >= 18]
    return bool(chunks) and all(x in normal(text) for x in chunks)


def main():
    manifest = {r['case_id']:r for r in json.loads((ROOT/'first_followup_packets/manifest.json').read_text())}
    rounds = {}; flags = []
    for name in ['A','B','NL_A','NL_B']:
        path = ROOT/'first_followup_rounds'/(name+'.json')
        rows = json.loads(path.read_text()) if path.exists() else []
        assert len(rows) == len({r['case_id'] for r in rows}), 'Duplicate coded IDs'
        rounds[name] = {r['case_id']:r for r in rows}
        for row in rows:
            cid = row['case_id']; assert cid in manifest and manifest[cid]['ready']
            packet = json.loads((ROOT/manifest[cid]['packet_path']).read_text())
            issues = []
            for source, field in [('original_source','original_quote'),('followup_source','followup_quote')]:
                text = (ROOT/packet[source]['text_path']).read_text()
                text += '\n'.join((ROOT/x['text_path']).read_text() for x in packet[source].get('supplementary_sources', []))
                quote = row.get(field)
                required = field == 'original_quote' or row.get('first_report_status') in ['fulfilled','partial','not_fulfilled']
                if required and not present(quote,text): issues.append(field+'_not_literal_or_too_short')
            if row.get('source_adequacy')!='assessable' or row.get('eligibility')=='unresolved':
                if row.get('first_report_status') is not None: issues.append('outcome_assigned_to_unresolved_case')
            if row.get('first_report_status')=='dropped':
                if not row.get('search_terms') or not row.get('searched_full_text'): issues.append('negative_search_audit_missing')
            if issues: flags.append(dict(round=name,case_id=cid,issues=issues))
    rounds['A'].update(rounds['NL_A'])
    rounds['B'].update(rounds['NL_B'])
    common = sorted(set(rounds['A'])&set(rounds['B']))
    signatures = lambda x:(x.get('source_adequacy'),x.get('eligibility'),x.get('first_report_status'))
    disagree = [cid for cid in common if signatures(rounds['A'][cid])!=signatures(rounds['B'][cid])]
    summary = dict(round_A_cases=len(rounds['A']),round_B_cases=len(rounds['B']),paired_cases=len(common),
                   joint_assessability_eligibility_outcome_disagreements=disagree,
                   quote_and_rule_flags=flags, human_validation=False,
                   caution='Literal quote matching does not establish correct object linkage, scope or outcome; flags require source review.')
    out=ROOT/'analysis/out/first_followup_round_checks.json';out.write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
