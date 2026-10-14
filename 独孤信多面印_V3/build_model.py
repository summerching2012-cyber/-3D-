from pathlib import Path
import json, math, time
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parent
photo_map=json.loads((ROOT/'photo-map.json').read_text(encoding='utf-8'))
photo_faces=set(photo_map['faces'])
data=json.loads((ROOT/'geometry.json').read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='CENTIMETERS'

def stone_material(f):
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

mesh=bpy.data.meshes.new('26_face_core')
mesh.from_pydata(data['vertices'],[],[f['vertices'] for f in data['faces']]);mesh.update()
body=bpy.data.objects.new('DuguXin_Seal',mesh);scene.collection.objects.link(body)
bpy.context.view_layer.objects.active=body;body.select_set(True)
for f in data['faces']:mesh.materials.append(stone_material(f))
pigment=bpy.data.materials.new('Incised_Red_Pigment');pigment.diffuse_color=(.29,.023,.016,1);pigment.use_nodes=True
bs=pigment.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.29,.023,.016,1);bs.inputs['Roughness'].default_value=.6
mesh.materials.append(pigment)
uv=mesh.uv_layers.new(name='FaceUV')
for poly,f in zip(mesh.polygons,data['faces']):
    poly.material_index=f['id']-1
    c,u,v=[Vector(f[k]) for k in ['center','u','v']]
    for li in poly.loop_indices:
        p=mesh.vertices[mesh.loops[li].vertex_index].co-c
        if f['id'] in photo_faces:
            px,py=photo_map['pixels'][str(mesh.loops[li].vertex_index)]
            uv.data[li].uv=(px/516,1-py/538)
        else:
            uv.data[li].uv=(p.dot(u)/f['width']+.5,p.dot(v)/f['height']+.5)

bevel=body.modifiers.new('Worn edges, approximately 0.22 mm','BEVEL');bevel.width=.055;bevel.segments=3
bpy.ops.object.modifier_apply(modifier=bevel.name)
font=bpy.data.fonts.load('C:/Windows/Fonts/simkai.ttf')

def glyphs(f):
    text=f['label'];count=len(text)
    if count==1:layout=[(text,0,0,1.20)]
    elif count==2:layout=[(ch,0,(.38 if i==0 else -.38),.69) for i,ch in enumerate(text)]
    elif count==3:layout=[(text[0],.35,.38,.64),(text[1],.35,-.38,.64),(text[2],-.35,.27,.64)]
    elif count==4:layout=[(ch,(.38 if i<2 else -.38),(.39 if i%2==0 else -.39),.66) for i,ch in enumerate(text)]
    else:layout=[(ch,(.49 if i<3 else -.34),(.55-i*.55 if i<3 else .29-(i-3)*.59),(.46 if i<3 else .54)) for i,ch in enumerate(text)]
    c,n,u,v=[Vector(f[k]) for k in ['center','normal','text_right','text_up']]
    cutters=[]
    for ch,x,y,sz in layout:
        curve=bpy.data.curves.new('Glyph','FONT');curve.body=ch;curve.font=font;curve.size=1;curve.resolution_u=5;curve.extrude=.035
        obj=bpy.data.objects.new('Carve_'+ch,curve);scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')
        coords=[p.co for p in obj.data.vertices];xmin=min(p.x for p in coords);xmax=max(p.x for p in coords);ymin=min(p.y for p in coords);ymax=max(p.y for p in coords)
        scale=sz/max(xmax-xmin,ymax-ymin)
        for p in obj.data.vertices:
            # Negative X creates the reversed matrix required for a readable impression.
            xx=-((p.co.x-(xmin+xmax)/2)*scale+x)
            yy=(p.co.y-(ymin+ymax)/2)*scale+y
            zz=p.co.z-.010
            p.co=c+u*xx+v*yy+n*zz
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        obj.data.materials.clear()
        for m in body.data.materials:obj.data.materials.append(m)
        for p in obj.data.polygons:p.material_index=26
        cutters.append(obj)
    return cutters

report=[]
for f in data['faces']:
    if not f['label'] or f['id'] in photo_faces:continue
    cutters=glyphs(f)
    bpy.ops.object.select_all(action='DESELECT')
    for o in cutters:o.select_set(True)
    bpy.context.view_layer.objects.active=cutters[0];bpy.ops.object.join();cut=cutters[0]
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
    mod=body.modifiers.new('Recess_'+str(f['id']),'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut,do_unlink=True)
    print('CARVED',f['id'],flush=True)
    report.append(dict(face=f['id'],label=f['label'],polygons=len(body.data.polygons)))

# Mesh coordinates and the exported glTF are in metres.
for p in body.data.vertices:p.co*=.01
body['photo_faces']=list(photo_faces)
body['photo_source']=photo_map['url']
body['description']='V3: museum photograph mapped only to documented visible faces. Other faces use neutral stone and approximate incisions. Rounded edges are illustrative; not a measured scan.'
body['principal_faces']=26;body['inscribed_faces']=14;body['width_m']=.0435;body['height_m']=.045
for poly in body.data.polygons:poly.use_smooth=False
for image in bpy.data.images:
    if image.source=='FILE':image.pack()

def aim(obj,p):obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.18,.21,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
for name,loc,power,size,color in [('Key',(-.07,-.07,.095),.09,.08,(1,.90,.78)),('Fill',(.07,-.035,.03),.04,.06,(.75,.84,1)),('Rim',(.025,.06,.07),.08,.06,(1,.7,.46))]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;light.color=color
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=loc;aim(obj,(0,0,0))
camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);cam.location=(-.073,-.11,.076);aim(cam,(0,0,0));camdata.type='ORTHO';camdata.ortho_scale=.095;camdata.clip_start=.001;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=48
scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.render.use_stamp=False
scene.view_settings.view_transform='AgX'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=.12
        area.spaces.active.clip_start=.001
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(ROOT/'独孤信多面印.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=False,export_copyright='')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'独孤信多面印.blend'))
scene.render.filepath=str(ROOT/'preview.png');bpy.ops.render.render(write_still=True)
import bmesh
bm=bmesh.new();bm.from_mesh(body.data)
reportdata=dict(photo_faces=sorted(photo_faces),blender=bpy.app.version_string,vertices=len(body.data.vertices),polygons=len(body.data.polygons),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),dimensions_m=list(body.dimensions),carvings=report)
(ROOT/'model-check.json').write_text(json.dumps(reportdata,ensure_ascii=False,indent=2),encoding='utf-8')
print('MODEL_COMPLETE',json.dumps(reportdata,ensure_ascii=True),flush=True)
