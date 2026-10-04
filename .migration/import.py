import concurrent.futures, hashlib, json, pathlib, tempfile, urllib.request
BASE = "https://masha-maykova.grif86.chatgpt.site/"
items = json.loads(pathlib.Path(".migration/manifest.json").read_text())
def fetch(item, root):
    path = item["path"]
    if path.startswith("/") or ".." in pathlib.PurePosixPath(path).parts:
        raise ValueError("Invalid path")
    with urllib.request.urlopen(BASE + path, timeout=60) as response:
        data = response.read()
    digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if len(data) != item["size"] or digest != item["sha"]:
        raise ValueError("Source differs from reviewed website: " + path)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return path
with tempfile.TemporaryDirectory() as temp:
    root = pathlib.Path(temp)
    probe = next(item for item in items if item["path"] == "index.html")
    print("Checking public source", flush=True)
    fetch(probe, root)
    print("Source verified; transferring website", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for n, path in enumerate(pool.map(lambda item: fetch(item, root), items), 1):
            if n % 50 == 0:
                print(f"Verified {n}/{len(items)} files", flush=True)
    for item in items:
        dest = pathlib.Path(item["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((root / item["path"]).read_bytes())
print(f"All {len(items)} files verified", flush=True)
