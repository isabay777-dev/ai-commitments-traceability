# Blind human validation of AI-commitment coding / Слепая ручная валидация кодирования

Files / Файлы: `coding_sheet.csv` (give to coders), `key_hidden.csv` (**authors: do NOT open until all coding and adjudication are finished / авторы: НЕ открывать до завершения кодирования и согласования**), `compare_after_coding.py`, `build_kit.py` (how the sample was drawn).

---
## ENGLISH

### 1. Who codes
Two language-competent coders per country, working **independently and blind** (no discussion, no access to model verdicts or the key): Kazakhstan, Kazakh/Russian; Poland, Polish; Netherlands, English/Dutch. Each coder gets their own copy of `coding_sheet.csv` (rename e.g. `coding_sheet_KZ_A.csv`) and fills `coder_name` on every row. Coders code only their own country's rows. The sample is 76 commitments: all 56 KZ+PL commitments (27 KZ, 29 PL) plus 20 NL (5 per outcome). Sample seed 20261015.

### 2. What you see and what you do
For each row you see the **original commitment wording** (an excerpt of up to 300 characters from the original report, in the original language), the source report (file name and URL) and the list of later reports of the same company. The excerpt is a window and may start or end mid-sentence: open the source report and read the surrounding passage to identify the exact commitment (the object, function and any scale). Then (a) code the **specificity of the wording**, and (b) **search the later reports yourself** (use the listed URLs; search by product, process, partner and spelling variants, also without the words "AI/ИИ/AI/sztuczna inteligencja"; for Kazakh use both Kazakh and Russian forms) and code what they say. You do not see any prior verdict or evidence.

### 3. Specificity rule (wording only; later reports are not used)
**Specific (1)** = the wording names a concrete AI process, function, product or area **and** at least one of: a current achieved stage (a pilot or test already running, or a solution already implemented that is to be extended; a future intention to implement or develop is not a stage), a deadline or time frame, a quantitative target or result, an investment amount, a named AI solution, product, platform or model, or a named external partner, vendor or institution. **Otherwise 0** (partly specific). Record `specificity_specific` (0/1), `process_named` (0/1) and, as text or 0/1, `stage`, `deadline`, `target`, `amount`, `solution_or_partner`. Only the company's own AI counts: a description of a law or market trend does not.

### 4. Later status (`later_status`): pick one
Rule: an outcome above "ongoing" needs evidence of an **achieved state** (launched, deployed, operating, in use, completed, rolled out, piloted in live operation) for the **same** promised object or function. Activity language alone (developing, working on, progressing towards, preparing, continuing development, planning, on track, positioned to deliver) never counts as achievement. Deadlines are recorded separately; a future deadline is not a failure.
- `full` (= fulfilled): a later report states that the promised object or function is implemented, launched or in use at the explicitly promised scale. If the commitment was to run a study, pilot or test, its completion or live operation suffices. A broad general-AI commitment requires at least one named, implemented AI process within its scope; repeating the strategy is not enough. Scope or deadline absent from the original is not invented.
- `partial`: achieved-state evidence for the same object that is incomplete: a live pilot where full deployment was promised, some of the promised functions live, or a smaller scale, unit, market or product line. Continuing development, readiness work, expenditure or a repeated intention alone does not qualify.
- `ongoing` (= not_fulfilled): the same object reappears only as ongoing work, development, testing without a live pilot, renewed plan, postponement or explicit cancellation.
- `untraced` (= dropped): no identifiable continuation located in the available later reports; not a synonym for cancellation.
- `not_a_commitment` (= not_a_promise): the original fragment is not a company undertaking to implement, use or scale AI in its own operations or products.

### 5. What counts as evidence
- The **same AI object or function** as the original commitment. A host system, platform or product **without an AI component** (e.g. a digital platform, a data warehouse, an app that merely exists) does **not** count.
- General statements that "AI is used" do not trace a specific commitment; a general-AI commitment needs a named implemented AI process.
- Activity language ("developing", "working on", "preparing") is not achievement (see section 4).
- Fill `evidence_quote` (verbatim, original language), `evidence_report_year`, `evidence_page`, `report_language`. For `untraced` write the reports and search terms tried in `notes`.
- **Retrieval failures and unresolved cases:** if a listed report cannot be opened, is unreadable (including broken PDF extraction), or its URL is dead, record the affected report, retrieval attempts and limitation in `notes` (e.g. "RETRIEVAL FAILURE: 2025 report, 404"). Search any other available reports within this kit's specified window, but do not infer the missing report's content. If unavailable or unreadable material prevents a supported judgement, leave `later_status` blank and mark the case `UNRESOLVED` in `notes`; do not choose a best category. Use `untraced` only after an adequate search of accessible, readable reports in the required window finds no identifiable AI-component continuation. A missing document is not evidence of non-fulfilment, non-continuation or cancellation.
- Record `minutes_spent` per item.

