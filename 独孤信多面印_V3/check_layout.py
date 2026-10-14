from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT/'geometry.json').read_text(encoding='utf-8'))
faces = data['faces']
assert len(faces) == 26 and sum(f['sides'] == 4 for f in faces) == 18
assert sum(len(f['label']) for f in faces) == 47
# Independently encode the visible adjacency in the lower half of each photo.
observations = [
    (1, 1, [0,0,1], {'left':10,'right':9,'up':8,'down':2}),
    (2, 2, [0,-1,1], {'up':1,'down':3}),
    (3, 7, [0,1,0], {'left':12,'right':11,'up':6,'down':8}),
    (4, 13, [0,1,0], {'left':11,'down':9}),
    (5, 3, [1,0,0], {'left':2,'right':4}),
    (6, 10, [0,0,1], {'left':14,'right':1}),
]
results=[]
for photo, face_id, up, expected in observations:
    f=faces[face_id-1];n=np.array(f['normal']);up=np.array(up,dtype=float)
    up-=n*np.dot(up,n);up/=np.linalg.norm(up);right=np.cross(up,n)
    neighbors=[g for g in faces if g['id']!=face_id and len(set(g['vertices'])&set(f['vertices']))==2]
    actual={}
    for g in neighbors:
        delta=np.array(g['center'])-f['center'];x=np.dot(delta,right);y=np.dot(delta,up)
        direction=('right' if x>0 else 'left') if abs(x)>abs(y) else ('up' if y>0 else 'down')
        actual[direction]=g['id']
    assert all(actual[k]==v for k,v in expected.items()), (photo,actual,expected)
    results.append({'photo':photo,'face':face_id,'expected':expected,'actual':actual,'pass':True})
for f in faces[:14]:
    basis=np.array([f['text_right'],f['text_up'],f['normal']])
    assert np.allclose(basis@basis.T,np.eye(3)) and np.linalg.det(basis)>.999
report={'pass':True,'photo_adjacency_checks':results,'text_frames_checked':14,'characters':47}
(ROOT/'layout-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
