#!/usr/bin/env python3
"""Table I–IV and Figure 1, WRITING_KIT_v2 §4, C-primary release.

Run from any directory after Rscript scripts/34_models_v2.R and 35_governance_v2.R.
Historical F/A/B/C inputs are read-only. Writes only article1/tables_v2.
"""
from pathlib import Path
import csv
import hashlib
import json
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/article1_mpl_v2')
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'article1/tables_v2'
OUT.mkdir(exist_ok=True)
INPUTS = []
def read(path, sep=','):
    INPUTS.append(path)
    return pd.read_csv(ROOT / path, sep=sep)
def pct(x):
    return f'{x:.1f}'.replace('.', ',')
def ratio(n, d):
    return f'{int(n)}/{int(d)} ({pct(100*n/d)}%)'
def mdtable(df):
    lines = ['| ' + ' | '.join(map(str, df.columns)) + ' |',
             '| ' + ' | '.join(['---']*len(df.columns)) + ' |']
    for row in df.itertuples(index=False, name=None):
        lines.append('| ' + ' | '.join(str(v).replace('|', '/') for v in row) + ' |')
    return '\n'.join(lines)
def panel(filename, rows):
    df = pd.DataFrame(rows)
    assert not df.isna().any().any(), filename
    df.to_csv(OUT / filename, index=False)
    return mdtable(df)

d = read('data/promise_model_final_v2.csv')
old = read('data/promise_model_final.csv')
assert len(d) == d.promise_id.nunique() == 190
assert d.verdict_version.eq('v2_C_primary_2026-10-07').all()
assert d.verdict_final.value_counts().to_dict() == dict(fulfilled=80, partial=46, not_fulfilled=41, dropped=23)
assert old.promise_id.equals(d.promise_id)
assert list(d.loc[d.verdict_final.ne(old.verdict_final), 'promise_id']) == ['P0058']
for col, values in [('fulfilled', ['fulfilled']), ('fulfilled_or_partial', ['fulfilled','partial']), ('dropped', ['dropped'])]:
    assert d[col].eq(d.verdict_final.isin(values).astype(int)).all()
    if col == 'fulfilled':
        assert old[col].equals(d[col])
countries = ['KZ','PL','NL']
spec = []
INPUTS.append('article1/history/all.csv')
with (ROOT / INPUTS[-1]).open() as f:
    for r in csv.reader(f, delimiter=';'):
        if len(r) >= 8 and r[1] == 'SPEC' and r[0] in set(d.promise_id):
            spec.append(dict(promise_id=r[0], deadline_stated=int(r[3]), measurable_target=int(r[4])))
s = pd.DataFrame(spec)
assert len(s) == s.promise_id.nunique() == 190
ds = d.merge(s, validate='one_to_one')
assert ds.measurable_target.sum() == 11 and ds.deadline_stated.sum() == 40

rows = []
for name, kind, fun in [
    ('Строки обязательств', 'A', lambda q: str(len(q))),
    ('Юридические лица', 'A', lambda q: str(q[['country','firm']].drop_duplicates().shape[0])),
    ('Конкретность 2', 'A', lambda q: ratio(q.specificity.eq(2).sum(), len(q))),
    ('Отмечена измеримая цель', 'A', lambda q: ratio(q.measurable_target.sum(), len(q))),
    ('Отмечен срок', 'A', lambda q: ratio(q.deadline_stated.sum(), len(q))),
    ('Полное подтверждение', 'B', lambda q: ratio(q.fulfilled.sum(), len(q))),
    ('Частичное подтверждение', 'B', lambda q: ratio(q.verdict_final.eq('partial').sum(), len(q))),
    ('Продолжение без достаточного подтверждения', 'B', lambda q: ratio(q.verdict_final.eq('not_fulfilled').sum(), len(q))),
    ('Ненайденное продолжение', 'B', lambda q: ratio(q.dropped.sum(), len(q))),
    ('Полное или частичное — сводка', 'B', lambda q: ratio(q.fulfilled_or_partial.sum(), len(q)))]:
    rows.append({'Панель':kind, 'Показатель':name, **{c:fun(ds[ds.country.eq(c)]) for c in countries}, 'Всего':fun(ds)})
