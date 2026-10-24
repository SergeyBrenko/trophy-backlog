# Research brief: PS trophy-hunting game cards

The user (Russian-speaking, PSN/stratege nick DannyMadcat) 100%-completes PlayStation games
(platinum + every DLC trophy list). Plays from PHYSICAL DISC, buys DLC digitally (Turkey/Ukraine PS Store).
Comfortable difficulty on stratege.ru is up to 6/10; harder games are still added (the page colours difficulty red),
but say so in `why`/`trophy_summary`. Online trophies allowed but must be flagged.
PS5 preferred; PS4 games OK. If a game has separate PS4 and PS5 trophy lists, use the PS5 list.

## Tools
- Fetch pages with the WebFetch tool. stratege.ru works with it directly.
  If a site blocks fetching (PSNProfiles, sometimes Metacritic/PowerPyx), skip it and note it. stratege.ru rate-limits bursts (HTTP 429): pace requests.
- Use WebSearch to find URLs / facts.

## Sources per game (in this order)
1. stratege.ru trophies page: `https://stratege.ru/ps5/games/<slug>/trophies` (or /ps4/). Find slug via WebSearch `site:stratege.ru <title> трофеи` if guessing fails.
   Read: Трофеев (total), Основных, Из DLC, bronze/silver/gold/plat counts, "Игра есть у", "Получили платину", "Среднее завершение",
   "Среднее время платины", "Получили 100%", list of "Дополнения с трофеями".
   Per-DLC trophy counts: the trophies page has filter links "Показать DLC «...»" (…/trophies?nax=1&filter=N) — fetch each to count trophies, or use PSNProfiles/PlayStationTrophies.
2. stratege.ru difficulty page: `.../difficulty` → "Оценка основных трофеев" (difficulty X.XX, duration "NN+ часов", vote count) and "Оценка трофеев из DLC" (aggregate for all DLC).
   Skim player comments for recurring praise/complaints and trophy pain points.
3. A trophy guide roadmap (PowerPyx, Knoef, PlayStationTrophies.org, PSNProfiles guide): online trophies?, missable trophies?, min playthroughs,
   difficulty-related trophies, glitched trophies, per-DLC difficulty/time if available.
4. OpenCritic and/or Metacritic: critic score, Metacritic user score (or Steam % positive).
5. Russian localization — see below.
6. DLC status: which DLC with trophies are released, which are ANNOUNCED but not yet released (pending). Also: is there a physical
   disc edition that already includes DLC (GOTY/Complete/Deluxe)? The stratege game page (`/ps5/games/<slug>`, field "Тип") says whether a disc exists.

## Russian localization
Two fields: `ru` — one of `"voice"` (Russian voice-over; subtitles implied), `"subs"` (Russian text/subtitles only), `"none"`, or `null` if
it cannot be established; `ru_loc` — short Russian text shown in the details, e.g. "Озвучка и субтитры", "Субтитры", "Нет".
Sources, best first: PS Store product page for the PS4/PS5 version (audio vs screen languages), the publisher's site, Steam language table
(note "по данным Steam" in `ru_loc` if only Steam confirms it), stratege game page field "Язык" (it does NOT distinguish voice from text).
If Russian was removed from the console version after 2022, it is `"none"`.

## Quality score (1–10, one decimal)
quality = 0.6 * critic (OpenCritic top-critic avg or Metacritic, /10) + 0.4 * user score (Metacritic user /10, or Steam % /10),
then adjust by up to ±0.5 based on stratege comment sentiment and recent reviews. State the inputs in quality_note.

## Output: one JSON object per game, merged into data/games.json.
All human-readable text in RUSSIAN. Use null for unknown values — never invent numbers.
```json
{
  "id": "short_snake_slug",
  "title": "Official title",
  "platform": "PS5",               // trophy list used: PS5 | PS4
  "release": "2025-08-14",
  "genre": "Экшен-RPG",
  "developer": "…",
  "stratege_url": "https://stratege.ru/ps5/games/…/trophies",
  "trophies": {"total": 62, "base": 54, "dlc": 8, "plat": 1, "gold": 2, "silver": 12, "bronze": 47},
  "dlcs": [ {"name": "In Tanta We Trust", "trophies": 8, "released": true, "release_date": "2023-05-26", "difficulty": 3, "hours": 6,
             "note": "trophy pain points, ~6 ч", "about": "1–2 sentences: what the DLC is about", "free": false, "expected": null} ],  // expected: text deadline for unreleased DLC
  "dlc_pending": false,            // true if any trophy DLC is announced but not yet out
  "dlc_pending_note": null,
  "diff_base": 3.56, "diff_base_votes": 101, "dur_base": "50+",
  "diff_dlc": 2.89, "dur_dlc": "0+",
  "avg_plat_hours": 62,
  "owners": 4825, "plat_count": 1012, "full_count": 290, "avg_completion": 29,
  "critic": 63, "critic_src": "OpenCritic", "user_score": 4.9,
  "quality": 5.8, "quality_note": "OC 63, MC user 4.9, на stratege отзывы смешанные",
  "online": false, "online_note": null,
  "online_trophies": [],           // if online: [{"name": "…", "grade": "bronze", "part": "Основная игра", "note": "…", "got": null}]
  "missables": "Нет (глава-селект после финала)",
  "playthroughs": "1",
  "difficulty_trophy": "Нет",
  "glitched": "Нет известных",
  "ru": "subs", "ru_loc": "Субтитры",
  "disc_note": "Диск PS5; DLC отдельно",
  "pros": ["…", "…", "…"],
  "cons": ["…", "…"],
  "trophy_summary": "1-2 предложения: что самое нудное/сложное в платине и DLC",
  "sources": [{"name": "Stratege", "url": "…"}, {"name": "PowerPyx", "url": "…"}]
}
```
Keep pros/cons to 2–4 short bullets each (≤ 12 words each). Be efficient: don't over-fetch.

Covers are not part of the card: after the cards are merged into data/games.json, run `python3 scripts/fetch_stratege.py`.
It finds the trophy-list icon by `stratege_url`, so `stratege_url` must point to the exact trophy list used.
