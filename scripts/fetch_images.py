#!/usr/bin/env python3
"""Download the PSN avatar and game covers (trophy-list icons) from stratege.ru into img/.

Usage:
  python3 scripts/fetch_images.py            # only what is missing
  python3 scripts/fetch_images.py --force    # re-download everything

Avatar: stratege profile AJAX -> img/avatar.png, path saved to library.json "avatar".
Covers: for every game in games.json and library.json the trophy-list id (NPWR...) is taken from the
profile's platinum board or from the game's stratege trophies page, then ICON0 is cropped to a square
256x256 JPEG -> img/covers/<platform>_<slug>.jpg. Map {"/ps5/games/<slug>": "img/covers/..."} is
written to data/covers.json; index.html looks covers up by the stratege path.
Requires Pillow.
"""
import io, json, pathlib, re, sys, time, urllib.parse, urllib.request

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / "data", ROOT / "img"
COVERS = IMG / "covers"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PROFILE = "https://stratege.ru/playstation/users/dannymadcat"
PROFILE_UID = 134267
PATH_RE = re.compile(r"/(ps[345]|psvita)/games/([^/?#]+)")
FORCE = "--force" in sys.argv


def get(url, data=None, tries=4):
    for i in range(tries):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Referer": PROFILE,
                                                              "X-Requested-With": "XMLHttpRequest"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(25)
                continue
            raise


def profile_html():
    q = dict(ajax_mode="profile_all_loader", action="all_page", firmware=1, uid=PROFILE_UID,
             sort=0, type="current", compare="", page=0)
    return get("https://stratege.ru/ajax_loader/users_profile_fw",
               urllib.parse.urlencode(q).encode()).decode("utf-8", "replace")


def save_square(raw, dest, size):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    s = min(im.size)
    l, t = (im.width - s) // 2, (im.height - s) // 2
    im.crop((l, t, l + s, t + s)).resize((size, size), Image.LANCZOS).save(dest, "JPEG", quality=82, optimize=True)


def main():
    IMG.mkdir(exist_ok=True)
    COVERS.mkdir(exist_ok=True)
    html = profile_html()

    # avatar
    lib_path = DATA / "library.json"
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    m = re.search(r'<img src="(https?://[^"]+avatar_xl[^"]+)" title="DannyMadcat"', html, re.I)
    if m and (FORCE or not (IMG / "avatar.png").exists()):
        im = Image.open(io.BytesIO(get(m.group(1).replace("http://", "https://")))).convert("RGBA")
        im.resize((160, 160), Image.LANCZOS).save(IMG / "avatar.png", optimize=True)
        print("avatar:", m.group(1))
    if (IMG / "avatar.png").exists():
        lib["avatar"] = "img/avatar.png"
        lib_path.write_text(json.dumps(lib, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # trophy-list ids already visible on the profile (platinum board)
    known = {}
    for a, npwr in re.findall(r'href="(/ps[345]/games/[^/"]+)/trophies[^"]*">\s*<img src="[^"]+/trophies/(NPWR\d+_\d+)/', html):
        known.setdefault(a, npwr)

    games = json.loads((DATA / "games.json").read_text(encoding="utf-8"))
    urls = [g.get("stratege_url") for g in games] + [x.get("url") for x in lib.get("games", [])]
    paths = []
    for u in urls:
        m = PATH_RE.search(u or "")
        if m and m.group(0) not in paths:
            paths.append(m.group(0))

    map_path = DATA / "covers.json"
    covers = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else {}
    failed = []
    for p in paths:
        pf, slug = PATH_RE.search(p).groups()
        rel = f"img/covers/{pf}_{slug}.jpg"
        if not FORCE and (ROOT / rel).exists():
            covers[p] = rel
            continue
        try:
            src = known.get(p) and f"https://static.stratege.ru/trophies/{known[p]}/ICON0.PNG"
            if not src:
                time.sleep(2)
                page = get(f"https://stratege.ru{p}/trophies").decode("utf-8", "replace")
                m = re.search(r"/trophies/(NPWR\d+_\d+)/ICON0", page) or re.search(r"/trophies/(NPWR\d+_\d+)/", page)
                # old PS4 lists have no NPWR images on stratege, but the page logo is the same list icon
                logo = re.search(r'src="(/sites/default/files/games/logo/img/[^"]+)"', page)
                if m:
                    src = f"https://static.stratege.ru/trophies/{m.group(1)}/ICON0.PNG"
                elif logo:
                    src = "https://stratege.ru" + logo.group(1)
                else:
                    raise ValueError("trophy list icon not found")
            save_square(get(src), ROOT / rel, 256)
            covers[p] = rel
            print("ok  ", p, src)
        except Exception as e:
            failed.append(f"{p}: {e}")
            print("FAIL", p, e)
    map_path.write_text(json.dumps(dict(sorted(covers.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"covers: {len(covers)}/{len(paths)}; failed: {len(failed)}")
    for f in failed:
        print("  ", f)


if __name__ == "__main__":
    main()
