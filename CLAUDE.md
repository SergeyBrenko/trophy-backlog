# Трофейный бэклог — контекст для Claude Code

Статическое веб-приложение (GitHub Pages) со списком PlayStation-игр, которые владелец планирует пройти на 100% трофеев.
Страница только для просмотра: на ней нет кнопок и форм, меняющих данные. Все данные меняешь ты через репозиторий.
Ты ведёшь данные: собираешь информацию об играх, актуализируешь список раз в 1–2 месяца, предлагаешь новые игры, коммитишь и пушишь.
Общайся с владельцем по-русски. Весь видимый текст в данных тоже на русском. Не стесняйся задавать вопросы и предлагать улучшения.

## Владелец и его правила
- Ник на stratege.ru и в PSN: **DannyMadcat**. Профиль: https://stratege.ru/playstation/users/dannymadcat
- Цель в каждой игре: платина + 100% всех DLC с трофеями.
- Играет с **физического диска**, DLC докупает цифрой (PS Store Турция или Украина). Игры без диска помечать (`disc_note`).
- Комфортная сложность — до 6.0 по stratege (основная игра и DLC). Сложные игры тоже добавляются в кандидаты: страница подсвечивает сложность цветом (красная — выше 6). В `why`/`trophy_summary` прямо пиши, что делает платину сложной.
- Онлайн-трофеи допустимы, но всегда `online: true` + пояснение в `online_note` + список `online_trophies`: по нему плитки трофеев делятся на офлайн и онлайн.
- Наличие русского языка важно: у каждой игры должно быть поле `ru` (см. ниже), неизвестное ищи по источникам из `docs/research-brief.md`.
- Платформы: PS5 и PS4. Если у игры отдельные списки PS4/PS5 — бери PS5.
- Скучные игры (как Forspoken) по умолчанию не предлагать, но держать в списке не запрещено.
- **Новые игры не добавлять в основной список самостоятельно.** Сначала они попадают в кандидаты (`section: "candidate"`), владелец решает. Перед массовым добавлением покажи ему сводку в чате.
- Игры, которые владелец точно не будет проходить, — `section: "rejected"`. На странице они нигде не показываются; не удалять и не предлагать снова.
- Никогда не выдумывай цифры: неизвестное — `null`.

## Структура
```
index.html                 приложение (один файл, без сборки; читает data/*.json)
data/games.json            все игры: список, кандидаты, недоделанные, «не буду» (rejected)
data/library.json          профиль: итоги, аватар, пройденные игры
data/library_raw.txt       выгрузка профиля stratege (источник для library.json)
data/covers.json           путь stratege (/ps5/games/<slug>) → img/covers/<платформа>_<slug>.jpg
data/stratege.json         путь stratege → {type, lang, votes}: тип издания и язык (подсказка при проверке диска и русского), голоса за сложность
data/trophies.json         путь stratege → списки трофеев основной игры и каждой группы DLC со stratege (имя, тип кубка, пометка онлайн)
img/avatar.png             аватар PSN владельца
img/covers/                обложки: иконки трофейных листов PSN, квадрат 256×256 JPEG
scripts/sync_profile.py    выгружает профиль stratege без браузера → library_raw.txt + library.json → totals, synced
scripts/fetch_stratege.py  докачивает аватар, обложки, тип издания/язык, голоса и списки трофеев (нужен Pillow; --trophies — перечитать трофеи и голоса, --force — всё заново)
scripts/recalc.py          пересчёт производных полей games.json и статистики library.json
mockups/                   (создаётся по необходимости) временные макеты интерфейса на согласование; после решения удалять
docs/research-brief.md     как собирать карточку игры: источники, русский язык, формула оценки, схема JSON (на английском)
```
Локальный просмотр: `python3 -m http.server 8000` в корне → http://localhost:8000 (через file:// fetch не работает).

