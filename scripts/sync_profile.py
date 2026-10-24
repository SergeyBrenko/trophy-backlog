#!/usr/bin/env python3
"""Sync the owner's stratege.ru profile without a browser.

Usage:
  python3 scripts/sync_profile.py      # then: python3 scripts/recalc.py

Reads the profile AJAX endpoint (game collection + time in game), rewrites data/library_raw.txt and
updates library.json -> totals and synced. Line format of library_raw.txt:
  title|platform|got/total|stratege_diff|stratege_dur|last_trophy|plat_speed|stratege_path|hours_played
plat_speed is not in the AJAX response: the previous value for the same game is kept, otherwise "—".
"""
import datetime, html as htmllib, json, pathlib, re, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PROFILE = "https://stratege.ru/playstation/users/dannymadcat"
PROFILE_UID = 134267


def profile(kind):
    q = dict(ajax_mode="profile_all_loader", action="all_page", firmware=1, uid=PROFILE_UID,
             sort=0, type=kind, compare="", page=0)
    req = urllib.request.Request("https://stratege.ru/ajax_loader/users_profile_fw", data=urllib.parse.urlencode(q).encode(),
                                 headers={"User-Agent": UA, "Referer": PROFILE, "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def rows(h, header):
    """Rows of the table whose header contains `header`: (cells, first /psN/games/<slug> link)."""
    t = h[h.rfind("<table", 0, h.find(header)):]
    t = t[t.find("</thead>"):]
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        cells = [htmllib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c))).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        link = re.search(r'href="(/ps[345]/games/[^/"?]+)', r)
        if link and len(cells) >= 6:
            out.append((cells, link.group(1)))
    return out


def hours(s):
    n = re.match(r"[\d\s]+", s or "")
    if not n or not n.group().strip():
        return ""
    v = int(n.group().replace(" ", ""))
    return round(v / 60, 1) if "мин" in s else 0 if "сек" in s else v


def main():
    cur, tim = profile("current"), profile("time")
    old_speed = {}
    raw_path = DATA / "library_raw.txt"
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        p = line.split("|")
        if len(p) > 7 and not line.startswith("#"):
            old_speed[p[7]] = p[6]

    played = {path: hours(c[4]) for c, path in rows(tim, "Время в игре")}
    lines = []
    for c, path in rows(cur, "Прогресс"):
        title = re.sub(r"\s*\((Европа|Весь мир|Оригинал|Трофеи)\)$", "", c[0]).strip().replace("’", "'")
        if not re.fullmatch(r"\d+/\d+", c[3]):
            continue
        lines.append("|".join([title, c[2], c[3], c[4] or "—", c[5] or "—", c[1], old_speed.get(path, "—"), path, str(played.get(path, ""))]))

    text = re.sub(r"<[^>]+>", " ", cur)
    num = lambda pat: (m := re.search(pat, text)) and int(re.sub(r"\D", "", m.group(1)))
    count = lambda cls: int(re.sub(r"\D", "", re.search(rf'{cls}">([\d\s]+)<', cur).group(1)))
    totals = dict(plat=count("pupfscd_platinum_value"), gold=count("pupfscd_gold_value"), silver=count("pupfscd_silver_value"),
                  bronze=count("pupfscd_bronze_value"), trophies=count("pupfscd_trops_value_total"),
                  games=num(r"Всего игр\s*([\d\s]+)"), complete100=num(r"Пройдено на 100%\s*([\d\s]+)"),
                  completion_pct=num(r"Общее завершение\s*([\d\s]+)%"), hours_profile=num(r"Время в играх\s*([\d\s]+)"))
    if totals["games"] and len(lines) != totals["games"]:
        raise SystemExit(f"parsed {len(lines)} games, profile says {totals['games']}: markup changed? library_raw.txt not touched")

    today = datetime.date.today().isoformat()
    raw_path.write_text(f"# Stratege profile DannyMadcat, synced {today} by scripts/sync_profile.py. "
                        "Format: title|platform|got/total|stratege_diff|stratege_dur|last_trophy|plat_speed|stratege_path|hours_played\n"
                        + "\n".join(lines) + "\n", encoding="utf-8")
    lib_path = DATA / "library.json"
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    lib["totals"] = {k: v if v is not None else lib.get("totals", {}).get(k) for k, v in totals.items()}
    lib["synced"] = today
    lib_path.write_text(json.dumps(lib, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(lines)} games; totals: {lib['totals']}")


if __name__ == "__main__":
    main()
