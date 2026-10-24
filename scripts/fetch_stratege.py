#!/usr/bin/env python3
"""Collect per-game data from stratege.ru that is not part of the research cards.

Usage:
  python3 scripts/fetch_stratege.py            # only what is missing
  python3 scripts/fetch_stratege.py --force    # re-download everything
  python3 scripts/fetch_stratege.py --trophies # re-read trophy lists only (new DLC after an update)

- Avatar: stratege profile AJAX -> img/avatar.png, path saved to library.json "avatar".
- Covers: trophy-list icon (ICON0) of every game in games.json and library.json, cropped to a square
  256x256 JPEG -> img/covers/<platform>_<slug>.jpg; map {"/ps5/games/<slug>": "img/covers/..."} in data/covers.json.
- Game page facts: release type (disc/digital) and language from /<platform>/games/<slug>, difficulty vote counts
  (base, DLC) from .../difficulty -> data/stratege.json {"/ps5/games/<slug>": {"type", "lang", "votes": [base, dlc]}}.
  type/lang are a hint when checking discs and Russian; recalc.py copies votes into games.json.
- Trophy lists of games in games.json (not rejected): base game and every DLC group as stratege shows them,
  each trophy {name, grade, online} -> data/trophies.json {"/ps5/games/<slug>": {"base": [...], "dlcs": [{"name", "trophies"}]}}.
  stratege's online mark is often wrong; recalc.py corrects it with the verified games.json -> online_trophies.
index.html looks covers up by the stratege path. Requires Pillow.
"""
import html, io, json, pathlib, re, sys, time, urllib.parse, urllib.request

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / "data", ROOT / "img"
COVERS = IMG / "covers"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PROFILE = "https://stratege.ru/playstation/users/dannymadcat"
PROFILE_UID = 134267
PATH_RE = re.compile(r"/(ps[345]|psvita)/games/([^/?#]+)")
FORCE = "--force" in sys.argv
TROPHIES = FORCE or "--trophies" in sys.argv


def get(url, data=None, tries=4, referer=PROFILE):
    for i in range(tries):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Referer": referer,
                                                              "X-Requested-With": "XMLHttpRequest"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(25)
                continue
            raise


def page(path):
    time.sleep(2)
    return get("https://stratege.ru" + path).decode("utf-8", "replace")


def profile_html():
    q = dict(ajax_mode="profile_all_loader", action="all_page", firmware=1, uid=PROFILE_UID,
             sort=0, type="current", compare="", page=0)
    return get("https://stratege.ru/ajax_loader/users_profile_fw",
               urllib.parse.urlencode(q).encode()).decode("utf-8", "replace")