## Данные: data/games.json
Массив объектов. Ключевые поля:
- `id` — уникальный slug; у недоделанных префикс `u_`.
- `section`: `backlog` (основной список) · `candidate` (предложено, ждёт решения) · `unfinished` (игры из профиля не на 100%) · `rejected` (точно не буду).
- `status`: `planned` · `playing` · `paused` · `done`. Плюс поля владельца `priority` (1–3|null), `my_rating` (1–10|null), `notes`: на странице показываются в раскрытой карточке, если заполнены.
- `cand_group` у кандидатов: «Новинки», «Пропущенное», «По вашей просьбе», «Тактика и RPG», «Сюжетные AA», «Эксклюзивы Sony» (группы в фильтре строятся автоматически).
- `online_trophies`: `[{name, grade: "platinum|gold|silver|bronze", part: "Основная игра" | название DLC, note, got}]` — имена как на stratege, по ним `recalc.py` отделяет онлайн-трофеи; `got` (true/false) — только у `unfinished`, иначе `null`. Пометка «онлайн» у трофея на stratege бывает неверной: сверяй с гайдом.
- `ru`: `"voice"` (озвучка, зелёный) · `"subs"` (только текст, оранжевый) · `"none"` (нет, красный) · `null` (не установлено, серый «русский?»); `ru_loc` — подробности текстом.
- Карточка игры — полная схема в `docs/research-brief.md`: `trophies{total,base,dlc,plat,gold,silver,bronze}`, `dlcs[]` (`released:false` = ещё не вышло), `dlc_pending`, `diff_base`, `diff_dlc`, `dur_base`, `avg_plat_hours`, `owners`, `plat_count`, `full_count`, `critic`, `user_score`, `quality`, `quality_note`, `online`, `missables`, `playthroughs`, `difficulty_trophy`, `glitched`, `ru`, `ru_loc`, `disc_note`, `pros[]`, `cons[]`, `trophy_summary`, `why` (для кандидатов), `sources[]`.
- У DLC в `dlcs[]` кроме цифр и `note`: `about` (о чём дополнение, 1–2 предложения), `free` (ничего не стоит сверх издания, по которому играет владелец: бесплатное обновление или уже входит в издание — Complete/Definitive/GOTY), `expected` (срок для невышедших, текстом), `group` (точное имя группы DLC на stratege; `recalc.py` подбирает его сам по названию и пишет о несовпадениях — тогда поправь руками).
- Производные (не править руками, их считает `scripts/recalc.py`): `plat_pct`, `est_100_hours`, `dlc_count`, `tro_split` (плитки трофеев: основная игра и DLC, по типам, офлайн/онлайн), `dlcs[].grades` и `dlcs[].trophies` (из списка stratege), `diff_base_votes`, `diff_dlc_votes`.
- Недоделанные (`unfinished`) имеют свою схему: `got`, `total`, `plat_done`, `missing[{part,trophies,note}]`, `diff_dlc`, `online`, `online_note`, `est_hours`, `feasible` ("да"|"сложно"|"нет"), `summary`, плюс `ru`/`ru_loc`.

Оценка качества `quality` (1–10): 0.6 × оценка критиков (OpenCritic/Metacritic, /10) + 0.4 × оценка игроков (Metacritic user /10 или Steam %/10), поправка до ±0.5 по отзывам на stratege и свежим отзывам. Входные данные — в `quality_note`.

## Правки владельца
Владелец пишет правки в чат («Atomic Heart начал», «Dispatch в список», «Persona 5 не хочу»). Меняй соответствующие поля в `data/games.json`: `status`, `priority`, `my_rating`, `notes`, а `section` — `backlog` при одобрении кандидата, `rejected` при отказе. Затем `recalc.py`, commit, push.

