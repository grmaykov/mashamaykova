import concurrent.futures,hashlib,io,json,pathlib,time,urllib.parse,urllib.request
from PIL import Image,ImageOps
ROOT=pathlib.Path(__file__).resolve().parents[1]
records=json.loads((ROOT/'.migration/archive34-20261005.json').read_text())['added']
assert len(records)==34
assert {r['id'] for r in records}=={f'{n:04d}' for n in range(756,790)}
def transfer(r):
 for attempt in range(3):
  try:
   url='https://cloud-api.yandex.net/v1/disk/public/resources?'+urllib.parse.urlencode({'public_key':r['public_url'],'path':r['path']})
   with urllib.request.urlopen(url,timeout=90) as response:meta=json.load(response)
   assert meta['md5']==r['original_md5']
   with urllib.request.urlopen(meta['file'],timeout=150) as response:raw=response.read()
   assert hashlib.md5(raw).hexdigest()==r['original_md5']
   assert hashlib.sha256(raw).hexdigest()==r['original_sha256']
   break
  except Exception:
   if attempt==2:raise
   time.sleep(2)
 im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
 if r['rotate_ccw']:im=im.rotate(r['rotate_ccw'],expand=True)
 im.thumbnail((2200,2200))
 assert list(im.size)==r['encoded_size']
 for thumb in (False,True):
  out=im.copy()
  if thumb:out.thumbnail((650,650))
  path=ROOT/'assets'/(r['id']+('-thumb' if thumb else '')+'.webp')
  assert not path.exists(),f'Refusing to overwrite {path}'
  out.save(path,'WEBP',quality=82 if thumb else 88,method=6)
  with Image.open(path) as check:check.load();assert check.size==out.size
 print('Verified '+r['id'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(transfer,records))
print('All 34 originals and thumbnails verified.')
