#!/usr/bin/env python3
"""Recompute derived fields after editing data by hand.

Usage:
  python3 scripts/recalc.py            # games.json derived fields + library.json stats

games.json: plat_pct, est_100_hours, dlc_count, dlc_pending (from dlcs[].released == false).
library.json: games list, by_year and computed stats are rebuilt from data/library_raw.txt;
totals (profile header numbers) are kept as-is — update them by hand from the stratege profile.
"""
import collections, datetime, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TODAY = datetime.date.today().isoformat()


def recalc_games():
    path = DATA / "games.json"
    games = json.loads(path.read_text(encoding="utf-8"))
    ids = set()
    for g in games:
        assert g.get("id") and g["id"] not in ids, f"duplicate or missing id: {g.get('id')}"
        ids.add(g["id"])
        if g.get("section") == "unfinished":
            continue
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
    by_year = collections.OrderedDict()
    for x in sorted(done, key=lambda x: x["last"]):
        b = by_year.setdefault(x["last"][:4], {"year": x["last"][:4], "games": 0, "trophies": 0, "hours": 0})
        b["games"] += 1; b["trophies"] += x["got"]; b["hours"] += x["hours"] or 0
    for b in by_year.values():
        b["hours"] = round(b["hours"])
    diffs = [x["diff"] for x in done if x["diff"]]
    meta["games"] = lib
    meta["by_year"] = list(by_year.values())
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