## Обложки и аватар
Страница ищет обложку по пути stratege из `stratege_url` (у игр) или `url` (у пройденных) в `data/covers.json`. Отдельного поля в карточке нет. Если обложки нет, показываются инициалы.
После добавления новых игр или синхронизации профиля запусти `python3 scripts/fetch_stratege.py`: он докачает только недостающее (пауза 2 с между запросами, при 429 ждёт и повторяет).

## Процедура «актуализируй»
0. **Спроси владельца**, что делать в этот раз: (а) только обновить данные — профиль, статистику, DLC, оценки, хвалят/ругают по свежим отзывам; или (б) то же плюс поискать новые игры, вышедшие с прошлой актуализации (`library.json → last_update`).
1. **Профиль:** `python3 scripts/sync_profile.py`. Stratege — единственный источник прогресса владельца. Скрипт сам проверяет, что разобрал столько игр, сколько в профиле.
2. **Сверка с профилем:** игры из `backlog`, которые стали 100% → `status: "done"`; начатые → `playing` + `progress: "x/y"`. Обнови секцию `unfinished`: доделанное убрать, новые неполные добавить.
3. **Обновление карточек** `backlog`, `candidate`, `unfinished` (не `rejected`). Stratege — один из источников, не единственный:

   | Что | Откуда |
   |---|---|
   | трофеи, листы DLC, владельцы/платины/100%, среднее время платины, сложность | stratege (других источников этих цифр нет) |
   | вышли ли ожидаемые DLC, анонсы новых, даты | stratege «Дополнения с трофеями» + PlayStation Blog, сайт/соцсети издателя, PS Store |
   | издание на диске (в т.ч. GOTY/Complete с DLC) | stratege «Тип» в `data/stratege.json` + новости издателя, ритейл |
   | русский язык (`ru`, `ru_loc`) | PS Store, сайт издателя, Steam, stratege «Язык» |
   | `critic`, `user_score`, `quality` | OpenCritic, Metacritic, Steam (недавние отзывы) |
   | `pros`, `cons`, `trophy_summary`, `glitched`, `missables` | комментарии stratege, свежие отзывы игроков, патчноуты, трофейные гайды (PowerPyx, PSNProfiles, PlayStationTrophies) — патчи чинят баги и меняют трофеи |

   Большой объём делай параллельными агентами по группам игр, каждый пишет результат во временный файл, сливаешь сам и проверяешь схему.
4. **Новые кандидаты** (только при варианте «б» и по прямой просьбе): заметные релизы за период; сложные тоже. Исключай всё из `library_raw.txt` и `games.json` (включая `rejected`). Полная карточка по `docs/research-brief.md`, `section: "candidate"`, заполни `why`.
5. `python3 scripts/fetch_stratege.py --trophies` (новые DLC, голоса за сложность), затем `python3 scripts/recalc.py` — проверь его вывод «DLC: …» о несовпадениях групп.
6. Покажи владельцу сводку (что пройдено, что изменилось, новые кандидаты с ключевыми цифрами), обнови «Известные пробелы данных» ниже, затем commit, push и ссылка на сайт.

Подсказки по stratege:
- Трофеи: `https://stratege.ru/ps5/games/<slug>/trophies` (поля «Трофеев», «Основных», «Из DLC», «Игра есть у», «Получили платину», «Среднее время платины», «Получили 100%», «Дополнения с трофеями»).
- Сложность: `.../difficulty` («Оценка основных трофеев», «Оценка трофеев из DLC» — одна общая на все DLC). Комментарии на странице грузятся скриптом: WebFetch и curl их не видят.
- Страница игры `.../games/<slug>`: «Тип» (диск / цифровая версия), «Язык» (не различает озвучку и субтитры).
- Трофеи отдельного DLC: фильтр на странице трофеев `?nax=1&filter=N` («Показать DLC «…»»).
- Сам список трофеев страница грузит POST-запросом `https://stratege.ru/ajax_loader/trophies_sp_list` (`ajax_mode=trophies_list_loader`, `settings` и `players` из JS-объекта `tl_global_bx_settings` на странице, `filter`, `sort=0`, `helps=0`, `guest=1`, `shag=0`). У трофея: класс `tltstpl_border_<grade>_trophies`, иконка `trophies_icon/online.png` или `offline.png`.
- Чего не хватает владельцу в игре: `.../trophies?nax=1&filter=101&show_user=dannymadcat`.
- Профиль: POST `https://stratege.ru/ajax_loader/users_profile_fw` с `ajax_mode=profile_all_loader&action=all_page&firmware=1&uid=134267&sort=0&type=current&compare=&page=0` (`type=time` — время в играх). Им пользуются `sync_profile.py` и `fetch_stratege.py`.
- Иконка трофейного листа: `https://static.stratege.ru/trophies/<NPWR…>/ICON0.PNG` (PS5 512×512, PS4 320×176).
- Сайт режет частые запросы (429) — делай паузы.

