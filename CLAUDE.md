# Трофейный бэклог — контекст для Claude Code

Статическое веб-приложение (GitHub Pages) со списком PlayStation-игр, которые владелец планирует пройти на 100% трофеев.
Страница только для просмотра: на ней нет кнопок и форм, меняющих данные. Все данные меняешь ты через репозиторий.
Ты ведёшь данные: собираешь информацию об играх, актуализируешь список раз в 1–2 месяца, предлагаешь новые игры, коммитишь и пушишь.
Общайся с владельцем по-русски. Весь видимый текст в данных тоже на русском.

## Владелец и его правила
- Ник на stratege.ru и в PSN: **DannyMadcat**. Профиль: https://stratege.ru/playstation/users/dannymadcat
- Цель в каждой игре: платина + 100% всех DLC с трофеями.
- Играет с **физического диска**, DLC докупает цифрой (PS Store Турция или Украина). Игры без диска помечать (`disc_note`).
- Порог сложности: **не выше 6.0** по stratege (основная игра и DLC). Выше 6 — не предлагать или явно пометить.
- Онлайн-трофеи допустимы, но всегда `online: true` + пояснение в `online_note`.
- Платформы: PS5 и PS4. Если у игры отдельные списки PS4/PS5 — бери PS5.
- Скучные игры (как Forspoken) по умолчанию не предлагать, но держать в списке не запрещено.
- **Новые игры не добавлять в основной список самостоятельно.** Сначала они попадают в кандидаты (`section: "candidate"`), владелец решает. Перед массовым добавлением покажи ему сводку в чате.
- Никогда не выдумывай цифры: неизвестное — `null`.

## Структура
```
index.html                       приложение (один файл, без сборки; читает data/*.json)
data/games.json                  все игры: список, кандидаты, недоделанные, отклонённые
data/library.json                профиль: итоги, пройденные игры, статистика по годам, журнал обновлений
data/library_raw.txt             сырая выгрузка профиля stratege (источник для library.json)
data/covers.json                 карта обложек: путь stratege (/ps5/games/<slug>) → img/covers/<платформа>_<slug>.jpg
img/avatar.png                   аватар PSN владельца (путь в library.json → avatar)
img/covers/                      обложки игр: иконки трофейных листов PSN, квадрат 256×256 JPEG
scripts/fetch_images.py          скачивает аватар и недостающие обложки со stratege (нужен Pillow; --force перекачать всё)
scripts/recalc.py                пересчёт производных полей + статистики; --changelog "текст" добавляет запись в журнал
scripts/stratege_profile_snippet.js  скрипт для консоли браузера: выгружает профиль stratege в формат library_raw.txt
docs/research-brief.md           как собирать карточку игры: источники, формула оценки, схема JSON (на английском)
```
Локальный просмотр: `python3 -m http.server 8000` в корне → http://localhost:8000 (через file:// fetch не работает).

## Данные: data/games.json
Массив объектов. Ключевые поля:
- `id` — уникальный slug; у недоделанных префикс `u_`.
- `section`: `backlog` (основной список) · `candidate` (предложено, ждёт решения) · `unfinished` (игры из профиля не на 100%) · `rejected` (владелец отказался — **не удалять и не предлагать снова**).
- `status`: `planned` · `playing` · `paused` · `done` · `skip`. Плюс поля владельца `priority` (1–3|null), `my_rating` (1–10|null), `notes`: на странице показываются в раскрытой карточке, если заполнены.
- `cand_group` у кандидатов: «Новинки», «Пропущенное», «По вашей просьбе» и т.п. (группы в фильтре строятся автоматически).
- Карточка игры — полная схема в `docs/research-brief.md`: `trophies{total,base,dlc,plat,gold,silver,bronze}`, `dlcs[]` (`released:false` = ещё не вышло), `dlc_pending`, `diff_base`, `diff_dlc`, `dur_base`, `avg_plat_hours`, `owners`, `plat_count`, `full_count`, `hltb{main,extra,complete}`, `critic`, `user_score`, `quality`, `quality_note`, `online`, `missables`, `playthroughs`, `difficulty_trophy`, `glitched`, `ru_loc`, `disc_note`, `pros[]`, `cons[]`, `trophy_summary`, `why` (для кандидатов), `sources[]`.
- Производные (не править руками, их считает `scripts/recalc.py`): `plat_pct`, `est_100_hours`, `dlc_count`.
- Недоделанные (`unfinished`) имеют свою схему: `got`, `total`, `plat_done`, `missing[{part,trophies,note}]`, `diff_dlc`, `online`, `online_note`, `est_hours`, `feasible` ("да"|"сложно"|"нет"), `summary`.

Оценка качества `quality` (1–10): 0.6 × оценка критиков (OpenCritic/Metacritic, /10) + 0.4 × оценка игроков (Metacritic user /10 или Steam %/10), поправка до ±0.5 по отзывам на stratege. Входные данные — в `quality_note`.

## Правки владельца
Владелец пишет правки в чат («Atomic Heart начал», «Dispatch в список», «Persona 5 не хочу»). Меняй соответствующие поля в `data/games.json`: `status`, `priority`, `my_rating`, `notes`, а у кандидатов `section` (`backlog` при одобрении, `rejected` при отказе). Затем `recalc.py`, commit, push.