def load(name):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def dump(name, obj):
    (DATA / name).write_text(json.dumps(dict(sorted(obj.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def save_square(raw, dest, size):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    s = min(im.size)
    l, t = (im.width - s) // 2, (im.height - s) // 2
    im.crop((l, t, l + s, t + s)).resize((size, size), Image.LANCZOS).save(dest, "JPEG", quality=82, optimize=True)


def cover_src(p, known):
    if p in known:
        return f"https://static.stratege.ru/trophies/{known[p]}/ICON0.PNG"
    trophies = page(p + "/trophies")
    m = re.search(r"/trophies/(NPWR\d+_\d+)/ICON0", trophies) or re.search(r"/trophies/(NPWR\d+_\d+)/", trophies)
    if m:
        return f"https://static.stratege.ru/trophies/{m.group(1)}/ICON0.PNG"
    # old PS4 lists have no NPWR images on stratege, but the page logo is the same list icon
    logo = re.search(r'src="(/sites/default/files/games/logo/img/[^"]+)"', trophies)
    if logo:
        return "https://stratege.ru" + logo.group(1)
    raise ValueError("trophy list icon not found")


def game_facts(p):
    h = page(p)
    field = lambda name: (m := re.search(rf"<span>{name}:</span>\s*([^<]+)<", h)) and m.group(1).strip()
    return {"type": field("Тип"), "lang": field("Язык")}


def trophy_lists(p):
    """Base game (filter 103 = hide all DLC) and each DLC group (filter N) from the AJAX trophy list."""
    h = page(p + "/trophies")
    blk = h[h.find("var tl_global_bx_settings"):]
    blk = blk[:blk.find("};")]
    vals = dict(re.findall(r"(\w+)\s*:\s*'([^']*)'", blk))
    if "settings" not in vals:
        raise ValueError("trophy list settings not found")

    def one(flt):
        q = dict(ajax_mode="trophies_list_loader", filter=flt, sort=0, helps=0, settings=vals["settings"], p_show_user="",
                 guest=1, players=vals.get("players", ""), compare_one="", shag=0)
        time.sleep(2)
        r = get("https://stratege.ru/ajax_loader/trophies_sp_list", urllib.parse.urlencode(q).encode(),
                referer="https://stratege.ru" + p + "/trophies").decode("utf-8", "replace")
        out = []
        for part in r.split('id="tltstplid_bx_trophies_')[1:]:
            g = re.search(r"tltstpl_border_(\w+)_trophies", part)
            t = re.search(r'tltstpl_tt_trops_title">.*?<a[^>]*>(.*?)</a>', part, re.S)
            out.append({"name": html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else None,
                        "grade": g.group(1) if g else None, "online": "trophies_icon/online.png" in part})
        return out

    groups = []
    for n, name in re.findall(r'filter=(\d+)" title="Показать DLC «(.*?)»"', h):
        if n not in [x[0] for x in groups]:
            groups.append((n, name))
    return {"base": one(103), "dlcs": [{"name": html.unescape(name), "trophies": one(n)} for n, name in groups]}


def difficulty_votes(p):
    h = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page(p + "/difficulty")))
    out = []
    for label in ("Оценка основных трофеев", "Оценка трофеев из DLC"):
        m = re.search(label + r" [\d.]+ [^(]*\(([\d\s]+) голос", h)
        out.append(int(m.group(1).replace(" ", "")) if m else None)
    return out


def main():
    IMG.mkdir(exist_ok=True)
    COVERS.mkdir(exist_ok=True)
    prof = profile_html()

    # avatar
    lib_path = DATA / "library.json"
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    m = re.search(r'<img src="(https?://[^"]+avatar_xl[^"]+)" title="DannyMadcat"', prof, re.I)
    if m and (FORCE or not (IMG / "avatar.png").exists()):
        im = Image.open(io.BytesIO(get(m.group(1).replace("http://", "https://")))).convert("RGBA")
        im.resize((160, 160), Image.LANCZOS).save(IMG / "avatar.png", optimize=True)
        print("avatar:", m.group(1))
    if (IMG / "avatar.png").exists() and lib.get("avatar") != "img/avatar.png":
        lib["avatar"] = "img/avatar.png"
        lib_path.write_text(json.dumps(lib, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # trophy-list ids already visible on the profile (platinum board)
    known = {}
    for a, npwr in re.findall(r'href="(/ps[345]/games/[^/"]+)/trophies[^"]*">\s*<img src="[^"]+/trophies/(NPWR\d+_\d+)/', prof):
        known.setdefault(a, npwr)

    games = json.loads((DATA / "games.json").read_text(encoding="utf-8"))
    urls = [g.get("stratege_url") for g in games] + [x.get("url") for x in lib.get("games", [])]
    paths = []
    for u in urls:
        m = PATH_RE.search(u or "")
        if m and m.group(0) not in paths:
            paths.append(m.group(0))

    covers, facts, failed = load("covers.json"), load("stratege.json"), []
    for p in paths:
        pf, slug = PATH_RE.search(p).groups()
        rel = f"img/covers/{pf}_{slug}.jpg"
        try:
            if FORCE or not (ROOT / rel).exists():
                save_square(get(cover_src(p, known)), ROOT / rel, 256)
                print("cover", p)
            covers[p] = rel
            if FORCE or p not in facts:
                facts[p] = game_facts(p)
                print("facts", p, facts[p])
            if (TROPHIES or "votes" not in facts[p]) and any(PATH_RE.search(g.get("stratege_url") or "") and PATH_RE.search(g["stratege_url"]).group(0) == p
                                                         and g.get("section") != "rejected" for g in games):
                facts[p]["votes"] = difficulty_votes(p)
                print("votes", p, facts[p]["votes"])
        except Exception as e:
            failed.append(f"{p}: {e}")
            print("FAIL", p, e)
        # keep progress if the run is interrupted
        dump("covers.json", covers)
        dump("stratege.json", facts)
    tro = load("trophies.json")
    for g in games:
        m = PATH_RE.search(g.get("stratege_url") or "")
        if g.get("section") == "rejected" or not m or (m.group(0) in tro and not TROPHIES):
            continue
        try:
            tro[m.group(0)] = trophy_lists(m.group(0))
            print("trophies", m.group(0), len(tro[m.group(0)]["base"]), [len(d["trophies"]) for d in tro[m.group(0)]["dlcs"]])
        except Exception as e:
            failed.append(f"{m.group(0)} trophies: {e}")
            print("FAIL", m.group(0), e)
        dump("trophies.json", tro)
    print(f"covers: {len(covers)}, facts: {len(facts)} of {len(paths)} games, trophy lists: {len(tro)}; failed: {len(failed)}")
    for f in failed:
        print("  ", f)


if __name__ == "__main__":
    main()