t1 = panel('Table_I.csv', rows)
note1 = ('Источник: F2 и предварительная модельная компонентная кодировка S. KZ — Казахстан, PL — Польша, NL — Нидерланды. '
         'Панель A: состав и компоненты; B: четыре исхода и отдельная сводка. Не суммировать сводку с исходами. '
         'У 30/40 отмеченных сроков A установил календарный год/конец окна; 10 неопределимы, четыре после 2025. '
         'Это не независимая проверка измеримых целей. Исходы относятся к доступным корпоративным самоотчётам при неодинаковых окнах; '
         'уточнённый протокол C не применялся заново ко всем 190. Округление может давать сумму, отличную от 100%.')

rows = []
for version, frame in [('F2 / C-primary (основной)', d), ('F (архивное сравнение)', old)]:
    for level in [1,2]:
        q = frame[frame.specificity.eq(level)]
        rows.append({'Версия':version,'Конкретность':level,'N':len(q),
                     'Полное':ratio(q.fulfilled.sum(),len(q)),
                     'Полное/частичное':ratio(q.fulfilled_or_partial.sum(),len(q)),
                     'Ненайденное':ratio(q.dropped.sum(),len(q))})
t2a = panel('Table_II_A.csv', rows)
mc = read('results/promise_models_coefficients_v2.csv')
gc = read('results/governance_promise_models_coefficients_v2.csv')
INPUTS.append('article1/analysis_C/metrics.json')
metrics = json.loads((ROOT / INPUTS[-1]).read_text())
def coef(frame, model, term):
    q = frame[frame.model.eq(model) & frame.term.eq(term)]
    assert len(q)==1
    return q.iloc[0]
rows = [{'Оценка':'Разность конкретности 2 − 1', 'Исход':'Полное', 'N/G':'190/83',
         'Результат, п.п.':'−17,9; 95% ДИ ['+pct(metrics['bootstrap']['lower_pp'])+'; '+pct(metrics['bootstrap']['upper_pp'])+']'}]
for model, outcome in [('m2','Полное'),('m3','Полное/частичное')]:
    r=coef(mc,model,'spec2')
    rows.append({'Оценка':model+', spec2','Исход':outcome,'N/G':f'{r.N}/{r.G}',
                 'Результат, п.п.':pct(100*r.estimate)+' (SE '+pct(100*r.se)+')'})
t2b = panel('Table_II_B.csv', rows)
a = read('article1/analysis_A/t1_outcomes.csv',';')
at = a.merge(d[['promise_id','specificity']], left_on='ID',right_on='promise_id',validate='one_to_one')
at = at[at.report_available_verified.eq(1)]
assert len(at)==174
t1spec = [{'Конкретность':i,'Полное при доступном t+1':ratio(q.full.sum(),len(q))}
          for i in [1,2] for q in [at[at.specificity.eq(i)]]]
panel('Supplementary_specificity_t1.csv',t1spec)
note2 = ('Источник: F2, архив F, аудит C, модели 34. Отношение долей ненайденного продолжения: F2 5,39; архив F 5,67. '
         'Повторный поиск 24 исходных dropped: 23 dropped, 1 partial (P0058), 0 full. '
         'ДИ разности full: 10 000 перевыборок целых фирм внутри стран; не интервал отношения долей и не поправка на ошибку кодирования. '
         'm2/m3: страна, spec2, pilot, general, число поздних отчётов, эффекты года, SE по фирме. N — строки, G — фирмы. '
         'SE — стандартная ошибка, не ДИ; оценки LPM умножены на 100. '
         'Диагностика C: 40 отобрано, 38 определимы, 26/38 совпадений, κ=0,577; сравнение моделей, не человеческая валидация. '
         'При t+1 по A: full 33/90 (36,7%) для конкретности 1 и 25/84 (29,8%) для 2; разность −6,9 п.п. '
         'Это отдельная описательная сверка с изменённым доступным составом. В KZ полногоризонтная разность +1,5 п.п.')

