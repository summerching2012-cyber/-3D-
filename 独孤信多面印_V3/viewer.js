import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id);
const faces=window.SEAL.faces;
const stage=$('stage');
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(32,1,.02,120);
camera.up.set(0,0,1);camera.position.set(-7,-11,7);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setClearColor(0x000000,0);
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.3;
stage.prepend(renderer.domElement);
renderer.domElement.setAttribute('aria-label','独孤信多面印三维视图：拖动旋转，滚轮缩放，双击印面定位');
renderer.domElement.tabIndex=0;
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=.07;
controls.minDistance=3.8;controls.maxDistance=24;
controls.autoRotateSpeed=.6;
const pmrem=new THREE.PMREMGenerator(renderer);
const room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;room.dispose();pmrem.dispose();
scene.environmentIntensity=.4;
scene.add(new THREE.HemisphereLight(0xe1eafa,0x302116,1));
const rig=new THREE.Group();scene.add(rig);
function light(color,intensity,x,y,z){const l=new THREE.DirectionalLight(color,intensity);l.position.set(x,y,z);rig.add(l);return l;}
light(0xffe2bd,1.8,-5,-7,9);light(0xadc9ef,1,6,-3,2);light(0xeaa66a,1.5,2,6,7);
let model, agedModel, cleanModel, outline, selected=0, tween=null;
const photoFaces=new Set(window.PHOTO_MAP.faces);
const materials=[];
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
let down=null;
const descriptions={
 '公文用印':'官职及公文标记用印。凹刻文字呈反书，钤印后才为正读。',
 '上书用印':'用于向上呈递文书的一组印文，含上疏、上章、上表与启事。',
 '书信用印':'书简用印，显示姓名和行文用语。异体字按公开释文作近似呈现。',
 '素面':'无印文面。保留石质、棱线及近似磨损，便于观察完整几何结构。'
};
const comparisons=[
 {face:1,n:[0,-1,0],up:[0,0,1]},
 {face:2,n:[0,-1,-1],up:[0,-1,1]},
 {face:7,n:[0,0,1],up:[0,1,0]},
 {face:13,n:[1,0,0],up:[0,1,0]},
 {face:3,n:[0,0,-1],up:[1,0,0]},
 {face:10,n:[-1,-1,0],up:[0,0,1]}
];
comparisons.forEach((view,index)=>{
 const button=document.createElement('button');button.textContent=`对照 ${index+1}`;button.dataset.comparison=index+1;
 button.onclick=()=>{
  if(!model)return;
  selectFace(view.face);controls.autoRotate=false;$('rotate').classList.remove('active');
  document.querySelector('.exhibit').classList.add('focused');
  const up=new THREE.Vector3(...view.up).normalize();
  const to=new THREE.Vector3(...view.n).normalize().addScaledVector(up,.12).normalize().multiplyScalar(11);
  tween={start:performance.now(),from:camera.position.clone(),to,fromTarget:controls.target.clone(),toTarget:new THREE.Vector3(),fromUp:camera.up.clone(),toUp:up};
  photo=index;
 };
 $('compareViews').append(button);
});
for(const f of faces){
 const button=document.createElement('button');button.className='face';
 button.innerHTML=`<small>${String(f.id).padStart(2,'0')}</small><span>${f.label|| (f.sides===3?'三角素面':'四边素面')}</span><i>${f.label?'↗':'◇'}</i>`;
 button.onclick=()=>focusFace(f.id);button.dataset.face=f.id;
 $('faces').append(button);
}
function selectFace(id){
 selected=id;const f=faces[id-1];
 $('faceTitle').textContent=f.label||`${f.sides===3?'三角':'四边'}素面`;
 $('faceType').textContent=`第 ${String(id).padStart(2,'0')} 面 · ${f.category}`;
 $('faceDesc').textContent=descriptions[f.category];
 $('faceNote').textContent=$('aged').checked?(photoFaces.has(id)?'馆藏照片表面：裂隙、红色残留及反光来自照片；贴合位置为近似。':'此面缺少清楚的馆藏表面照片，保留中性石色；文字为几何近似，不补画损伤。'):'V2 几何对照：已校正相邻印位，字体和程序微纹均为近似。';
 document.querySelectorAll('.face').forEach(b=>b.classList.toggle('active',+b.dataset.face===id));
 $('prev').disabled=false;$('next').disabled=false;
}
function focusFace(id){
 if(!model)return;
 document.querySelector('.exhibit').classList.add('focused');
 selectFace(id);controls.autoRotate=false;$('rotate').classList.remove('active');
 const f=faces[id-1],center=new THREE.Vector3(...f.center),n=new THREE.Vector3(...f.normal),up=new THREE.Vector3(...(f.text_up||f.v));
 tween={start:performance.now(),from:camera.position.clone(),to:center.clone().addScaledVector(n,6.4),fromTarget:controls.target.clone(),toTarget:center,fromUp:camera.up.clone(),toUp:up};
}
function reset(){
 document.querySelector('.exhibit').classList.remove('focused');
 controls.autoRotate=false;$('rotate').classList.remove('active');
 tween={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(-7,-11,7),fromTarget:controls.target.clone(),toTarget:new THREE.Vector3(),fromUp:camera.up.clone(),toUp:new THREE.Vector3(0,0,1)};
}
controls.addEventListener('start',()=>{tween=null;controls.autoRotate=false;$('rotate').classList.remove('active');});
renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
renderer.domElement.addEventListener('pointerup',e=>{
 if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5||!model)return;
 const r=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);
 ray.setFromCamera(mouse,camera);const hits=ray.intersectObject(model,true);
 if(hits.length){const p=hits[0].point;const f=faces.reduce((a,b)=>distance(a)<distance(b)?a:b);selectFace(f.id);
 function distance(f){return Math.abs(p.clone().sub(new THREE.Vector3(...f.center)).dot(new THREE.Vector3(...f.normal)));}}
});
renderer.domElement.addEventListener('dblclick',()=>selected&&focusFace(selected));
renderer.domElement.addEventListener('keydown',e=>{
 if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();focusFace((selected-1+(e.key==='ArrowRight'?1:25))%26+1);}
 if(e.key==='Home')reset();
});
$('prev').onclick=()=>focusFace((selected+24)%26+1);
$('next').onclick=()=>focusFace(selected%26+1);
$('reset').onclick=reset;
$('rotate').onclick=()=>{tween=null;controls.autoRotate=!controls.autoRotate;$('rotate').classList.toggle('active',controls.autoRotate);};
$('edges').onclick=()=>{if(outline){outline.visible=!outline.visible;$('edges').classList.toggle('active',outline.visible);}};
$('zoomIn').onclick=()=>{tween=null;camera.position.sub(controls.target).multiplyScalar(.85).add(controls.target);controls.update();};
$('zoomOut').onclick=()=>{tween=null;camera.position.sub(controls.target).multiplyScalar(1.18).add(controls.target);controls.update();};
$('exposure').oninput=e=>renderer.toneMappingExposure=+e.target.value;
$('lightAngle').oninput=e=>rig.rotation.z=+e.target.value;
$('pigment').onchange=e=>materials.filter(m=>m.name==='Incised_Red_Pigment').forEach(m=>m.color.set(e.target.checked?0x922b23:0x191513));
$('rough').onchange=e=>materials.filter(m=>m.name.startsWith('Stone')).forEach(m=>{m.normalScale.setScalar(e.target.checked?.65:0);m.needsUpdate=true;});
$('full').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
$('save').onclick=()=>{renderer.render(scene,camera);const a=document.createElement('a');a.download='独孤信多面印-当前视角.png';a.href=renderer.domElement.toDataURL('image/png');a.click();};
$('sourceOpen').onclick=()=>$('sources').showModal();$('sourceClose').onclick=()=>$('sources').close();
let photo=0;
const captions=window.PHOTO_CAPTIONS;
function setPhoto(i){photo=(i+window.PHOTOS.length)%window.PHOTOS.length;$('photo').src=window.PHOTOS[photo];$('photoCaption').textContent=captions[photo];}
$('photoPrev').onclick=()=>setPhoto(photo-1);$('photoNext').onclick=()=>setPhoto(photo+1);
$('photoOpen').onclick=()=>{setPhoto(photo);$('photoDialog').showModal();};$('photoClose').onclick=()=>$('photoDialog').close();
function readModel(encoded){
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
 const points=[],edges=new Set();
 for(const f of faces)for(let i=0;i<f.vertices.length;i++){
   const a=f.vertices[i],b=f.vertices[(i+1)%f.vertices.length],key=[a,b].sort((a,b)=>a-b).join('-');
   if(!edges.has(key)){edges.add(key);points.push(new THREE.Vector3(...window.SEAL.vertices[a]).multiplyScalar(1.003),new THREE.Vector3(...window.SEAL.vertices[b]).multiplyScalar(1.003));}
 }
 outline=new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:0xc1a26a,transparent:true,opacity:.65}));outline.visible=false;scene.add(outline);
 $('loading').hidden=true;$('state').textContent='模型已就绪 · 文物照片表面';
 selectFace(1);
},error=>{$('loading').textContent='模型加载失败：'+error.message;});
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(stage);resize();
function frame(now){
 requestAnimationFrame(frame);
 if(tween){let t=Math.min((now-tween.start)/650,1);t=t*t*(3-2*t);camera.position.lerpVectors(tween.from,tween.to,t);controls.target.lerpVectors(tween.fromTarget,tween.toTarget,t);camera.up.lerpVectors(tween.fromUp,tween.toUp,t).normalize();if(t===1)tween=null;}
 controls.update();renderer.render(scene,camera);
}
requestAnimationFrame(frame);