### 6. After coding
1. Authors collect the filled sheets (do not open `key_hidden.csv`).
2. Run the comparison on the two coders' sheets for inter-coder agreement; list disagreements.
3. **Adjudication:** the two coders of each country (or a third competent person) discuss each disagreement with the evidence quotes and agree a final code. Save a file `adjudicated.csv` with columns `vid, later_status, specificity_specific`.
4. Only now open `key_hidden.csv` (the script reads it).
5. Run: `python3 validation/compare_after_coding.py A.csv B.csv --adjudicated adjudicated.csv` (all sheets of all countries may be passed together). It writes `results.md` and `corrected_codes.csv`.

### 7. What to report
Per country (= language) and pooled: percent agreement and Cohen's kappa between the two coders and between the adjudicated codes and the model, for (i) **full vs not-full**, (ii) **traced vs untraced**, (iii) specificity (specific vs not), plus the 4-category outcome; the confusion table; the number of retrieval failures and of `not_a_commitment`; median minutes per item. Mapping to model labels: full=fulfilled, partial=partial, ongoing=not_fulfilled, untraced=dropped.
**Re-estimating the KZ-PL contrast with corrected codes:** make a copy of `repo/data/promise_model_F5.csv` (do not edit the original); for the sampled `promise_id`s replace `verdict_final` with the adjudicated model label and update the derived columns the script uses consistently (`fulfilled`, `fulfilled_or_partial`, `dropped`); drop items judged `not_a_commitment`; point `analysis/final_analysis.R` at the copy (the path on the `read.csv` line; its stopifnot on 183 rows and `verdict_version` must be relaxed in the copy) and compare the KZ-PL coefficients with the published ones. Since the sample is all of KZ and PL (the contrast is in these two) and a stratified NL subsample, treat NL results as validation only.

---
## РУССКИЙ

### 1. Кто кодирует
Два кодировщика на страну, владеющие языком, работают **независимо и слепо** (без обсуждения, без доступа к вердиктам модели и ключу): Казахстан, казахский/русский; Польша, польский; Нидерланды, английский/нидерландский. Каждый получает свою копию `coding_sheet.csv` (например, `coding_sheet_KZ_A.csv`) и заполняет `coder_name` в каждой строке. Кодируются только строки своей страны. Выборка: 76 обязательств (все 56 обязательств KZ+PL (27 KZ, 29 PL) и 20 NL, по 5 на исход). Seed 20261015.

### 2. Что вы видите и что делаете
В строке: **исходная формулировка обязательства** (фрагмент до 300 символов из исходного отчёта, на языке оригинала), исходный отчёт (имя файла и URL) и список более поздних отчётов компании. Фрагмент может начинаться/обрываться посреди предложения: откройте отчёт и прочитайте окружающий текст, чтобы точно определить объект, функцию и масштаб. Затем (а) закодируйте **конкретность формулировки**; (б) **сами найдите в поздних отчётах** следы обязательства (по продукту, процессу, партнёру и вариантам написания, в том числе без слов «ИИ/AI»; для казахского ищите и казахские, и русские формы) и закодируйте статус. Прежних вердиктов и доказательств вы не видите.

### 3. Правило конкретности (только формулировка, поздние отчёты не используются)
**Конкретно (1)** = названы конкретный ИИ-процесс, функция, продукт или область **и** хотя бы одно из: текущая достигнутая стадия (пилот или тест уже идёт, либо решение уже внедрено и будет расширено; будущее намерение внедрить или разработать стадией не является), срок или временные рамки, количественная цель или результат, сумма инвестиций, названное ИИ-решение, продукт, платформа или модель, либо названный внешний партнёр, поставщик или организация. **Иначе 0** (частично конкретно). Заполните `specificity_specific` (0/1), `process_named` (0/1), а также `stage`, `deadline`, `target`, `amount`, `solution_or_partner`. Учитывается только собственный ИИ компании: описание закона или рыночного тренда не считается.