episodes = read('article1/analysis_B/episode_outcomes.csv',';')
assert len(episodes)==162
assert episodes[['country','firm_group']].drop_duplicates().shape[0]==82
# B's anchor verdict remains unchanged: P0058 is a later member, not an anchor.
assert not episodes.anchor_ids.str.contains('P0058').any()
assert episodes.member_ids.str.contains('P0058').sum()==1
def sector_rows(all_sectors=False):
    rows=[]
    for country in countries:
        for sector in (['all'] if all_sectors else ['finance','nonfinance']):
            q=d[d.country.eq(country)]; e=episodes[episodes.country.eq(country)]
            if sector!='all':
                q=q[q.sector_group.eq('finance') == (sector=='finance')]
                e=e[e.sector_group.eq('finance') == (sector=='finance')]
            group_rates=e.assign(full=e.verdict_episode.eq('fulfilled')).groupby('firm_group').full.mean()
            rows.append({'Страна / сектор':country+' / '+{'all':'все','finance':'финансы','nonfinance':'нефинансы'}[sector],
                         'Строки full, n/N (%)':ratio(q.fulfilled.sum(),len(q)),
                         'Эпизоды full, n/N (%)':ratio(e.verdict_episode.eq('fulfilled').sum(),len(e)),
                         'Равные веса групп, %':pct(100*group_rates.mean()),'Групп':len(group_rates)})
    return rows
t3a = panel('Table_III_A.csv',sector_rows())
t3b = panel('Table_III_B.csv',sector_rows(True))
note3 = ('Источник: F2 для строк; B для эпизодов и групп. Полные исходы не изменились при переходе F→F2. '
         '190 строк → 162 эпизода; 83 юридических лица → 82 группы после объединения ING. '
         'Эпизод сохраняет исход первого обязательства; P0058 не якорная строка. '
         'Равные веса: сначала доля full среди эпизодов группы, затем среднее этих долей. Это иной оцениваемый показатель. '
         'Проценты вычислены заново из индивидуальных эпизодов, не из округлённых итогов B. '
         'Отраслевые различия описательные; сравнительная объяснительная сила страны и отрасли не оценивалась.')

ct = read('article1/analysis_A/country_t1.csv',';')
rows=[]
for country in countries:
    r=ct[ct.country.eq(country)&ct.outcome.eq('full')].iloc[0]
    rows.append({'Страна':country,'Доступно / все':f'{r.denominator_available}/{r.denominator_all}',
                 'Фирм / всех':f'{r.firms_available}/{r.firms_total}',
                 'Full, n/N (%)':ratio(r.numerator,r.denominator_available),
                 '95% ДИ, %':pct(100*r.ci95_low)+'–'+pct(100*r.ci95_high),
                 'Границы пропусков, %':pct(100*r.missing_all_zero)+'–'+pct(100*r.missing_all_one)})
t4a=panel('Table_IV_A.csv',rows)
rows=[]
for model, term, outcome in [('g1','dig_any','Полное'),('g2','dig_any','Полное'),('g3','dig_any','Полное/частичное'),('g5','dig_nar','Полное')]:
    r=coef(gc,model,term)
    rows.append({'Модель / признак':model+' / '+term,'Исход':outcome,
                 'Оценка, п.п. (SE)':pct(100*r.estimate)+' ('+pct(100*r.se)+')','N/G':f'{r.N}/{r.G}'})