## Git и деплой
- Репозиторий: https://github.com/SergeyBrenko/trophy-backlog (публичный). Сайт: https://sergeybrenko.github.io/trophy-backlog/ (GitHub Pages из `main`, корень; `.nojekyll` на месте).
- После любых изменений: commit → push → дождаться сборки Pages (`gh api repos/SergeyBrenko/trophy-backlog/pages/builds/latest --jq .status` = `built`) → дать владельцу ссылку на сайт.
- Сообщения коммитов только на русском, небольшие и осмысленные: «Актуализация 2026-12: …», «Кандидаты: + …», «Интерфейс: …». История изменений — это git log, отдельного журнала нет.
- Контекстные файлы (`CLAUDE.md`, `README.md`, `docs/research-brief.md`) обновлять в том же коммите, что и изменение. Устаревшее удалять: здесь должна быть только актуальная информация.

## Известные пробелы данных (на 2026-10-24)
- S.T.A.L.K.E.R. 2 — карточка предварительная: нет оценок критиков, пропускаемых трофеев, наличия диска.
- Мафии: у Mafia II DE пока нет PS5-листа (появится — перейти на него); статистика PS5-листа Mafia III (вышел 08.10.2026) на малой выборке, на PS4 платина в среднем 84 ч. Диски только PS4 (Mafia: Trilogy / отдельные), PS5-версии через бесплатный апгрейд.
- Распределение трофеев по DLC у части игр выведено вычитанием из общего числа.
- В `quality` у кандидатов, добавленных 2026-10-24, нет поправки по комментариям stratege (они грузятся скриптом), кроме групп «Тактика и RPG» и запасных.
- Мало голосов за сложность, оценка может сдвинуться: The Blood of Dawnwalker, Avowed, Disciples: Domination, Star Wars Zero Company, King Arthur, Romeo is a Dead Man, GreedFall II, Pathfinder (2 голоса), DLC Dying Light: The Beast (2 голоса). Нет оценки: Days Gone Remastered (в карточке цифры PS4-оригинала), DLC Rogue Trader, Atomfall, Little Nightmares III, King Arthur.
- Диска нет или он не подтверждён: Outer Worlds: Spacer's Choice (только PS4-диск + платный апгрейд), Avowed, South of Midnight, Sherlock Holmes: Chapter One (только азиатское издание), King's Bounty II и Divinity: OS2 (PS5 через PS4-диск), Pathfinder: WotR, King Arthur, Romeo is a Dead Man, Days Gone Remastered, Hellblade II (анонсирован LRG), The Alters (Complete Edition выходит 20.11.2026), Dying Light: The Beast (Definitive, декабрь 2026).
- Русский язык: у Assassin's Creed Unity зависит от региона копии (`ru: null`), у Dying Light: The Beast PS Store пишет «субтитры», а Steam и пресса — озвучка. Hellblade (PS4): русский текст есть только в европейской версии.
- `plat_speed` в `library_raw.txt` из профиля больше не приходит: у старых игр сохранён, у новых «—» (на странице не используется).
