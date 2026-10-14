from pathlib import Path
import hashlib,json,struct,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=ROOT.parent/'dugu-seal-v2'
baseline_report=json.loads((baseline/'delivery-check.json').read_text(encoding='utf-8'))
unchanged={name:digest(baseline/name)==info['sha256'] for name,info in baseline_report['outputs'].items()}
assert all(unchanged.values())
sources=json.loads((ROOT/'source-manifest.json').read_text(encoding='utf-8'))
assert all(digest(Path(s['path']))==s['sha256'] for s in sources)
assert (ROOT/'geometry.json').read_bytes()==(baseline/'geometry.json').read_bytes()
assert json.loads((ROOT/'layout-check.json').read_text())['pass']
assert json.loads((ROOT/'model-check.json').read_text())['nonmanifold_edges']==0
assert json.loads((ROOT/'viewer-check.json').read_text())['pass']
for p in ROOT.glob('*.png'):
    im=Image.open(p);im.save(p)
    with Image.open(p) as check:assert not check.info
for name in ['独孤信多面印.glb','几何对照.glb']:
    raw=(ROOT/name).read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    assert not json.loads(raw[20:20+n])['asset'].get('generator')
names=['打开模型.html','独孤信多面印.blend','独孤信多面印.glb','几何对照.glb','README_V3.md','使用说明.md','V2修改对照.md','geometry.json','photo-map.json','source-manifest.json','model-check.json','layout-check.json','viewer-check.json','preview.png','viewer-aged.png','viewer-clean.png','build_model.py','viewer.js','template.html','package_viewer.py','check_layout.py','make_v3.py','update_viewer.py','finalize.py','viewer.bundle.js','package.json','package-lock.json','vendor/THREE-LICENSE.txt','research/museum-collection.png']
report=dict(version='V3',v2_unchanged=unchanged,source_count=len(sources),sources_unchanged=True,face_layout_identical_to_v2=True,photo_faces=[1,7,8,10,12,14,18],model_closed=True,viewer_pass=True,formal_memory='not_synced_index_unavailable',outputs={name:dict(sha256=digest(ROOT/name),bytes=(ROOT/name).stat().st_size) for name in names})
(ROOT/'delivery-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
archive=ROOT.parent/'独孤信多面印_V3_文物表面参照版.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in names+['delivery-check.json']:z.write(ROOT/name,'独孤信多面印_V3/'+name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,v2_unchanged=unchanged,source_count=len(sources)),ensure_ascii=False))