t4b=panel('Table_IV_B.csv',rows)
note4 = ('Панель A: отдельные проверенные исходы A в следующем обозначенном отчётном году, не ровно через 12 месяцев. '
         'Доступны 174/190. ДИ: 50 000 перевыборок фирм внутри страны. Границы пропусков — крайние сценарии, не ДИ; PL 4/30–18/30. '
         'Full/partial: KZ 12/29 (41,4%), PL 9/16 (56,3%), NL 76/129 (58,9%). '
         'Панель B: модели 35 на F2 за весь доступный горизонт. g1: страна и год; g2/g3/g5: также spec2, general, '
         'стандартизованный внутри страны логарифм активов, государственная принадлежность. SE по country × firm. '
         'g1 предварительно требует наличие активов: 164/72; затем 36 строк исключены из-за state, остаётся 128/57 '
         '(KZ 19/11, PL 15/6, NL 94/40). Смена g1→g2 отражает также состав. Отрасль и независимые директора не контролируются. '
         'Широкий dig_any и узкий dig_nar — косвенные биографические признаки. Эти две панели не являются одной моделью. '
         'Отсутствие убедительной поддержки положительного ожидания не устанавливает нулевой эффект.')

table_blocks = [('I','Проверяемые компоненты и наблюдаемая судьба обязательств',t1,note1),
                ('II','Конкретность и чувствительность связи','### Панель A\n\n'+t2a+'\n\n### Панель B\n\n'+t2b,note2),
                ('III','Финансовый сектор и единицы подсчёта','### Панель A\n\n'+t3a+'\n\n### Панель B\n\n'+t3b,note3),
                ('IV','Временная сопоставимость и совет','### Панель A\n\n'+t4a+'\n\n### Панель B\n\n'+t4b,note4)]
text = '# Таблицы статьи 1\n\nРусские рабочие данные и примечания для автора. Версия v2 C-primary. Заголовки для подачи автор формулирует самостоятельно.\n\n'
for number,title,body,note in table_blocks:
    block=f'## Table {number} · {title}\n\n{body}\n\n**Примечания.** {note}\n'
    (OUT/f'Table_{number}.md').write_text(block)
    text += block+'\n* * *\n\n'
(OUT/'Tables_I_IV.md').write_text(text)

outcomes=['fulfilled','partial','not_fulfilled','dropped']
labels=['Полное подтверждение','Частичное подтверждение','Продолжение без достаточного\nподтверждения','Ненайденное продолжение']
figdata=pd.crosstab(d.specificity,d.verdict_final).reindex(index=[1,2],columns=outcomes)
assert figdata.loc[1].tolist()==[51,24,22,4] and figdata.loc[2].tolist()==[29,22,19,19]
figdata.to_csv(OUT/'Figure_1_data.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white'})
fig,ax=plt.subplots(figsize=(9,4.2))
left=[0.,0.]
for j,(outcome,label,color,hatch) in enumerate(zip(outcomes,labels,['0.2','0.58','0.88','white'],['','///','...','xxx'])):
    values=figdata[outcome].tolist(); widths=[100*n/N for n,N in zip(values,[101,89])]
    ax.barh([0,1],widths,left=left,color=color,edgecolor='black',hatch=hatch,height=.48,label=label,linewidth=.7)
    for i,(n,w) in enumerate(zip(values,widths)):
        if w<6:
            ax.annotate(str(n),(left[i]+w/2,i),xytext=(102,i),ha='left',va='center',arrowprops={'arrowstyle':'-','color':'black'},annotation_clip=False)
        else: ax.text(left[i]+w/2,i,str(n),ha='center',va='center',color='white' if j==0 else 'black',bbox=dict(facecolor=color,edgecolor='none',pad=1))
    left=[l+w for l,w in zip(left,widths)]
ax.set(xlim=(0,100),ylim=(1.6,-.6),yticks=[0,1],yticklabels=['Конкретность 1\nN = 101','Конкретность 2\nN = 89'],xlabel='Доля строк обязательств, %')
ax.spines[['top','right']].set_visible(False)
ax.legend(loc='upper center',bbox_to_anchor=(.46,-.25),ncol=2,frameon=False,fontsize=9)
fig.subplots_adjust(left=.19,right=.93,bottom=.36,top=.97)
for ext in ['png','tiff','eps','pdf']:
    fig.savefig(OUT/f'Figure_1_specificity.{ext}',dpi=300)
