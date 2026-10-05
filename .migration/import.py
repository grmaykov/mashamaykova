import base64
import hashlib
import io
import json
import os
import pathlib
import urllib.request
import zipfile

def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

manifest = json.loads(pathlib.Path('.migration/manifest.json').read_text())
expected = {item['path']: item for item in manifest}
parts = json.loads(pathlib.Path('.migration/archive-parts.json').read_text())
archive = io.BytesIO()
for number, part in enumerate(parts, 1):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/git/blobs/{part['sha']}",
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json', 'User-Agent': 'verified-portfolio-import'},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.load(response)
    if payload['encoding'] != 'base64':
        raise ValueError('Unexpected blob encoding')
    data = base64.b64decode(payload['content'])
    if len(data) != part['size'] or blob_sha(data) != part['sha']:
        raise ValueError('Archive part verification failed')
    archive.write(data)
    print(f'Verified archive part {number}/{len(parts)}', flush=True)

archive.seek(0)
with zipfile.ZipFile(archive) as bundle:
    names = bundle.namelist()
    if len(names) != len(set(names)):
        raise ValueError('Duplicate archive entries')
    for name in names:
        path = pathlib.PurePosixPath(name)
        if name not in expected or path.is_absolute() or '..' in path.parts:
            raise ValueError('Unexpected archive path')
        data = bundle.read(name)
        item = expected[name]
        if len(data) != item['size'] or blob_sha(data) != item['sha']:
            raise ValueError('Source verification failed: ' + name)
        target = pathlib.Path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

for item in manifest:
    data = pathlib.Path(item['path']).read_bytes()
    if len(data) != item['size'] or blob_sha(data) != item['sha']:
        raise ValueError('Final verification failed: ' + item['path'])
print(f"All {len(manifest)} website files verified", flush=True)
