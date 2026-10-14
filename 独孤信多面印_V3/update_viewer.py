from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'dugu-seal-v2'
s=(BASE/'viewer.js').read_text(encoding='utf-8')
s=s.replace('camera.position.set(7,-11,7)','camera.position.set(-7,-11,7)').replace('new THREE.Vector3(7,-11,7)','new THREE.Vector3(-7,-11,7)')
s=s.replace('let model, outline, selected=0, tween=null;','let model, agedModel, cleanModel, outline, selected=0, tween=null;\nconst photoFaces=new Set(window.PHOTO_MAP.faces);')
s=s.replace("$('faceNote').textContent=f.label?'V2 已校正印位与字向；释文正读，刻面反书。笔形与裂纹仍为近似。':'模型按文献结构构建，表面裂纹为程序化近似。';", "$('faceNote').textContent=$('aged').checked?(photoFaces.has(id)?'馆藏照片表面：裂隙、红色残留及反光来自照片；贴合位置为近似。':'此面缺少清楚的馆藏表面照片，保留中性石色；文字为几何近似，不补画损伤。'):'V2 几何对照：已校正相邻印位，字体和程序微纹均为近似。';")
start=s.index('const binary=');end=s.index('function resize()',start)
old=s[start:end]
edges=old[old.index(' const points=[]'):old.index(" $('loading').hidden")]
s=s[:start]+'''function readModel(encoded){
 const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));
 return new GLTFLoader().parseAsync(bytes.buffer,'');
}
function setMode(){
 const aged=$('aged').checked;
 agedModel.visible=aged;cleanModel.visible=!aged;model=aged?agedModel:cleanModel;
 $('pigment').disabled=aged;$('rough').disabled=aged;
 $('modeHelp').textContent=aged?'照片表面含原有红色与反光；关闭此模式后可调整填痕和微纹。':'几何对照可调节红色填痕与表面微纹。';
 selectFace(selected||1);
}
$('aged').onchange=()=>{if(agedModel&&cleanModel)setMode();};
$('museumView').onclick=reset;
Promise.all([readModel(window.MODEL),readModel(window.CLEANMODEL)]).then(([aged,clean])=>{
 agedModel=aged.scene;cleanModel=clean.scene;
 for(const item of [agedModel,cleanModel]){
  item.scale.setScalar(100);scene.add(item);
  item.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material])){
   if(!materials.includes(m)){materials.push(m);m.envMapIntensity=item===agedModel?.15:.65;}
  }});
 }
 model=agedModel;setMode();$('aged').disabled=false;
''' + edges + ''' $('loading').hidden=true;$('state').textContent='模型已就绪 · 文物照片表面';
 selectFace(1);
},error=>{$('loading').textContent='模型加载失败：'+error.message;});
''' + s[end:]
(ROOT/'viewer.js').write_text(s,encoding='utf-8')
s=(BASE/'template.html').read_text(encoding='utf-8')
s=s.replace('V2 | 印位校正版','V3 | 文物表面参照版').replace('V2 · 印位校正版','V3 · 文物表面参照').replace('V2 · 实物印位校正','V3 · 文物表面参照')
s=s.replace('<div class="controls">','<div class="controls"><label><input id="aged" type="checkbox" checked disabled>文物照片表面</label><p id="modeHelp" class="sidefoot">正在载入表面…</p><button id="museumView">馆藏参照视角</button>')
s=s.replace('查看 6 张对比图及 5 张原始照片','查看复制品与馆藏参考照片')
s=s.replace('<h2>复原依据与边界</h2>','<h2>复原依据与边界</h2><p><strong>V3 文物表面参照：</strong>将陕历博官网照片中能辨认的7个可见面，按共享棱角贴合至V2面位。裂隙、红色残留、磨损斑驳直接来自照片；没有在未知面随机生成损伤。照片保留拍摄反光，映射是手工近似，不能用于文物测量。该模式的可见字迹来自照片，不把其凹凸声称为真实雕刻几何。</p><p>关闭“文物照片表面”可查看完整几何刻字对照；该对照模式沿用V2字体及程序微纹。复制品只用于印位核对。<a href="https://www.sxhm.com/collections/detail/439.html" target="_blank" rel="noopener">陕西历史博物馆藏品原页</a>。</p>')
s=s.replace('V2 复核日期','V3 复核日期')
(ROOT/'template.html').write_text(s,encoding='utf-8')
s=(BASE/'package_viewer.py').read_text(encoding='utf-8')
s=s.replace('ImageOps.exif_transpose(Image.open(p))', 'ImageOps.exif_transpose(Image.open(p)).convert("RGB")')
s=s.replace("p.name+(' · 上方", "p.name+(' · 陕西历史博物馆官网藏品照片，V3表面参照来源' if p.name=='museum-collection.png' else ' · 上方")
s=s.replace("sorted(ROOT.parent.glob('*对比图.jpg'))", "sorted(ROOT.parent.glob('*对比图*.jpg'))")
s=s.replace("for p in sources:","sources += [ROOT/'research/museum-collection.png']\nfor p in sources:")
s=s.replace("payload='<script>window.SEAL='", "payload='<script>window.PHOTO_MAP='+ (ROOT/'photo-map.json').read_text(encoding='utf-8')+';window.CLEANMODEL=\"'+base64.b64encode((ROOT/'几何对照.glb').read_bytes()).decode()+'\";window.SEAL='")
(ROOT/'package_viewer.py').write_text(s,encoding='utf-8')
print('Viewer mode and source provenance updated')