plt.close(fig)
(OUT/'Figure_1.md').write_text('# Figure 1 · Исходы по конкретности\n\n![Figure 1 — четыре исхода по конкретности](Figure_1_specificity.png){width=6.3in}\n\n'
    'Данные: F2, C-primary; числа внутри сегментов — n, рядом с группами — N; ширины по точным n/N. '
    'Исходы корпоративного раскрытия при неодинаковом горизонте. Аудит исходного F: при конкретности 2 partial 21→22, dropped 20→19, full 29 без изменения. '
    'Чёрно-белое построение кодом по существующим данным; это не генеративное изображение и не причинная диаграмма.\n')

p=read('data/panel_ai_disclosure.csv')
trend=p.groupby(['country','year']).ai_any.agg(['sum','count']).reset_index()
trend['share']=trend['sum']/trend['count']
trend.to_csv(OUT/'Supplementary_Figure_S1_data.csv',index=False)
fig,ax=plt.subplots(figsize=(8,4.8))
for c,marker,ls in zip(countries,['o','s','^'],['-','--',':']):
    q=trend[trend.country.eq(c)]
    ax.plot(q.year,q.share*100,marker=marker,linestyle=ls,color='black',label=c)
ax.set(xticks=[2021,2022,2023,2024,2025],ylim=(0,100),xlabel='Отчётный год',ylabel='Отчёты со словарным упоминанием ИИ, %')
ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
for ext in ['png','tiff','pdf']:
    fig.savefig(OUT/f'Supplementary_Figure_S1.{ext}',dpi=300)
plt.close(fig)
denoms='; '.join(c+': '+', '.join(f'{int(r.year)} — {int(r["sum"])}/{int(r["count"])}' for _,r in trend[trend.country.eq(c)].iterrows()) for c in countries)
(OUT/'Supplementary_Figure_S1.md').write_text('# Supplementary Figure S1 · Словарные упоминания ИИ\n\n![Supplementary Figure S1](Supplementary_Figure_S1.png){width=6.3in}\n\n'
    'Источник: исходная панель 1 098 отчётов до фильтра непригодных текстов в анализе обещаний. '+denoms+'. '
    'Состав по годам меняется. Включены четыре файла из BAD скрипта 21; сырые находки могут отражать повреждения текста. '
    'График описывает поиск в доступной панели, не использование ИИ и не качество очищенного корпуса. К RQ2 об исходах по конкретности не относится.\n')

manifest={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in INPUTS}
(OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
(OUT/'README.md').write_text('# Экспонаты v2\n\nСборка: `Rscript scripts/34_models_v2.R`, `Rscript scripts/35_governance_v2.R`, `python3 scripts/36_tables_v2.py` из корня проекта. '
    'Затем запустить `scripts/37_build_docx_v2.py` интерпретатором Python с python-docx и доступным pandoc: он создаёт Word-файлы. '
    'Первые два скрипта экспортируют точные коэффициенты и фактические выборки; третий собирает русские рабочие экспонаты. '
    'Tables_I_IV.md / .docx — отдельный файл таблиц; CSV — данные панелей; Figure_1.md / .docx — рисунок и рабочее примечание; TIFF/EPS — экспорт для подачи, PNG — предпросмотр. '
    'Supplementary Figure S1 — дополнительный график сырой панели, не Figure 1. F2 принят по C-primary; F/A/B/C сохранены как история. '
    'Source manifest содержит SHA-256 входов. После изменения исходов сначала повторить R, затем Python.\n')
print('Validated: 190 rows / 83 firms; 80/46/41/23; Table I–IV, Figure 1 and Supplementary S1 written.')
