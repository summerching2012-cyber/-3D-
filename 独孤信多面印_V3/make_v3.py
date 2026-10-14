from pathlib import Path
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'dugu-seal-v2'
# Start from the verified V2 generators; retain the face coordinates and text frames.
s=(BASE/'build_model.py').read_text(encoding='utf-8')
s=s.replace("data=json.loads", "photo_map=json.loads((ROOT/'photo-map.json').read_text(encoding='utf-8'))\nphoto_faces=set(photo_map['faces'])\ndata=json.loads",1)
start=s.index('def stone_material(f):');end=s.index("\nmesh=bpy.data.meshes",start)
s=s[:start]+'''def stone_material(f):
    mat=bpy.data.materials.new(f'Stone_{f["id"]:02}')
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    p=nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.009,.007,.006,1)
    p.inputs['Roughness'].default_value=.46
    p.inputs['IOR'].default_value=1.5
    if f['id'] in photo_faces:
        tex=nodes.new('ShaderNodeTexImage')
        tex.image=bpy.data.images.load(str(ROOT/photo_map['source']),check_existing=True)
        links.new(tex.outputs['Color'],p.inputs['Base Color'])
        p.inputs['Roughness'].default_value=.72
        p.inputs['Specular IOR Level'].default_value=.12
    return mat
''' + s[end:]
s=s.replace("uv.data[li].uv=(p.dot(u)/f['width']+.5,p.dot(v)/f['height']+.5)","""if f['id'] in photo_faces:
            px,py=photo_map['pixels'][str(mesh.loops[li].vertex_index)]
            uv.data[li].uv=(px/516,1-py/538)
        else:
            uv.data[li].uv=(p.dot(u)/f['width']+.5,p.dot(v)/f['height']+.5)""")
s=s.replace("bevel.width=.022","bevel.width=.055")
s=s.replace("if not f['label']:continue","if not f['label'] or f['id'] in photo_faces:continue")
s=s.replace("body['description']=", "body['photo_faces']=list(photo_faces)\nbody['photo_source']=photo_map['url']\nbody['description']=")
s=s.replace('V2: face placement and lettering orientation corrected using six replica comparison photos, museum photo and impressions. Letterforms and wear remain approximate.','V3: museum photograph mapped only to documented visible faces. Other faces use neutral stone and approximate incisions. Rounded edges are illustrative; not a measured scan.')
s=s.replace("cam.location=(.073,-.11,.076)","cam.location=(-.073,-.11,.076)")
s=s.replace("reportdata=dict(blender=", "reportdata=dict(photo_faces=sorted(photo_faces),blender=")
(ROOT/'build_model.py').write_text(s,encoding='utf-8')
shutil.copyfile(BASE/'独孤信多面印.glb',ROOT/'几何对照.glb')
sources=[]
for p in sorted(ROOT.parent.glob('*.jpg'))+[ROOT/'research/museum-collection.png']:
    sources.append(dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size,modified=p.stat().st_mtime))
(ROOT/'source-manifest.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
assert json.loads((ROOT/'geometry.json').read_text(encoding='utf-8'))==json.loads((BASE/'geometry.json').read_text(encoding='utf-8'))
print('V3 build prepared; V2 face mapping unchanged')

