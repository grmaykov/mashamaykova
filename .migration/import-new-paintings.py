import concurrent.futures, hashlib, io, json, pathlib, time, urllib.parse, urllib.request
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parents[1]
records = json.loads((ROOT / ".migration/new-paintings-20261005.json").read_text())["added"]
assert len(records) == 33
assert {r["id"] for r in records} == {f"{n:04d}" for n in range(723, 756)}
url = "https://cloud-api.yandex.net/v1/disk/public/resources?" + urllib.parse.urlencode({"public_key": records[0]["folder_url"], "limit": 1000})
with urllib.request.urlopen(url, timeout=90) as response:
    listing = json.load(response)
files = {x["name"]: x for x in listing["_embedded"]["items"]}
def transfer(record):
    item = files[record["filename"]]
    assert item["md5"] == record["original_md5"]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(item["file"], timeout=120) as response:
                raw = response.read()
            assert hashlib.md5(raw).hexdigest() == record["original_md5"]
            assert hashlib.sha256(raw).hexdigest() == record["original_sha256"]
            break
        except Exception:
            if attempt == 2: raise
            time.sleep(2)
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    image.thumbnail((2200, 2200))
    for thumb in (False, True):
        output = image.copy()
        if thumb: output.thumbnail((650, 650))
        path = ROOT / "assets" / (record["id"] + ("-thumb" if thumb else "") + ".webp")
        assert not path.exists(), f"Refusing to overwrite {path}"
        output.save(path, "WEBP", quality=82 if thumb else 88, method=6)
        with Image.open(path) as check:
            assert check.size == output.size
            check.load()
    print("Verified and prepared " + record["id"], flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(transfer, records))
print("All 33 new paintings and 33 thumbnails verified.")