## Обложки и аватар
Обложка ищется страницей по пути stratege из `stratege_url` (у игр) или `url` (у пройденных) в `data/covers.json`. Отдельного поля в карточке нет. Если обложки нет, на странице показываются инициалы.
После добавления новых игр запусти `python3 scripts/fetch_images.py`: он докачает только недостающее (пауза 2 с между запросами, при 429 ждёт и повторяет).

## Процедура «актуализируй»
1. **Профиль.** Список игр на stratege грузится скриптом, WebFetch его не видит. Попроси владельца выполнить `scripts/stratege_profile_snippet.js` в консоли браузера на странице профиля и вставить результат → перезапиши `data/library_raw.txt`. Цифры шапки (платины/золото/серебро/бронза, всего игр, на 100%, часы) обнови в `library.json → totals`. Если в браузере доступен MCP-инструмент — можешь сделать это сам.
2. **Сверка с профилем:** игры из `backlog`, которые стали 100% → `status: "done"`; начатые → `playing` + `progress: "x/y"`. Обнови секцию `unfinished` (что доделано — убрать, новые неполные — добавить).
3. **Обновление карточек** `backlog` и `candidate`: заново сними со stratege трофеи (вышли ли новые DLC — у них растёт «Из DLC»), сложность, среднее время платины, владельцев/платины/100%. Проверь, вышли ли ожидаемые DLC (`released:false`), не анонсированы ли новые.
4. **Новые кандидаты:** громкие релизы с прошлой актуализации + по просьбе владельца. Исключай всё из `library_raw.txt`, `games.json` (включая `rejected`). Собирай полную карточку по `docs/research-brief.md`, `section: "candidate"`, заполни `why`.
5. `python3 scripts/fetch_images.py` (обложки новых игр и пройденных), затем `python3 scripts/recalc.py --changelog "Кратко: что изменилось"`.
6. Покажи владельцу сводку (что пройдено, что изменилось, новые кандидаты с ключевыми цифрами), затем commit, push и ссылка на сайт.

Подсказки по stratege:
- Трофеи: `https://stratege.ru/ps5/games/<slug>/trophies` (поля «Трофеев», «Основных», «Из DLC», «Игра есть у», «Получили платину», «Среднее время платины», «Получили 100%», «Дополнения с трофеями»).
- Сложность: `.../difficulty` («Оценка основных трофеев», «Оценка трофеев из DLC» — одна общая на все DLC).
- Трофеи отдельного DLC: фильтр на странице трофеев `?nax=1&filter=N` («Показать DLC «…»»).
- Чего не хватает владельцу в игре: `.../trophies?nax=1&filter=101&show_user=dannymadcat`.
- Профиль без браузера: POST `https://stratege.ru/ajax_loader/users_profile_fw` с `ajax_mode=profile_all_loader&action=all_page&firmware=1&uid=134267&sort=0&type=current&compare=&page=0` отдаёт HTML профиля: аватар, счётчики трофеев, все игры. Из него `fetch_images.py` берёт аватар и ID трофейных листов (`NPWR…`).
- Иконка трофейного листа: `https://static.stratege.ru/trophies/<NPWR…>/ICON0.PNG` (PS5 512×512, PS4 320×176).
- Сайт режет частые запросы (429) — делай паузы.

## Git и деплой
- Репозиторий: https://github.com/SergeyBrenko/trophy-backlog (публичный). Сайт: https://sergeybrenko.github.io/trophy-backlog/ (GitHub Pages из `main`, корень; `.nojekyll` на месте).
- После любых изменений: commit → push → дождаться сборки Pages (`gh api repos/SergeyBrenko/trophy-backlog/pages/builds/latest --jq .status` = `built`) → дать владельцу ссылку на сайт.
- Сообщения коммитов только на русском, небольшие и осмысленные: «Актуализация 2026-12: …», «Кандидаты: + …», «Интерфейс: …».
- Контекстные файлы (`CLAUDE.md`, `README.md`, `docs/research-brief.md`) обновлять в том же коммите, что и изменение. Устаревшее удалять: здесь должна быть только актуальная информация.

## Известные пробелы данных (на 2026-10-24)
- HowLongToBeat почти везде `null` (сайт блокирует автоматическое чтение).
- S.T.A.L.K.E.R. 2 — карточка предварительная: нет оценок критиков, пропускаемых трофеев, наличия диска.
- Outer Worlds: Spacer's Choice — диска для PS5 нет (только PS4-диск + платный апгрейд).
- Mafia: Definitive Edition — версия для PS5 и наличие диска не проверены.
- Распределение трофеев по DLC у части игр выведено вычитанием из общего числа.
- Кандидаты из групп «Сюжетные AA» и «Эксклюзивы Sony»: в `quality` нет поправки по отзывам stratege (комментарии грузятся скриптом).
- Мало голосов за сложность на stratege, оценка может сдвинуться: The Blood of Dawnwalker (6), Avowed (8), Disciples: Domination (3), Star Wars Zero Company (2). У DLC Rogue Trader и Atomfall оценки сложности ещё нет.
- Диск не подтверждён или его нет: Avowed, South of Midnight, The Sinking City (PS5), Sherlock Holmes: Chapter One (только азиатское издание), King's Bounty II (PS5 — через PS4-диск с апгрейдом), The Alters (диск Complete Edition выходит 20.11.2026).
