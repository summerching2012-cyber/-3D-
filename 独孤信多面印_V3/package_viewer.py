from pathlib import Path
import base64, json, struct, io
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parent
glb=ROOT/'独孤信多面印.glb'
raw=glb.read_bytes()
length,kind=struct.unpack_from('<II',raw,12)
doc=json.loads(raw[20:20+length])
doc['asset']['generator']='';doc['asset'].pop('copyright',None)
chunk=json.dumps(doc,ensure_ascii=True,separators=(',',':')).encode()
chunk+=b' '*((-len(chunk))%4)
body=struct.pack('<II',len(chunk),kind)+chunk+raw[20+length:]
glb.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(body))+body)
images=[];captions=[]
sources=sorted(ROOT.parent.glob('*对比图*.jpg'))+sorted(ROOT.parent.glob('独孤信多面印*.jpg'))+sorted(ROOT.parent.glob('食物-独孤信多面印*.jpg'))
sources += [ROOT/'research/museum-collection.png']
for p in sources:
    im=ImageOps.exif_transpose(Image.open(p)).convert("RGB");im.thumbnail((1600,1600));out=io.BytesIO();im.save(out,format='JPEG',quality=88)
    images.append('data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode())
    captions.append(p.name+(' · 陕西历史博物馆官网藏品照片，V3表面参照来源' if p.name=='museum-collection.png' else ' · 上方为旧模型，下方为实物，V2以实物为校正依据' if '对比图' in p.name else ' · 初版原始参考照片'))
payload='<script>window.PHOTO_MAP='+ (ROOT/'photo-map.json').read_text(encoding='utf-8')+';window.CLEANMODEL="'+base64.b64encode((ROOT/'几何对照.glb').read_bytes()).decode()+'";window.SEAL='+ (ROOT/'geometry.json').read_text(encoding='utf-8')+';window.PHOTOS='+json.dumps(images)+';window.PHOTO_CAPTIONS='+json.dumps(captions,ensure_ascii=False)+';window.MODEL="'+base64.b64encode(glb.read_bytes()).decode()+'";</script>'
bundle=(ROOT/'viewer.bundle.js').read_text(encoding='utf-8').replace('</script','<\\/script')
license=(ROOT/'vendor/THREE-LICENSE.txt').read_text(encoding='utf-8')
html=(ROOT/'template.html').read_text(encoding='utf-8').replace('<!-- PAYLOAD -->',payload).replace('<!-- SCRIPT -->','<!--\n'+license+'\n--><script>'+bundle+'</script>')
(ROOT/'打开模型.html').write_text(html,encoding='utf-8')
preview=ROOT/'preview.png'
if preview.exists():
    im=Image.open(preview);im.save(preview)
print(json.dumps(dict(html_bytes=len(html.encode()),glb_bytes=glb.stat().st_size,materials=len(doc['materials']),generator=doc['asset']['generator'])))

