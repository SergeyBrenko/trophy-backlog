#!/usr/bin/env python3
"""Recompute derived fields after editing data by hand.

Usage:
  python3 scripts/recalc.py            # games.json derived fields + library.json stats

games.json: plat_pct, est_100_hours, dlc_count, dlc_pending (from dlcs[].released == false);
from data/stratege.json "stats" (fetch_stratege.py --stats): trophies, owners, plat_count, full_count, avg_completion,
avg_plat_hours, diff_base, dur_base, diff_dlc, dur_dlc;
from data/trophies.json and data/stratege.json: tro_split (base / DLC trophies by grade, offline vs online),
dlcs[].grades and dlcs[].trophies (by the stratege DLC group in dlcs[].group, matched by name if missing),
diff_base_votes, diff_dlc_votes.
Online = names in online_trophies (verified against guides; stratege's own online mark is unreliable); platinum stays offline.
library.json: games list and computed stats are rebuilt from data/library_raw.txt;
totals (profile header numbers) are kept as-is — scripts/sync_profile.py updates them.
"""
import collections, datetime, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TODAY = datetime.date.today().isoformat()


GRADE = {"platinum": "p", "gold": "g", "silver": "s", "bronze": "b"}
def words(t, skip=()):
    t = html.unescape(t or "").lower().replace("ё", "е")
    return {w for w in re.findall(r"\w+", t) if (len(w) > 2 or w.isdigit()) and w not in skip}


def tally(trophies, online):
    split = {"off": {}, "on": {}}
    for t in trophies:
        k = GRADE.get(t.get("grade"))
        if k:
            side = split["on" if t.get("name") in online and k != "p" else "off"]
            side[k] = side.get(k, 0) + 1
    return split


def trophy_split(g, lists, votes, unmatched):
    if votes:
        g["diff_base_votes"], g["diff_dlc_votes"] = votes
    if not lists:
        return
    online = {t["name"] for t in g.get("online_trophies") or []} if g.get("online") else set()
    groups = lists["dlcs"]
    g["tro_split"] = {"base": tally(lists["base"], online),
                      "dlc": tally([t for d in groups for t in d["trophies"]], online), "dlc_groups": len(groups)}
    by_name = {d["name"]: d for d in groups}
    used = set()
    # stratege group names often repeat the game title ("Atomic Heart: Trapped in Limbo"): compare the rest
    title = words(g.get("title"))
    flat = lambda t: " ".join(re.findall(r"\w+", html.unescape(t or "").lower().replace("ё", "е")))
    for d in g.get("dlcs") or []:
        if d.get("group") not in by_name:
            d.pop("group", None)
        if not d.get("group") and d.get("released") is not False:
            taken = {x.get("group") for x in g["dlcs"]}
            exact = [n for n in by_name if n not in taken and flat(n) == flat(d["name"])]
            score = {n: len(words(d["name"], title) & words(n, title)) for n in by_name if n not in taken}
            best = sorted(score.items(), key=lambda x: -x[1])
            if exact:
                d["group"] = exact[0]
            elif best and best[0][1] and (len(best) == 1 or best[0][1] > best[1][1]):
                d["group"] = best[0][0]
        grp = by_name.get(d.get("group"))
        if grp:
            d["grades"] = tally(grp["trophies"], online)
            d["trophies"] = sum(v for side in d["grades"].values() for v in side.values())
            used.add(grp["name"])
        else:
            d.pop("grades", None)
            if d.get("released") is not False:
                unmatched.append(f'{g["id"]}: DLC "{d["name"]}" без группы stratege')
    for n in by_name:
        if n not in used:
            unmatched.append(f'{g["id"]}: группа stratege "{n}" без DLC в карточке')


def recalc_games():
    path = DATA / "games.json"
    games = json.loads(path.read_text(encoding="utf-8"))
    lists = json.loads((DATA / "trophies.json").read_text(encoding="utf-8")) if (DATA / "trophies.json").exists() else {}
    facts = json.loads((DATA / "stratege.json").read_text(encoding="utf-8")) if (DATA / "stratege.json").exists() else {}
    unmatched = []
    ids = set()
    for g in games:
        assert g.get("id") and g["id"] not in ids, f"duplicate or missing id: {g.get('id')}"
        ids.add(g["id"])
        if g.get("section") in ("unfinished", "rejected"):
            continue
        m = re.search(r"/(ps[345]|psvita)/games/[^/?#]+", g.get("stratege_url") or "")
        if m:
            fact = facts.get(m.group(0), {})
            # stratege is the source of base stats: values from fetch_stratege.py --stats replace the card's
            for k, v in (fact.get("stats") or {}).items():
                if v is not None:
                    g[k] = v
            trophy_split(g, lists.get(m.group(0)), fact.get("votes"), unmatched)
        ow, pc = g.get("owners"), g.get("plat_count")
        g["plat_pct"] = round(100 * pc / ow, 1) if ow and pc is not None else None
        dlcs = g.get("dlcs") or []
        hours = [d.get("hours") for d in dlcs if d.get("released") is not False and d.get("hours")]
        p = g.get("avg_plat_hours")
        g["est_100_hours"] = p + sum(hours) if p else None
        g["dlc_count"] = len([d for d in dlcs if (d.get("trophies") or 0) > 0 or d.get("released") is False])
        if any(d.get("released") is False for d in dlcs):
            g["dlc_pending"] = True
    order = {"backlog": 0, "unfinished": 1, "candidate": 2, "rejected": 3}
    games.sort(key=lambda g: (order.get(g.get("section"), 9), g["title"].lower()))
    path.write_text(json.dumps(games, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for u in unmatched:
        print("DLC:", u)
    return games


def recalc_library():
    path = DATA / "library.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    lib = []
    for line in (DATA / "library_raw.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        p = line.split("|")
        got, tot = map(int, p[2].split("/"))
        d, m, y = p[5].split(".")
        lib.append(dict(title=p[0], platform=p[1], got=got, total=tot,
                        diff=None if p[3] == "—" else float(p[3]), dur=None if p[4] == "—" else p[4],
                        last=f"{y}-{m}-{d}", speed=None if p[6] == "—" else p[6],
                        url="https://stratege.ru" + p[7] + "/trophies",
                        hours=float(p[8]) if len(p) > 8 and p[8] else None, complete=got == tot))
    done = [x for x in lib if x["complete"]]
    diffs = [x["diff"] for x in done if x["diff"]]
    meta["games"] = lib
    meta["computed"] = dict(done_count=len(done), done_trophies=sum(x["got"] for x in done),
                            done_hours=round(sum(x["hours"] or 0 for x in done)),
                            avg_diff=round(sum(diffs) / len(diffs), 2) if diffs else None,
                            ps5=sum(1 for x in done if x["platform"] == "PS5"),
                            ps4=sum(1 for x in done if x["platform"] == "PS4"))
    meta["last_update"] = TODAY
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return meta


if __name__ == "__main__":
    g = recalc_games()
    m = recalc_library()
    c = collections.Counter(x.get("section") for x in g)
    print(f"games.json: {dict(c)}; library: {m['computed']}")
