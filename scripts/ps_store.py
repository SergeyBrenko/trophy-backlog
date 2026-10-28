#!/usr/bin/env python3
"""PS Store links of Ukraine (ru-ua) and Turkey (en-tr) for games.json -> store.

Usage:
  python3 scripts/ps_store.py search "Resident Evil 3"   # products in both regions: id, type, platforms, prices
  python3 scripts/ps_store.py concept EP0102-PPSA03953_00-BH3ROFF000000001   # concept id of a product
  python3 scripts/ps_store.py check                      # every store link opens and is for sale in its region

games.json -> store: {"game": {"ua": "concept/<id>", "tr": "concept/<id>"},
                      "dlc": [{"name": "…", "ua": "product/<id>", "tr": "product/<id>"}]}
A region is left out when the product is not sold there. Game links use the concept (all editions on one page),
DLC links the product. Search goes through the store's GraphQL API with a persisted query: if it starts failing,
open store.playstation.com/en-tr/search/<anything> with DevTools -> Network, find operationName=getSearchResults
and copy the new sha256Hash into SEARCH_HASH.
"""
import json, pathlib, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
SEARCH_HASH = "4df6284f982e57bec70f23c77e2c219dc792eb19af7fb3d3a81767aa3f1958aa"
REGIONS = {"ua": "ru-ua", "tr": "en-tr"}
NOT_FOR_SALE = {"Недоступно", "Unavailable"}


def search(loc, term):
    lang, cc = loc.split("-")
    var = {"countryCode": cc.upper(), "languageCode": lang, "nextCursor": "", "pageOffset": 0, "pageSize": 24, "searchTerm": term}
    url = "https://web.np.playstation.com/api/graphql/v1/op?" + urllib.parse.urlencode(
        {"operationName": "getSearchResults", "variables": json.dumps(var),
         "extensions": json.dumps({"persistedQuery": {"version": 1, "sha256Hash": SEARCH_HASH}})})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "x-psn-store-locale-override": f"{lang}-{cc.upper()}",
                                               "content-type": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    return [x for x in data["data"]["universalSearch"]["results"] if x.get("__typename") == "Product"]


def page(loc, path):
    try:
        return urllib.request.urlopen(urllib.request.Request(f"https://store.playstation.com/{loc}/{path}",
                                                             headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "replace")
    except urllib.error.HTTPError:
        return ""


def price(h):
    m = re.search(r'"basePrice":"([^"]*)"', h)
    return m and m.group(1)


def cmd_search(term):
    found = {}
    for k, loc in REGIONS.items():
        for x in search(loc, term):
            row = found.setdefault(x["id"], {"name": x["name"], "type": x.get("storeDisplayClassification"),
                                             "platforms": "/".join(x.get("platforms") or [])})
            row[k] = (x.get("price") or {}).get("basePrice")
        time.sleep(0.5)
    for pid, r in found.items():
        print(f'{pid} | {r["name"]} | {r["type"]} | {r["platforms"]} | UA {r.get("ua", "—")} | TR {r.get("tr", "—")}')


def cmd_check():
    games = json.loads((ROOT / "data" / "games.json").read_text(encoding="utf-8"))
    jobs = [(g["id"], e.get("name", "игра"), k, e[k]) for g in games if g.get("section") != "rejected"
            for e in [g.get("store", {}).get("game") or {}] + g.get("store", {}).get("dlc", []) for k in REGIONS if e.get(k)]

    def one(job):
        h = page(REGIONS[job[2]], job[3])
        return job, price(h) if h else "404"
    with ThreadPoolExecutor(6) as ex:
        bad = [(j, p) for j, p in ex.map(one, jobs) if p in NOT_FOR_SALE or p in (None, "404")]
    print(f"{len(jobs)} links checked, problems: {len(bad)}")
    for (gid, name, k, path), p in bad:
        print(f"  {gid}: {name} ({k}) {path}: {p}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        cmd_search(" ".join(sys.argv[2:]))
    elif len(sys.argv) == 3 and sys.argv[1] == "concept":
        m = re.search(r"Concept:(\d+)", page("en-tr", f"product/{sys.argv[2]}"))
        print(m.group(1) if m else "concept not found")
    elif sys.argv[1:] == ["check"]:
        cmd_check()
    else:
        print(__doc__)