### 4. Поздний статус (`later_status`): выберите один
Правило: исход выше «ongoing» требует свидетельства **достигнутого состояния** (запущено, развёрнуто, работает, используется, завершено, внедрено, пилот в реальной эксплуатации) для **того же** обещанного объекта или функции. Язык активности (разрабатываем, работаем над, продвигаемся к, готовим, продолжаем разработку, планируем, по плану, готовы поставить) достижением не считается никогда. Сроки фиксируются отдельно; будущий срок не есть провал.
- `full` (= fulfilled): поздний отчёт сообщает, что обещанный объект или функция внедрены, запущены или используются в явно обещанном масштабе. Если обещано провести исследование, пилот или тест, достаточно его завершения или реальной эксплуатации. Для широкого обязательства по ИИ вообще нужен хотя бы один названный внедрённый ИИ-процесс в его рамках; повтор стратегии недостаточен. Масштаб или срок, которых не было в оригинале, не додумываются.
- `partial`: свидетельство достигнутого состояния для того же объекта, но неполное: действующий пилот при обещанном полном внедрении, часть обещанных функций работает, либо меньший масштаб, подразделение, рынок или продуктовая линия. Продолжающаяся разработка, подготовка, расходы или повтор намерения сами по себе не подходят.
- `ongoing` (= not_fulfilled): тот же объект появляется только как текущая работа, разработка, тестирование без реального пилота, обновлённый план, перенос или явная отмена.
- `untraced` (= dropped): в доступных поздних отчётах не найдено идентифицируемого продолжения; это не синоним отмены.
- `not_a_commitment` (= not_a_promise): исходный фрагмент не является обязательством компании внедрять, использовать или масштабировать ИИ в собственных операциях или продуктах.

### 5. Что считается доказательством
- **Тот же ИИ-объект или функция**, что и в обязательстве. Система-«хозяин», платформа или продукт **без ИИ-компонента** (цифровая платформа, хранилище данных, приложение как таковое) **не** считаются.
- Общие слова «используем ИИ» не прослеживают конкретное обязательство; для общего ИИ-обязательства нужен названный внедрённый ИИ-процесс.
- Язык активности («разрабатываем», «работаем», «готовим») не есть достижение (см. п. 4).
- Заполните `evidence_quote` (дословно, на языке оригинала), `evidence_report_year`, `evidence_page`, `report_language`. Для `untraced` в `notes` укажите, какие отчёты и какие поисковые слова проверены.
- **Сбои получения и неразрешённые случаи:** если указанный отчёт не открывается, нечитаем (включая испорченное извлечение текста из PDF) или ссылка не работает, запишите в `notes` год отчёта, попытки получения и ограничение (например, «RETRIEVAL FAILURE: отчёт 2025, 404»). Проверьте другие доступные отчёты в пределах окна этого набора, но не домысливайте содержание отсутствующего. Если недоступный или нечитаемый материал мешает обоснованному выводу, оставьте `later_status` пустым и отметьте `UNRESOLVED` в `notes`; не выбирайте «лучшую» категорию. `untraced` ставьте только после достаточного поиска по доступным, читаемым отчётам в требуемом окне, если продолжение ИИ-компонента не найдено. Отсутствие документа не доказывает невыполнение, отсутствие продолжения или отмену.
- Записывайте `minutes_spent` по каждой строке.

### 6. После кодирования
1. Авторы собирают заполненные листы (`key_hidden.csv` не открывать).
2. Запустите сравнение по листам двух кодировщиков для межкодировочного согласия; получите список расхождений.
3. **Согласование:** два кодировщика страны (или третий компетентный человек) обсуждают каждое расхождение по цитатам-доказательствам и согласуют итоговый код. Сохраните `adjudicated.csv` со столбцами `vid, later_status, specificity_specific`.
4. Только теперь можно открывать `key_hidden.csv` (его читает скрипт).
5. Запуск: `python3 validation/compare_after_coding.py A.csv B.csv --adjudicated adjudicated.csv` (можно передать листы всех стран вместе). Результат: `results.md` и `corrected_codes.csv`.

### 7. Что сообщать
По странам (= языкам) и в целом: процент согласия и каппа Коэна между двумя кодировщиками и между согласованными кодами и моделью по (i) **full vs not-full**, (ii) **traced vs untraced**, (iii) конкретности (specific vs not), а также по 4 категориям исхода; таблицу сопряжённости; число сбоев поиска и `not_a_commitment`; медиану минут на строку. Соответствие меткам модели: full=fulfilled, partial=partial, ongoing=not_fulfilled, untraced=dropped.
**Пересчёт контраста KZ–PL с исправленными кодами:** сделайте копию `repo/data/promise_model_F5.csv` (оригинал не менять); для отобранных `promise_id` замените `verdict_final` согласованной меткой и согласованно обновите производные столбцы (`fulfilled`, `fulfilled_or_partial`, `dropped`); исключите `not_a_commitment`; направьте `analysis/final_analysis.R` на копию (путь в строке `read.csv`; в копии нужно снять проверку stopifnot на 183 строки и `verdict_version`) и сравните коэффициенты KZ–PL с опубликованными. Поскольку KZ и PL взяты целиком, а NL лишь стратифицированная подвыборка, результаты по NL служат только валидации.

> Maintenance warning (15 October 2026): do not run `compare_after_coding.py` on blank or unresolved sheets. Its legacy consensus and missingness handling requires revision before live comparison; it currently opens the hidden key even for empty input. Keep the key closed until two independent human rounds are frozen and the comparison code has been reviewed. The new `validation_first_report/` kit uses a different evidence window.
